"""Regression tests for lazy, cached untrained-reaction browsing."""

import gc
import weakref
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from threading import Event
from unittest.mock import patch

from django.http import Http404
from django.test import RequestFactory, SimpleTestCase
from rmgpy.data.base import Entry
from rmgpy.data.kinetics import KineticsDepository
from rmgpy.data.kinetics.family import KineticsFamily
from rmgpy.reaction import Reaction
from rmgpy.species import Species

from rmgweb.database import views


class KineticsBrowsingTest(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get('/database/kinetics/families/')
        self.family = KineticsFamily(label='example')
        self.other_family = KineticsFamily(label='example_other')
        for family in [self.family, self.other_family]:
            family.name = family.label
            family.groups = SimpleNamespace(label=family.label + '/groups', name='Groups', entries={})
        self.database_patch = patch.object(views, 'database')
        self.database = self.database_patch.start()
        self.addCleanup(self.database_patch.stop)
        self.database.kinetics.families = {
            'example': self.family, 'example_other': self.other_family,
        }
        self.database.kinetics.libraries = {}
        self.database.get_kinetics_database.return_value = None

    @patch.object(views, 'render')
    @patch.object(views, 'getUntrainedReactions')
    def test_indexes_do_not_calculate_untrained_reactions(self, calculate, render):
        for section in ['', 'families', 'libraries']:
            with self.subTest(section=section):
                views.kinetics(self.request, section=section)
                calculate.assert_not_called()
                context = render.call_args.args[2]
                self.assertIsNone(context['untrained'])
                if section == 'libraries':
                    self.assertEqual(context['kineticsFamilies'], [])

    @patch.object(views, 'render')
    @patch.object(views, 'getUntrainedReactions')
    def test_selected_family_only(self, calculate, render):
        views.kinetics(self.request, section='families', subsection='example')
        calculate.assert_called_once_with(self.family)
        context = render.call_args.args[2]
        self.assertEqual(context['selectedFamily'], 'example')
        self.assertIs(context['untrained'], calculate.return_value)
        self.assertEqual(self.family.depositories, [])

    @patch.object(views, 'render')
    @patch.object(views, 'getUntrainedReactions')
    def test_library_matching_family_name_does_not_calculate(self, calculate, render):
        views.kinetics(self.request, section='libraries', subsection='example')
        calculate.assert_not_called()

    @patch.object(views, 'render')
    @patch.object(views, 'getUntrainedReactions')
    def test_direct_untrained_page_uses_cache(self, calculate, render):
        calculate.return_value.entries = {}
        views.kineticsUntrained(self.request, 'example')
        calculate.assert_called_once_with(self.family)
        self.assertEqual(render.call_args.args[2]['entries'], [])

    def test_unknown_untrained_family_returns_404(self):
        with self.assertRaises(Http404):
            views.kineticsUntrained(self.request, 'missing')

    @patch.object(views, 'getUntrainedReactions')
    def test_index_renders_untrained_links_without_calculating(self, calculate):
        response = views.kinetics(self.request, section='families')
        self.assertContains(response, '/database/kinetics/families/example/untrained/')
        self.assertContains(response, 'example/untrained</a></li>', html=False)
        calculate.assert_not_called()

    @patch.object(views, 'getUntrainedReactions')
    def test_selected_family_renders_zero_count_only_for_that_family(self, calculate):
        calculate.return_value = KineticsDepository(label='example/untrained')
        response = views.kinetics(self.request, section='families', subsection='example')
        self.assertContains(response, 'example/untrained</a> (0 entries)</li>', html=False)
        self.assertContains(response, 'example_other/untrained</a></li>', html=False)


class UntrainedReactionCacheTest(SimpleTestCase):
    def setUp(self):
        views._untrained_reactions.clear()
        self.addCleanup(views._untrained_reactions.clear)
        self.family = KineticsFamily(label='example')

    @patch.object(views, '_calculateUntrainedReactions')
    def test_reuses_empty_result_without_mutating_depositories(self, calculate):
        calculate.return_value = KineticsDepository(label='example/untrained')
        first = views.getUntrainedReactions(self.family)
        self.assertIs(views.getUntrainedReactions(self.family), first)
        calculate.assert_called_once_with(self.family)
        self.assertEqual(self.family.depositories, [])

    @patch.object(views, '_calculateUntrainedReactions')
    def test_reloaded_family_with_same_label_gets_fresh_result(self, calculate):
        calculate.side_effect = [object(), object()]
        first = views.getUntrainedReactions(self.family)
        reloaded = KineticsFamily(label=self.family.label)
        self.assertIsNot(views.getUntrainedReactions(reloaded), first)
        self.assertEqual(calculate.call_count, 2)

    def test_cache_does_not_retain_replaced_family(self):
        with patch.object(views, '_calculateUntrainedReactions', return_value=object()):
            views.getUntrainedReactions(self.family)
        reference = weakref.ref(self.family)
        del self.family
        gc.collect()
        self.assertIsNone(reference())
        self.assertEqual(len(views._untrained_reactions), 0)

    @patch.object(views, '_calculateUntrainedReactions')
    def test_failed_calculation_can_be_retried(self, calculate):
        calculate.side_effect = [ValueError('incomplete data'), object()]
        with self.assertRaises(ValueError):
            views.getUntrainedReactions(self.family)
        views.getUntrainedReactions(self.family)
        self.assertEqual(calculate.call_count, 2)

    @patch.object(views, '_calculateUntrainedReactions')
    def test_concurrent_requests_share_result(self, calculate):
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(views.getUntrainedReactions, [self.family] * 4))
        self.assertTrue(all(result is results[0] for result in results))
        calculate.assert_called_once_with(self.family)

    def test_slow_family_does_not_block_other_families(self):
        started = Event()
        release = Event()

        def calculate(family):
            if family is self.family:
                started.set()
                if not release.wait(timeout=5):
                    raise TimeoutError('Test did not release calculation')
            return KineticsDepository(label=family.label + '/untrained')

        with patch.object(views, '_calculateUntrainedReactions', side_effect=calculate):
            with ThreadPoolExecutor(max_workers=2) as executor:
                slow = executor.submit(views.getUntrainedReactions, self.family)
                try:
                    self.assertTrue(started.wait(timeout=5))
                    other = KineticsFamily(label='other')
                    fast = executor.submit(views.getUntrainedReactions, other)
                    self.assertEqual(fast.result(timeout=2).label, 'other/untrained')
                finally:
                    release.set()
                slow.result(timeout=5)

    @patch.object(views, 'getReactionUrl', return_value='/reaction/')
    def test_excludes_training_and_duplicate_reactions(self, reaction_url):
        def reaction(reactant, product):
            return Reaction(reactants=[Species().from_smiles(reactant)],
                            products=[Species().from_smiles(product)])

        trained = reaction('C', '[CH3]')
        untrained = reaction('CC', '[CH2]C')
        training = KineticsDepository(label='example/training')
        training.entries = {'1': Entry(item=trained), '2': Entry(item=trained.copy())}
        source = KineticsDepository(label='example/literature')
        source.entries = {
            '1': Entry(item=trained.copy()),
            '2': Entry(item=untrained),
            '3': Entry(item=untrained.copy()),
        }
        self.family.depositories = [training, source]
        result = views.getUntrainedReactions(self.family)
        self.assertEqual(len(result.entries), 1)
        self.assertIs(result.entries['1'].item, untrained)
        self.assertEqual(self.family.depositories, [training, source])
        self.assertIs(views.getUntrainedReactions(self.family), result)
        reaction_url.assert_called_once_with(untrained)
