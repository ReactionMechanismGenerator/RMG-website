#!/usr/bin/env python
"""Check kinetics browsing against an installed RMG-Py and real RMG-database.

Run in the RMG environment with Django installed. Uses the example website
settings in memory and an in-memory SQLite database. Does not edit RMG data.
"""

import argparse
import ast
import gc
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
import types
import weakref


def configure(root):
    sys.path.insert(0, str(root))
    secret = types.ModuleType('rmgweb.secretsettings')
    secret.__file__ = str(root / 'rmgweb/secretsettings.py')
    example = root / 'rmgweb/secretsettings.py.example'
    exec(compile(example.read_text(), str(example), 'exec'), secret.__dict__)
    secret.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    secret.ALLOWED_HOSTS = ['testserver']
    sys.modules[secret.__name__] = secret
    os.environ['DJANGO_SETTINGS_MODULE'] = 'rmgweb.settings'
    import django
    django.setup()
    return secret


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--families', nargs='+', default=[
        'H_Abstraction', 'R_Recombination', 'Disproportionation',
    ])
    parser.add_argument('--pages', action='store_true',
                        help='Also load the full website kinetics database and time page handlers.')
    parser.add_argument('--baseline-ref',
                        help='With --pages, compare the libraries handler from this trusted local Git ref.')
    parser.add_argument('--output', type=Path, help='Write measurements to this JSON file.')
    args = parser.parse_args()
    if args.baseline_ref and not args.pages:
        parser.error('--baseline-ref requires --pages')

    root = Path(__file__).resolve().parents[1]
    logging.basicConfig(level=logging.WARNING)
    secret = configure(root)
    import django
    import rmgpy
    from django.test import RequestFactory
    from rmgpy.data.kinetics import KineticsDatabase
    from rmgweb.database import views

    results = {
        'python': sys.version,
        'django': django.get_version(),
        'rmgpy': rmgpy.__file__,
        'database': secret.DATABASE_PATH,
        'measurements': [],
        'families': {},
    }

    def timed(label, function):
        print('Starting: ' + label, flush=True)
        start = time.perf_counter()
        value = function()
        measurement = {'stage': label, 'seconds': time.perf_counter() - start}
        results['measurements'].append(measurement)
        print(json.dumps(measurement), flush=True)
        if args.output:
            args.output.write_text(json.dumps(results, indent=2) + '\n')
        return value

    database = KineticsDatabase()
    path = os.path.join(secret.DATABASE_PATH, 'kinetics', 'families')
    timed('load selected families, all depositories',
          lambda: database.load_families(path, families=args.families, depositories='all'))
    for label in args.families:
        family = database.families[label]
        sources = list(family.depositories)
        result = timed(label + ': first calculation', lambda: views.getUntrainedReactions(family))
        cached = timed(label + ': cache hit', lambda: views.getUntrainedReactions(family))
        assert cached is result
        expected = timed(label + ': uncached reference', lambda: views._calculateUntrainedReactions(family))
        assert [(e.index, e.label, id(e.item)) for e in result.entries.values()] == [
            (e.index, e.label, id(e.item)) for e in expected.entries.values()
        ]
        assert family.depositories == sources, 'Calculation mutated the source depositories'
        results['families'][label] = {
            'source_entries': {d.label: len(d.entries) for d in sources},
            'untrained': len(result.entries),
        }

    # Exercise RMG-Py's real reload, including weak-reference eviction.
    label = args.families[-1]
    old = weakref.ref(database.families[label])
    expected_count = len(result.entries)
    del family, sources, result, cached, expected
    timed(label + ': reload from disk',
          lambda: database.load_families(path, families=[label], depositories='all'))
    gc.collect()
    assert old() is None, 'Cache retained the old family after reload'
    assert database.families[label] not in views._untrained_reactions
    fresh = timed(label + ': recompute after reload',
                  lambda: views.getUntrainedReactions(database.families[label]))
    assert len(fresh.entries) == expected_count
    results['real_data_checks_passed'] = True

    if args.pages:
        request = RequestFactory().get('/database/kinetics/families/')

        def page(handler, section):
            response = handler(request, section=section)
            assert response.status_code == 200
            return response

        # This is the separate, initially unloaded website database instance.
        timed('libraries page: first load', lambda: page(views.kinetics, 'libraries'))
        timed('libraries page: warm', lambda: page(views.kinetics, 'libraries'))
        timed('families page: first load', lambda: page(views.kinetics, 'families'))
        timed('families page: warm', lambda: page(views.kinetics, 'families'))
        timed('libraries page: warm after loading families', lambda: page(views.kinetics, 'libraries'))
        results['loaded_families'] = len(views.database.kinetics.families)
        results['loaded_libraries'] = len(views.database.kinetics.libraries)

        if args.baseline_ref:
            # Use the original handler and uncached algorithm on exactly the
            # same loaded data. Restore its synthetic depository mutations.
            source = subprocess.check_output([
                'git', 'show', args.baseline_ref + ':rmgweb/database/views.py',
            ], cwd=root, text=True)
            node = next(node for node in ast.parse(source).body
                        if isinstance(node, ast.FunctionDef) and node.name == 'kinetics')
            namespace = dict(vars(views), getUntrainedReactions=views._calculateUntrainedReactions)
            exec(compile(ast.Module(body=[node], type_ignores=[]), '<baseline kinetics>', 'exec'), namespace)
            original = {label: list(family.depositories)
                        for label, family in views.database.kinetics.families.items()}
            try:
                timed('baseline libraries page: warm after loading families',
                      lambda: page(namespace['kinetics'], 'libraries'))
            finally:
                for label, family in views.database.kinetics.families.items():
                    family.depositories = original[label]

    if args.output:
        args.output.write_text(json.dumps(results, indent=2) + '\n')
    print('PASS: real-data correctness, cache reuse, source preservation, and reload invalidation', flush=True)


if __name__ == '__main__':
    main()
