# Maintainability refactor after the T7 hypothesis commit

Baseline: `cf3f7ee8454340c813e43a4f4beb533a12cf35fa` (`hypothesis on t7`).
Prepared on 2026-10-17. The T7 experiment remains exactly the one documented in
`t7_iteration_1.md`; this refactor introduces no new tax convention.

## Measured improvement

| Scope | Before | After |
|---|---:|---:|
| Provided scorer: every Python file recursively under my_solution | 75.3 | 83.3 |
| Top-level runtime files, excluding tools | 75.4 | 82.9 |

The supplied scorer is unchanged. All new runtime and tool modules remain inside
the measured submission folder. No implementation was moved outside the scoring
scope. The task PDF describes a task-only scope; the runtime-only number above is
an approximation of that scope, not a claim about the organizer's file filtering.

## What changed

The refactor separates responsibilities while preserving original public imports:

- Historical tax rates, residence versions, gain basis, per-policy payout taxes,
  and whole-export annual aggregation.
- Monthly charge scheduling, calculation, and proportional allocation.
- CSV reading and decoding, cache management, numeric formats, and date formats.
- Versioned validity lookup, application-time offer terms, customer orders and
  historical fund valuation.
- Premium allocation, due-date recurrence, premium unit bookings and Swiss
  premium stamp duty.
- Visualization style, era charts, statement charts, policy data collection,
  timeline plotting and the timeline command-line entry point.

Repetitive documentation was shortened and explanations were placed beside their
implementations. Arithmetic expressions, rounding calls, conditionals, loops,
method signatures and decorators were preserved. ChargeRun and LegacyTables use
an inherited calculation/reader layer; original method imports and access remain
available. No legislated or historical rule was changed.

## Verification

`verify_mi_structure.py` resolves the original APIs against the refactored code.
It confirms identical executable ASTs, signatures and decorators for all **132**
original functions/methods, plus identical values and exports for **37** literal
constants. Only docstrings and source locations may differ in that comparison.

`verify_mi_refactor.py` captures the full local export, including policies without
train targets. It compares complete outputs for T0-T5 and both T7 functions,
yearly offer projections, charge aggregates, unit-history arrays, and a digest of
every individual booking. It also checks five extra valuation dates, including
both sides of the system conversion, and business days from 1990 through 2030.
The baseline contains **6,782,289 bookings** and **22,393 unit histories**.
The final comparison passed all 15 sections with exact baseline equality.

| Task | Local result before and after |
|---|---|
| T0 | 225,848 / 225,858 = 99.9956% |
| T1 | 15,028 / 15,028 = 100% |
| T2 | 3,011 / 3,019 = 99.7350% |
| T3 | 6,137 / 6,153 = 99.7400% |
| T4 | 34,124 / 34,145 = 99.9385% |
| T5 | Same 55 outlier keys |
| T7 payout | Same 2,491 complete rows |
| T7 annual | Same 6,381 complete rows |

`verify_mi_tools.py` compares **29** decoder, discovery-tool and chart results.
It covers blank and open-ended dates, impossible dates, numeric parsing fallback,
fixed-point scales, convention search, residual analysis, feature preparation,
rule finding, weak labels, linked policy-story collection, printed story output,
and four rendered chart images. It uses an isolated copy of the committed source
and synthetic fixtures; the figure hashes match exactly.

Snapshots and the committed source copy are local, ignored artifacts in
`.cache/mi-refactor/`. These are verification data and are not part of the
submission. New helper modules in `starter_kit/my_solution/` are required and
must be included when committing or packaging the submission.

Example rerun commands from the repository root:

```sh
.venv/bin/python research/verify_mi_structure.py \
  --baseline .cache/mi-refactor/committed/starter_kit/my_solution \
  --solution starter_kit/my_solution

.venv/bin/python research/verify_mi_refactor.py \
  --legacy /path/to/participants/legacy \
  --targets /path/to/participants/targets \
  --compare .cache/mi-refactor/before.pkl

.venv/bin/python research/verify_mi_tools.py \
  --solution starter_kit/my_solution \
  --compare .cache/mi-refactor/tools-before.json
```

T7 accuracy still requires organizer targets. Exact parity with the committed
hypothesis version means this revision does not create another T7 experiment:
any paired-case score difference would require investigation of the submitted
files, evaluation inputs or setup.

## Runtime and memory measurements

`benchmark_submission.py` runs the baseline and candidate sequentially in fresh
Python processes on the same input files, environment and fixed hash seed.
Version order alternates within pairs; an extra T7 batch reverses the starting
order. The full scenario includes T0-T5 followed by both T7 entry points, while
the standalone scenario executes only the two T7 entry points. Measurements
include submission imports but exclude scoring, retained verification snapshots,
and research-only intermediate-accounting checks. Filesystem caches are not
flushed. Peak memory is the process's maximum RSS, including native allocations.

| Measurement | Hypothesis-only baseline | MI refactor |
|---|---:|---:|
| Full scenario median runtime, 3 runs each | 30.95 s | 30.74 s |
| Full scenario median peak RSS | 1,742.91 MiB | 1,743.19 MiB |
| Standalone T7 median runtime, 6 runs each | 23.37 s | 23.55 s |
| Standalone T7 median peak RSS | 1,774.80 MiB | 1,774.88 MiB |

Peak memory is effectively unchanged. The full median runtime is 0.67% lower;
standalone T7 is 0.18 seconds (0.77%) higher. Thus there is no material resource
regression in these measurements, but the standalone runtime is not literally
identical or faster. Timings have overlapping observed ranges and cannot
guarantee performance on the organizer's machine. No runtime optimization or tax
formula change was made to hide this small difference.

Raw measurements are in `.cache/mi-refactor/performance.json`,
`performance-t7-confirmation.json`, and `performance-combined.json`.
