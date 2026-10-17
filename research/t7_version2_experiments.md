# T7: Version-2 experiments, 17 October 2026

Base: `cc7ab4ca3277985c9bf190e703fe03ab1f06d965` (E4). The user confirmed E4 scored
1/20 payout and 15/20 annual on the same 20 cases. No hidden T7 targets or diagnostic
values were found locally. These experiments therefore measure contradictions with
the legacy bookings, example correctness, and output changes. They do not measure
new competition accuracy.

## What the unchanged score means

A payout passes only when all six fields are exact. Two wrong fields can hide the
benefit of correcting either one. H3 changed only four of 2,491 local rows, while
H1 changed many untaxed bases but only 13 rows with any tax booking. An unchanged
aggregate score does not reject either field-level rule. The recording also shows
that the leaderboard averages five original tasks and the two T7 tasks equally.
One extra correct T7 row out of 20 would add approximately 0.714 percentage points
to that average, assuming the other results and evaluation cases are unchanged.

## Corrected candidate in Version-2

1. Apply the existing surrender scale and waiver rules to withdrawals and full
   surrenders before calculating withholding. Convert the net amount to the tax
   currency after rounding it in policy currency. The existing E5 notes in a
   separate local checkout already identified this signal; it was reproduced here.
2. Return no remittance date when withholding and surcharges are zero. This changes
   182 stamp-only payouts, following the task's stated convention.

The payout tuple retains the gross fund-unit value. Italian BOL accrual and BOC
collection therefore keep their previous basis. A net withholding amount does not
establish a net policy-value basis for stamp duty. Death claims retain their
previous value: an uplift by the death-benefit option was not established by the
available evidence. Negative loss bases and the historical per-premium currency
conversion from E4 remain in place.

### Evidence for the penalty

| Booking-presence check | Gross amount | After penalty |
|---|---:|---:|
| Swiss VST: reporting objection and CHF amount above 5,000 | 2 disagreements / 1,661 | 0 / 1,661 |
| Italian SOS: positive gain, excluding death claims | 5 disagreements | 0 |
| Italian SOS: positive gain, including death claims | 9 disagreements | 4 |

The two Swiss threshold witnesses are BL10002408/8 (5,042.28 gross, 4,941.43 net)
and BL10004877/44 (5,092.72 gross, 4,939.93 net). Both are partial withdrawals with
no VST booking. The four remaining Italian disagreements are death claims. German
gain-sign agreement alone is insufficient because exempt contracts can have gains.
These presence checks support the direction of the correction, not cent-exact
amounts for all policies.

### Changes against E4 on the full local export

| Output | Changed rows |
|---|---:|
| Any payout field | 815 / 2,491 |
| Taxable base | 691 |
| Withholding | 69 |
| Surcharges | 10 |
| Country / stamp duty | 0 / 0 |
| Remittance date | 182 |
| Any annual field | 68 / 6,381 |

Annual changes are VST (43 rows), SOS (15), KST (10), SOL (10), and KIS (5), with
overlap across columns. STP and BOL are identical to E4. Keys are identical for
both payout and annual outputs.

## Alternative approaches tested

| Approach | Result | Decision |
|---|---|---|
| Convert the entire policy-currency gain at payout-date FX | Changes 502 DE/IT gains; Italian non-death booking contradictions rise from 0 to 49. Published German base becomes 539.30 instead of 5,628.16. | Reject. |
| Maintain one rounded premium account, subtracting each withdrawal's share | Changes 17 gains, seven with withholding; no gain-sign changes. | Unresolved; no evidence to prefer it. |
| One remittance batch on the next month's 10th for all countries | Changes 410 dates (257 CH, 153 IT); all amounts and annual outputs unchanged. Both examples pass. | Separate next-submission candidate. |
| Same common 10th, shifted off weekends | Changes 434 dates, including 24 DE rows. | Lower priority; no date labels support the extra adjustment. |

All local `TB_REMDT` fields are absent. The German example confirms one German
date; the January 10 year-end tax-booking schedule does not prove a monthly
remittance schedule. The common-10th candidate is explicitly unverified. It is
useful because it tests a broad remaining payout-only assumption while preserving
the corrected candidate's annual outputs.

Structural checks also ruled out promising-looking changes: event-number order
agrees with chronological payout order; tax-booking timestamps and effective dates
match the associated payout events. BOL is not booked at partial withdrawals, so
the suspected double-proration of a fresh BOL accrual cannot occur in these data.

## Validation

- Both published T7 examples are exact in the corrected and batch10 packages.
- All withholding, surcharges and collected duties are nonnegative.
- No remittance date is emitted without withholding.
- Annual VST/SOS/KST/SOL/KIS totals reconcile exactly to their payout movements.
- All T0-T5 local scores and counts reproduce: 99.9956%, 100%, 99.7350%, 99.7400%,
  99.9385%, and 55 outliers. These include manual corrections left in train targets.
- Local maintainability is 83.0, compared with 83.3 before the change; a small
  reduction, not a claimed improvement in that metric.
- Each upload archive contains 65 files, about 90 KB, with `submission.py` at its
  root. All helper modules, requirements, tools and notebooks are included.
  Notebook outputs are removed. Data, targets, caches and predictions are excluded.
- The batch10 archive was extracted and run against the full export. Exactly 410
  date fields differ from the corrected model; all other fields are equal.

## Run and compare

Use a fresh process per source tree. The baseline source can be obtained with
`git archive cc7ab4c starter_kit/my_solution` into a scratch directory.

```sh
python research/t7_experiments.py --legacy /path/to/legacy \
  --source /path/to/baseline/starter_kit/my_solution --output .cache/t7-version2/baseline.pkl
python research/t7_experiments.py --legacy /path/to/legacy \
  --output .cache/t7-version2/corrected.pkl --baseline .cache/t7-version2/baseline.pkl --matrix
python research/package_t7_candidates.py --output /path/to/outputs
```

The comparison snapshots and JSON reports are local ignored files. Packages have
SHA-256 manifests so the evaluated submission can be identified exactly.

## Recommended next evaluation

Use `t7-version2-batch10.zip` for the next broad T7 experiment: it combines the
penalty correction with a new date hypothesis. Keep `t7-version2-corrected.zip`
as the paired candidate with the previous dates. Both differ from E4 in the same
amount fields; they differ from each other only in remittance dates.

Record the uploaded archive hash, payout and annual counts, and whether the same
cases were used. A score increase is evidence for the submitted combination, not
proof that every included rule is right. A later comparison of the two packages
on the same cases isolates the date hypothesis. Another 1/20 result cannot rank
the two date models if incorrect amounts still block those rows. No official
submission was made during this investigation.

Sources: the two challenge PDFs, `SCHEMA.md`, the local `legacy/` export, the
existing E4/E5 investigation notes, the supplied recording, and the user's
confirmation of the latest evaluation. Recorded messages were treated as context,
not authorization to contact organisers or change other branches.
