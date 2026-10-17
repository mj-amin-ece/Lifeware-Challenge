# T7 organizer evaluation: iteration 1

Prepared on 2026-10-17. Previous organizer results: payout **1/20**, annual **15/20**.
New organizer results are pending; there are no local T7 targets.

## Purpose of the experiment

Use the next organizer evaluation both to seek better accuracy and to learn a
general reporting convention for the final implementation. The change is a
testable hypothesis, not a locally verified accuracy improvement. A lower score
is possible. The original implementation and its outputs are preserved so that
we can revert or refine the change after interpreting the evidence.

The competing hypotheses are:

- **H0 (original implementation):** no withholding booking means the reported
  taxable base is zero.
- **H1 (this revision):** the reported base is calculated independently of whether
  withholding was booked; an exempt or otherwise untaxed payout can still have a
  nonzero reported base.

Why H1 is worth testing:

- A payout row includes a base as a separate field from withholding. The task text
  does not explicitly say that absence of withholding erases that field.
- The original early return coupled the two fields without an exact target
  establishing that convention. The T7 notebook explicitly listed this as an
  unconfirmed assumption.
- Locally, 1,993 of 2,491 payouts have no main withholding booking (including 154
  Luxembourg payouts). This assumption therefore has broad potential impact.
- The organizer reported payout **1/20** but annual **15/20**. A payout-only field
  error is compatible with this gap, although the small samples do not establish
  its cause or representativeness.
- Both supplied examples already matched before the revision. They remain useful
  regression anchors but do not distinguish H0 from H1 on untaxed payouts.

## Hypothesis and change

`withholding.py` previously returned a zero base whenever no withholding tax was
booked. This iteration calculates the reported base before checking whether to
withhold: the payout amount converted to CHF for Switzerland, the nonnegative
gain for Italy, and the nonnegative gain with the existing adjustments for Germany.
Luxembourg retains a zero base because no withholding regime is implemented for it.
The booking still determines whether tax amounts are calculated.

This is a candidate convention to test with the organizer, not an established
legacy rule. Remittance dates, stamp-duty formulas and tax amounts were deliberately
kept unchanged to isolate the effect of the reported base.

This revision tests the specific bases above, not every possible interpretation
of H1. Whether an exempt base should instead be zero, whether losses should be
negative, and whether German exemptions alter the reported base remain open
questions. The initial hypothesis-only commit contained no MI refactor; the
combined submission below adds an output-equivalent MI refactor.

## Local comparison

- Same 2,491 payout keys and 6,381 annual rows.
- 1,442 previously zero bases became nonzero: CH 1,403; DE 30; IT 9.
- All other payout columns are exactly unchanged.
- Every annual row is exactly unchanged.
- Both examples from the task description still match all columns exactly.
- T0-T4 scores remain 99.9956%, 100%, 99.7350%, 99.7400%, and 99.9385%; T5 still
  flags 55 outliers. The hypothesis-only code's local MI was 75.3/100; the
  combined submission's local MI is 83.3/100.

Before/after snapshots, the original `withholding.py`, comparison statistics and
the validation log are saved locally in `.cache/t7-base-v1/` (ignored by Git).
The independent rerun is logged in `.cache/t7-base-v1/regression-rerun.log`.

Revision identity, to distinguish this experiment from later changes:

- Base Git commit: `2350c9b1dab2ab296bc02d95c5620efbd7972596`.
- Revised `withholding.py` SHA-256:
  `e2353734d81200faa9ec9df1f774d6226f73c7d681276e4f7dc2e2cebe2371e0`.
- Original `withholding.py` SHA-256:
  `12a7be71827cd882adf25515193eff62e14c4af932b40c9cf187b42d500fbfc9`.

## Combined submission: the same H1 experiment plus MI refactoring

The hypothesis-only code was committed as
`cf3f7ee8454340c813e43a4f4beb533a12cf35fa`. The proposed submission combines that
H1 with the MI refactor documented in [mi_refactor.md](mi_refactor.md).
The hashes above identify the earlier source layout, not the refactored files.
Gain and German-base methods now live in `payout_basis.py`; `withholding.py`
still calculates the base before checking whether withholding was booked.

The comparison chain is:

| Version | T7 calculation behavior | Local MI |
|---|---|---:|
| Previously evaluated H0 | Untaxed payouts have zero base; organizer scored payout 1/20, annual 15/20 | 75.3 |
| Committed H1 (`cf3f7ee`) | Calculate base independently of withholding | 75.3 |
| H1 plus MI refactor | Exactly the same T7 outputs as committed H1 on the full local export | 83.3 |

Final verification confirms:

- All 2,491 payout rows and 6,381 annual rows equal the committed H1 outputs.
- Relative to H0, the only changes remain 1,442 formerly zero payout bases:
  CH 1,403; DE 30; IT 9. Every other payout column and every annual amount remain
  identical to H0.
- All 132 original callable bodies, signatures and decorators retain identical
  executable ASTs, with all 37 checked literal constants unchanged. The MI
  refactor reorganizes the implementation without changing the calculation steps.
- The final source files match the hashes captured for the complete regression
  run, including intermediate accounting verification.

Therefore the combined submission does not introduce a second T7 calculation
hypothesis. Organizer feedback still tests H1 against H0, subject to the sampling
and exact-row limitations below. This is strong local equivalence evidence, not
an organizer accuracy result or a formal proof over every possible input.
All new helper modules must be included when committing or packaging the code.
Record the actual combined submission commit when it is available.

## Reading the next result

Record correct/total counts separately for payout and annual. If the organizer
uses the same cases, the annual result should be unchanged. If cases change,
score movements also reflect the changed sample; each of 20 rows is five
percentage points. No improvement can be established locally without targets.

| Outcome on the same payout cases | Interpretation |
|---|---|
| More than 1/20 correct | Evidence that the revised bases improve the net result on those cases; does not prove the convention for every country or payout type. |
| Fewer than 1/20 correct | Evidence that the revised bases worsen the net result on those cases; inspect the country and base convention before keeping the revision. |
| Still 1/20 correct | Inconclusive: changed cases may be absent, wins and losses may cancel, or other incorrect columns may still prevent a row from matching. |

Only fully exact payout rows count. A better base alone cannot improve the score
if the same row still has a wrong remittance date or another wrong amount. If the
sample changes, none of the score directions above provides a controlled
comparison. An unchanged annual score alone does not prove that cases stayed the
same. An annual score change cannot come from this revision's annual calculations
on identical inputs; check the sample, submitted version, or evaluation setup.

## Next result and follow-up

- Submission time/version: **not yet recorded**.
- New payout correct/total: **pending**.
- New annual correct/total: **pending**.
- Same evaluation cases as baseline: **unknown**.
- Organizer examples, column breakdowns, or other feedback: **pending**.
- Decision to keep, revert, or refine: **pending**.

When results arrive, first confirm which revision was submitted and whether the
cases were reused. Interpret the result using the table above. If evidence is
insufficient, avoid declaring H0 or H1 established. The next independent
investigations are remittance conventions, partial-withdrawal basis/collection,
and Italian stamp-duty accruals; preserve this iteration's snapshots before
changing those formulas. Use feedback to discover general rules, not to hardcode
individual evaluation results.
