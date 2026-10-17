# T7 MONDAY — H2: weekend remittance dates

Prepared on 2026-10-17. Remembering name: **T7 MONDAY**.
Status: implemented and locally validated; organizer result pending.

## Purpose and frozen baseline

Test one payout reporting convention using the next organizer evaluation. This
is a candidate legacy behavior, not a verified tax rule or promised improvement.
The baseline is commit `baec875` (H1 plus MI refactoring): payout **1/20**, annual
**15/20**. The organizer confirmed that the two previous runs used the same
20 cases. Whether the next run will reuse them must still be recorded.

The earlier base experiment remains documented in
[t7_iteration_1.md](t7_iteration_1.md). H1's independent taxable-base calculation
stays in place for this comparison; its unchanged score did not resolve H1.
Do not revert H1 or introduce another calculation convention in this submission.

## Hypothesis and exact scope

- **R0, baseline:** report the nominal remittance date already calculated by
  `tax_rules.remittance_date`, even when it falls on Saturday or Sunday.
- **R1, T7 MONDAY:** first calculate exactly the same nominal date, then move
  Saturday forward two days and Sunday forward one day. Leave Monday-Friday
  dates untouched. Leave absent dates as `None`.

Apply R1 to all remittance dates, including Italian stamp-duty collections.
Country selection, existing country-specific nominal deadlines, bases, tax
amounts, stamp duties, rounding, payout keys, and annual calculations stay the
same. A date moving into another month or year does not move an annual amount:
this experiment changes payment-date reporting, not annual attribution.

Do not add public-holiday adjustments. The existing learned business calendar
comes from fund-price publication days; it does not establish the tax-office
calendar for Switzerland, Germany or Italy. Testing weekend handling alone
avoids combining those assumptions. No external database, current tax-law rule,
target value or evaluation-key special case enters the implementation.

## Why test this next?

The challenge asks when taxes were paid, and the current code reports some
weekend dates. Moving those dates is a plausible convention to test, not evidence
that Neuron actually used it. The data dictionary describes `TB_REMDT` as the
date remitted to the tax office, but every local `NRTAXB.TB_REMDT` is missing;
there are no date labels to settle the choice locally.

Audit of the frozen full local payout snapshot:

| Coverage | Rows |
|---|---:|
| All payout rows | 2,491 |
| Rows with a remittance date | 680 |
| Weekend dates, and therefore predicted changed rows | 201 |
| Saturday / Sunday | 98 / 103 |
| Changed rows by residence: CH / IT / DE | 89 / 86 / 26 |

Thus R1 changes 29.6% of dated payouts and 8.1% of all local payouts. These are
local coverage figures, not estimates of the organizer's curated sample. Unlike
H1, whose 1,442 changed bases included only 13 payouts with any tax booking,
this experiment directly targets dated tax payments.

DatabaseSample and Databricks may suggest concepts to audit, but they supply no
Neuron tax targets. Assigning one external database to payout and another to
annual would not identify which database is closer: the tasks, samples and
starting accuracies differ. Here the feedback tests a named rule instead.

## Verification required before submission

1. Preserve the baseline source, source hashes and complete output snapshot in
   ignored `.cache/t7-monday/` artifacts before editing production code.
2. Verify weekday dates stay unchanged, Saturdays/Sundays move to the following
   Monday, and month/year/leap-year boundaries work. Check the supplied payout
   example still matches.
3. Rerun T0-T5 and both T7 functions over the full local export. Require exact
   equality of T0-T5, accounting checks, all payout keys, payout columns 1-5 and
   every annual row. Require the only payout differences to be the 201 weekend
   dates, with the documented country split. Preserve both PDF examples.
4. Check the existing T6 tool fixtures and measure MI. Compare standalone T7
   runtime and peak memory against the frozen baseline in fresh processes.
5. Record results and source fingerprints below. Verification artifacts are not
   submission dependencies. The runtime change belongs inside `my_solution`.

## How correct-out-of-20 feedback guides the next decision

Twenty cases are enough for a narrow engineering decision on a **fixed sample**,
but not enough to prove the rule generally or identify every wrong field.
These curated cases are not known to be random or independent. Do not turn the
count into a population-accuracy confidence claim.

With identical inputs and evaluation, and the date as the only changed field:

`new correct count - 1 = newly passing rows - previously passing rows lost`.

A newly passing row must have benefited from its new date, because its other
five output fields are unchanged. Some improved dates can remain invisible if
another field in that row is still wrong. Equal counts can also hide exchanging
one passing row for another. Only one previously passing row can be lost because
the baseline had exactly one pass.

| Next payout result on the same 20 cases | Interpretation and next action |
|---|---|
| **2-20/20** | Net exact-row improvement caused by the date change. Keep R1 provisionally for this sample; freeze it while investigating the next field. A large gain is stronger practical evidence than a one-row gain, but neither establishes all-country correctness. |
| **1/20** | No net benefit. The changed cases might be absent, other fields may mask date improvements, or one gain may offset one loss. Do not mark R1 true or false. Prefer R0 for the next isolated experiment absent other evidence; preserve R1 for possible retesting after amount fixes. |
| **0/20** | Net regression: the old passing row was harmed by the date change. Return to R0 for the next submission and investigate country/era differences before reconsidering R1. This does not prove R1 is wrong on every failed row. |

**Annual should remain 15/20 on identical inputs and evaluation.** Any change
requires investigating the submitted version, case selection, inputs or scoring;
it cannot be an intended effect of this date-only experiment. An unchanged
annual count by itself does not establish that payout cases were identical.

