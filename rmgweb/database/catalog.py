"""Lightweight kinetics catalogs and isolated, on-demand library loading."""

import ast
from concurrent.futures import Future
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
import tokenize
from typing import Optional


class KineticsDatabaseNotFound(ValueError):
    """The requested kinetics database label does not exist."""


@dataclass(frozen=True)
class CatalogEntry:
    label: str
    name: str
    short_desc: str = ''


@dataclass(frozen=True)
class FamilyCatalogEntry:
    label: str
    name: str
    groups: CatalogEntry
    rules: Optional[CatalogEntry]
    depositories: tuple


class KineticsCatalog:
    """Read index metadata without constructing reactions or preparing rules.

    Selected libraries use RMG's normal loader, including its chemistry checks,
    but live separately from the complete database used for kinetics searches.
    Cached values are replaced when their source-file signatures change.
    """

    def __init__(self, path):
        self.path = Path(path)
        self._cache = {}
        self._lock = Lock()

    @staticmethod
    def _signature(paths):
        return tuple((stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
                     for stat in (p.stat() for p in paths))

    def _cached(self, key, signature, load):
        with self._lock:
            previous = self._cache.get(key)
            calculate = previous is None or previous[0] != signature
            if calculate:
                future = Future()
                self._cache[key] = (signature, future)
            else:
                future = previous[1]
        if calculate:
            try:
                future.set_result(load())
            except BaseException as error:
                with self._lock:
                    if self._cache.get(key) == (signature, future):
                        del self._cache[key]
                future.set_exception(error)
                raise
        return future.result()

    def _metadata(self, path, label):
        def read():
            with tokenize.open(path) as source:
                tree = ast.parse(source.read(), filename=str(path))
            values = {}
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in ['name', 'shortDesc']:
                            try:
                                value = ast.literal_eval(node.value)
                            except (ValueError, TypeError):
                                value = ''
                            values[target.id] = value if isinstance(value, str) else ''
            return CatalogEntry(label, values.get('name') or label, values.get('shortDesc', ''))

        return self._cached(('metadata', path), self._signature([path]), read)

    def _library_paths(self):
        root = self.path / 'libraries'
        return {p.parent.relative_to(root).as_posix(): p for p in root.rglob('reactions.py')}

    def libraries(self, subsection=''):
        return [(label, self._metadata(path, label))
                for label, path in sorted(self._library_paths().items()) if subsection in label]

    def families(self):
        result = []
        for path in sorted((self.path / 'families').iterdir()):
            if not path.is_dir() or not (path / 'groups.py').is_file():
                continue
            label = path.name
            groups = self._metadata(path / 'groups.py', label + '/groups')
            rules = CatalogEntry(label + '/rules', label + '/rules') if (path / 'rules.py').is_file() else None
            depositories = tuple(self._metadata(p, label + '/' + p.parent.name)
                                 for p in sorted(path.glob('*/reactions.py')))
            result.append((label, FamilyCatalogEntry(label, label, groups, rules, depositories)))
        return result

    def library(self, label):
        # Resolve only labels discovered inside the catalog, including nested
        # libraries. Never turn a URL parameter directly into a filesystem path.
        try:
            path = self._library_paths()[label]
        except KeyError:
            raise KineticsDatabaseNotFound('Unknown kinetics library: {0}'.format(label))
        signature = self._signature([path, path.parent / 'dictionary.txt'])

        def load():
            from rmgpy.data.kinetics import KineticsDatabase
            from rmgpy.data.kinetics.library import KineticsLibrary

            context = KineticsDatabase()
            library = KineticsLibrary(label=label)
            library.load(str(path), context.local_context, context.global_context)
            return library

        return self._cached(('library', path), signature, load)
