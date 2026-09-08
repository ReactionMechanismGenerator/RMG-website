"""Checks for metadata-only indexes and individual kinetics library loading."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase

from rmgweb.database.catalog import CatalogEntry, KineticsCatalog, KineticsDatabaseNotFound
from rmgweb.database import views


class KineticsCatalogTest(SimpleTestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'families').mkdir()
        self.catalog = KineticsCatalog(self.root)
        self.reactions = self.root / 'libraries/nested/example/reactions.py'
        self.reactions.parent.mkdir(parents=True)
        self.reactions.write_text('name = "Example"\nshortDesc = "Description"\nentry(index=1)\n')
        self.dictionary = self.reactions.parent / 'dictionary.txt'
        self.dictionary.write_text('species data')

    def test_reads_metadata_without_executing_database_code(self):
        with self.reactions.open('a') as source:
            source.write('raise AssertionError("Metadata reading must not execute this file")\n')
        libraries = self.catalog.libraries()
        self.assertEqual(libraries, [('nested/example', CatalogEntry('nested/example', 'Example', 'Description'))])

    def test_dynamic_metadata_is_not_executed(self):
        self.reactions.write_text('name = dangerous()\nshortDesc = dangerous()\n')
        self.assertEqual(self.catalog.libraries()[0][1], CatalogEntry('nested/example', 'nested/example'))

    def test_metadata_cache_reuses_and_refreshes_results(self):
        first = self.catalog.libraries()[0][1]
        self.assertIs(self.catalog.libraries()[0][1], first)
        self.reactions.write_text('shortDesc = "Updated description"\n')
        self.assertEqual(self.catalog.libraries()[0][1].short_desc, 'Updated description')

    def test_catalog_discovers_added_and_removed_libraries(self):
        self.catalog.libraries()
        added = self.root / 'libraries/another/reactions.py'
        added.parent.mkdir()
        added.write_text('name = "Another"\n')
        self.assertEqual(len(self.catalog.libraries()), 2)
        self.reactions.unlink()
        self.assertEqual([label for label, _ in self.catalog.libraries()], ['another'])
        with self.assertRaises(ValueError):
            self.catalog.library('nested/example')

    def test_catalog_filters_nested_libraries(self):
        self.assertEqual(len(self.catalog.libraries('nested')), 1)
        self.assertEqual(self.catalog.libraries('missing'), [])

    def test_family_catalog_preserves_child_links_without_loading_rules(self):
        family = self.root / 'families/Example'
        family.mkdir()
        (family / 'groups.py').write_text('name = "Example/groups"\nrecipe(unknown())\n')
        (family / 'rules.py').write_text('raise AssertionError("Do not load rules")\n')
        training = family / 'training'
        training.mkdir()
        (training / 'reactions.py').write_text('name = "Example/training"\nentry(unknown())\n')
        (self.root / 'families/__pycache__').mkdir()
        families = self.catalog.families()
        self.assertEqual(len(families), 1)
        entry = families[0][1]
        self.assertEqual(entry.groups.label, 'Example/groups')
        self.assertEqual(entry.rules.label, 'Example/rules')
        self.assertEqual(entry.depositories[0].label, 'Example/training')

    @patch('rmgpy.data.kinetics.library.KineticsLibrary')
    def test_loads_selected_library_once_and_tracks_both_source_files(self, library_class):
        first = self.catalog.library('nested/example')
        self.assertIs(self.catalog.library('nested/example'), first)
        library_class.assert_called_once_with(label='nested/example')
        self.assertEqual(library_class.return_value.load.call_args.args[0], str(self.reactions))
        self.dictionary.write_text('updated species data')
        self.catalog.library('nested/example')
        self.assertEqual(library_class.call_count, 2)
        self.reactions.write_text('name = "Updated"\n')
        self.catalog.library('nested/example')
        self.assertEqual(library_class.call_count, 3)

    @patch('rmgpy.data.kinetics.library.KineticsLibrary')
    def test_missing_or_traversal_labels_never_load(self, library_class):
        for label in ['missing', '../example', '/tmp/example', 'nested/../example']:
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.catalog.library(label)
        library_class.assert_not_called()

    @patch('rmgpy.data.kinetics.library.KineticsLibrary')
    def test_failed_load_is_retried(self, library_class):
        library_class.return_value.load.side_effect = [ValueError('bad data'), None]
        with self.assertRaises(ValueError):
            self.catalog.library('nested/example')
        self.catalog.library('nested/example')
        self.assertEqual(library_class.call_count, 2)

    def test_cache_shares_work_without_blocking_other_sources(self):
        started = Event()
        release = Event()
        result = object()

        def slow():
            started.set()
            if not release.wait(timeout=5):
                raise TimeoutError('Test did not release calculation')
            return result

        with ThreadPoolExecutor(max_workers=3) as executor:
            first = executor.submit(self.catalog._cached, 'first', (1,), slow)
            try:
                self.assertTrue(started.wait(timeout=5))
                duplicate = executor.submit(self.catalog._cached, 'first', (1,), lambda: self.fail('Repeated load'))
                unrelated = executor.submit(self.catalog._cached, 'other', (1,), lambda: 'other')
                self.assertEqual(unrelated.result(timeout=2), 'other')
            finally:
                release.set()
            self.assertIs(first.result(timeout=5), result)
            self.assertIs(duplicate.result(timeout=5), result)


class KineticsLazyViewTest(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get('/database/kinetics/')
        database_patch = patch.object(views, 'database')
        self.database = database_patch.start()
        self.addCleanup(database_patch.stop)
        self.catalog = self.database.kinetics_catalog
        self.catalog.libraries.return_value = [('nested/example', CatalogEntry('nested/example', 'Example', 'Description'))]
        self.catalog.families.return_value = []

    def test_indexes_render_without_loading_reactions(self):
        for section in ['', 'libraries', 'families']:
            with self.subTest(section=section):
                response = views.kinetics(self.request, section=section)
                self.assertEqual(response.status_code, 200)
                self.database.load.assert_not_called()
                self.catalog.library.assert_not_called()
                if section != 'families':
                    self.assertContains(response, '/database/kinetics/libraries/nested/example/')
                    self.assertContains(response, 'Description')

    @patch.object(views, 'render')
    def test_selected_library_uses_only_individual_loader(self, render):
        library = SimpleNamespace(top=[], entries={}, name='Example', long_desc='Long description')
        self.catalog.library.return_value = library
        views.kinetics(self.request, section='libraries', subsection='nested/example')
        self.catalog.library.assert_called_once_with('nested/example')
        self.database.load.assert_not_called()
        self.assertEqual(render.call_args.args[1], 'kineticsTable.html')

    def test_library_prefix_renders_catalog(self):
        self.catalog.library.side_effect = KineticsDatabaseNotFound('Not an exact library')
        response = views.kinetics(self.request, section='libraries', subsection='nested')
        self.assertContains(response, '/database/kinetics/libraries/nested/example/')
        self.database.load.assert_not_called()

    def test_unknown_library_is_404(self):
        self.catalog.library.side_effect = KineticsDatabaseNotFound('Missing')
        self.catalog.libraries.return_value = []
        with self.assertRaises(Http404):
            views.kinetics(self.request, section='libraries', subsection='missing')

    def test_chemistry_errors_are_not_hidden_as_catalog_or_404(self):
        self.catalog.library.side_effect = ValueError('Invalid reaction data')
        with self.assertRaisesRegex(ValueError, 'Invalid reaction data'):
            views.kinetics(self.request, section='libraries', subsection='nested/example')
        with self.assertRaisesRegex(ValueError, 'Invalid reaction data'):
            views.kineticsEntry(self.request, 'libraries', 'nested/example', '1')

    def test_family_detail_keeps_existing_full_preparation(self):
        result = views._kineticsDatabaseForBrowsing('families', 'example/groups')
        self.database.load.assert_called_once_with('kinetics', 'families')
        self.database.get_kinetics_database.assert_called_once_with('families', 'example/groups')
        self.assertIs(result, self.database.get_kinetics_database.return_value)

    @patch.object(views, 'render')
    @patch.object(views, 'getReactionUrl', return_value='/reaction/')
    def test_direct_library_entry_does_not_load_all_libraries(self, reaction_url, render):
        library = SimpleNamespace(entries={'1': SimpleNamespace(
            index=1, item=SimpleNamespace(reactants=[], products=[], degeneracy=1, reversible=True),
            reference=None, reference_type='', data=None,
        )}, name='Example', long_desc='')
        self.catalog.library.return_value = library
        views.kineticsEntry(self.request, 'libraries', 'nested/example', '1')
        self.database.load.assert_not_called()
        self.catalog.library.assert_called_once_with('nested/example')
