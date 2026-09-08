# Kinetics browsing validation

Local measurements taken on 2026-09-08 using Python 3.9.23 in
`~/miniforge3/envs/rmg_env`, Django 4.2.30, RMG-Py at
`62eb728c0bb2d3c7c9f2f090dea1547a526e3903`, and
`~/code/RMG-database/input`. The database contained 125 kinetics families and
181 kinetics libraries. This local database copy did not expose a Git revision.

These are local Python page-handler timings, including template rendering;
they do not include browser assets, network latency, or production worker queues.
"First load" means an unloaded application database, not a cleared OS disk cache.
The benchmark uses example settings in memory and does not edit RMG data.

## Results

| Operation | Time |
| --- | ---: |
| Kinetics libraries index, first application load | 176.773 s |
| Kinetics libraries index, next request | 0.016 s |
| Kinetics families index, first application load, with cProfile enabled | 37.484 s |
| Kinetics families index, next request | 0.036 s |
| Changed libraries index, after all families are loaded | 0.014 s |
| Original libraries index from `main`, using the same loaded data | 28.319 s |

The original handler was extracted from `main:rmgweb/database/views.py` and run
with the uncached untrained-reaction calculation against the same website
database instance. Its modifications to family depositories were restored
afterward. The changed libraries index avoids this calculation entirely.

The profiled first family request spent approximately 14.4 s loading thermo
libraries, 8.3 s loading families, 7.1 s averaging rules, and 6.3 s adding rules
from training data. Profiling adds overhead, so that row is diagnostic rather
than an uninstrumented latency estimate.

## Real reaction data and cache invalidation

Loading three selected families with all their depositories took 0.790 s.
Their untrained-reaction calculations gave:

| Family | Training entries | NIST entries | Untrained reactions | First calculation | Cache lookup |
| --- | ---: | ---: | ---: | ---: | ---: |
| H_Abstraction | 3117 | 1312 | 222 | 17.089 s | 7.4 microseconds |
| R_Recombination | 175 | 519 | 110 | 0.179 s | 7.3 microseconds |
| Disproportionation | 137 | 117 | 20 | 0.090 s | 6.1 microseconds |

Cache lookup timings cover retrieving the derived depository, not rendering a
family or reaction page. Each result was compared with a fresh uncached
calculation, checking entry indices, reaction URLs, and reaction object identity.
The source depository lists were unchanged.

The check then called RMG-Py's actual `KineticsDatabase.load_families()` again.
It replaced the family objects, the old objects were garbage-collected, and
the weak-key cache released their entries. Requesting the reloaded
Disproportionation family recomputed its 20 untrained reactions in 0.091 s.

The 14 focused regression tests also passed through Django's `DiscoverRunner`,
including rendered links and counts, cache reuse, retry after failure, and
concurrent requests. Django reported a missing local `/var/www/static/`
directory; the context processor also reported the unversioned database copy.
Neither prevented these tests or rendered page checks from completing.

## Reproduce

With Django installed in the RMG environment, run from the repository root:

```bash
conda run -n rmg_env python scripts/benchmark_kinetics_browsing.py \
  --pages --baseline-ref main --output /tmp/kinetics-browsing.json
```

`--baseline-ref` executes the handler from that local Git ref; use the original
pre-change revision for the comparison. Omitting `--pages` runs just the real
family, cache, and reload checks. `--families Disproportionation` provides a
smaller check of the same path.

For this session, Django and its dependencies were installed under `/tmp`
without changing the existing conda environment. The equivalent command is:

```bash
MPLCONFIGDIR=/tmp/rmgweb-matplotlib PYTHONPATH=/tmp/rmgweb-django-test \
  ~/miniforge3/envs/rmg_env/bin/python scripts/benchmark_kinetics_browsing.py \
  --pages --baseline-ref main --output /tmp/kinetics-browsing.json
```

The reusable script's small real-data run was also executed successfully.
Its full-page mode reproduces the measurement sequence above without the
one-off cProfile instrumentation.

## Scope

The change removes eager untrained-reaction calculations from kinetics indexes
and caches the derived result when a family is selected. It does not make the
underlying RMG library/family loader lazy. That loader already retains data in
each worker and checks source-file timestamps before reloading it.

The initial library-loading cost remains and warrants a separate change, such
as a lightweight library catalog with individual library loading. The cache
added here is per process and does not survive worker restarts or share results
between workers. These measurements establish local behavior; production
timings and worker configuration still need separate verification.