If the organizer changes cases, the two aggregate scores no longer isolate R1.
Record the result but do not apply the causal decision table; a comparison on
the same cases or additional feedback is needed. Even one anonymized failed
row or per-column correct counts would be much more informative than the total.

After an unchanged result, prioritize a different payout field supported by a
local audit (for example partial-withdrawal basis or duty collection), rather
than stacking date variants indefinitely. Preserve annual behavior unless a
separate, evidenced annual hypothesis can be isolated. Learn general rules;
do not special-case hidden evaluation rows.

## Run record

- Organizer submission time / submitted commit: pending.
- Payout correct / total: pending / 20.
- Annual correct / total: pending / 20.
- Same payout cases as baseline: pending confirmation for this run.
- Same annual cases as baseline: pending confirmation for this run.
- Other organizer feedback: pending.
- Decision: pending.

## Implementation and validation record

The experiment specification above was written before changing production code.
The only runtime file changed is
[`tax_rules.py`](../starter_kit/my_solution/tax_rules.py), in
`remittance_date`. All other 55 Python source files match `baec875` byte for byte.
No new runtime dependency, calendar construction or retained cache was added.

Frozen baseline: `.cache/t7-monday/baseline/my_solution/` and `before.pkl`.
Full candidate results: `.cache/t7-monday/after.pkl`. The original snapshot was
copied from the previously verified `presubmission-baec875.pkl`; the current
baseline source was checked against the committed source before editing.

| Verification | Result |
|---|---|
| T0 | 225,848 / 225,858 = 99.9956%; full outputs equal baseline |
| T1 | 15,028 / 15,028 = 100%; full outputs equal baseline |
| T2 | 3,011 / 3,019 = 99.7350%; full outputs equal baseline |
| T3 | 6,137 / 6,153 = 99.7400%; full outputs equal baseline |
| T4 | 34,124 / 34,145 = 99.9385%; full outputs equal baseline |
| T5 | Same 55 outlier keys |
| T6 tools | All 29 existing decoder, discovery and chart checks match baseline |
| T7 payout | Same 2,491 keys; exactly 201 dates changed, CH 89 / IT 86 / DE 26; all other fields identical |
| T7 annual | All 6,381 complete rows exactly equal baseline |
| Boundary fixtures | 16 pass, including both weekend days, month/year changes, leap years and a weekday holiday left unchanged |
| PDF examples | Both exact, payout and annual |
| Accounting | Same 6,782,289 booking digests and 22,393 unit histories; charge aggregates, projections, extra valuations and 41 years of business days unchanged |
| Supplied local MI scorer | 83.3 before and after |

The 201 changed dates are listed in `.cache/t7-monday/comparison.json`; this
report also captures all 56 final source hashes. Logs are `validation.log`,
`isolation.log` (final verifier replay against captured outputs) and `tools.log`
in that directory. These are output-equivalence checks, not T7 accuracy scores.

Reproduce from the repository root:

```sh
.venv/bin/python research/verify_t7_monday.py \
  --legacy /path/to/participants/legacy \
  --targets /path/to/participants/targets \
  --baseline .cache/t7-monday/before.pkl \
  --output .cache/t7-monday

.venv/bin/python research/verify_mi_tools.py \
  --solution starter_kit/my_solution \
  --compare .cache/mi-refactor/tools-before.json
```

Source identity, SHA-256 of `starter_kit/my_solution/tax_rules.py`:

- Baseline: `a97c12a281126332f41ce473d75f5892a2101f9ac4473626cc80b303b3cc9eb2`.
- T7 MONDAY: `33a333e1cb0f0942bfb85640958e391ae9df863b877394fa65a62eb9239eecae`.

To return to R0, restore only `remittance_date` from the frozen baseline. Keep
H1's independent base calculation and the MI refactor. Do not revert the whole
experiment chain.

### Runtime and memory

Ran six fresh processes per version across two batches, each with alternating
version order. The second batch reversed the starting order. Both T7 entry
points ran against the same export and environment, using
`research/benchmark_submission.py --scenarios t7 --repeat 3` and then the same
command with `--candidate-first`.

| Measurement | Frozen H1/MI baseline | T7 MONDAY |
|---|---:|---:|
| Median standalone T7 runtime | 23.306 s | 23.411 s |
| Observed runtime range | 23.091-23.595 s | 23.270-25.656 s |
| Median process CPU time | 23.256 s | 23.305 s |
| Median peak RSS | 1,774.89 MiB | 1,775.13 MiB |

The measured runtime median is **0.105 s higher (0.45%)** and median peak RSS
is **0.24 MiB higher (0.014%)**. The first batch's runtime median was 1.13%
higher; the confirmation and pooled results are retained rather than selecting
only favorable measurements. The candidate's 25.656 s run is also retained.
The observed ranges overlap. There is no material resource regression in these
measurements, but they do not establish literally zero overhead or guarantee
timing on the organizer's machine.

A separate alternating helper-only measurement used the actual country/day
arguments for all 680 dated payouts: seven samples per version, each averaging
50 repetitions. Their combined helper runtime medians were 1.127 ms before and
1.179 ms after, an extra **0.052 ms for all 680 dates**. Thus the extra date
arithmetic is very small relative to the full T7 run. No new persistent data
structure or expensive calendar inference was introduced.

Raw artifacts in `.cache/t7-monday/`: `performance.json`,
`performance-confirmation.json`, `performance-combined.json`, `date-helper.json`
and both performance logs. Performance measurements exclude verification
snapshots and accounting-digest checks.
