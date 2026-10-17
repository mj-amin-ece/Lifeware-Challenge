# T7 audit: what every payout field rests on

Written 2026-10-17, 20:30, after three organizer evaluations on the same 20 cases:

| Version | Payout | Annual |
|---|---:|---:|
| H0, base 0.00 when nothing is withheld | 1/20 | 15/20 |
| H1, base calculated even when nothing is withheld | 1/20 | 15/20 |
| H2 + H3, weekend dates to Monday, residence known at processing | 1/20 | 15/20 |

A payout row counts only if all six fields are exact, so the question is which field can fail 19 rows.

## Facts checked in this audit

- Event types (NRCODE `EVTTP`): **400 partial withdrawal**, **410 full surrender**, 500 death claim. `EV_PCTG` is
  the share of the whole policy paid out: 0.10-0.30 for withdrawals, 1.0 for surrenders and deaths.
- The payout amount (- sum of WDR/SUR/DTH bookings) equals the policy value times that share within +-0.6%: the
  bookings hold the **gross** unit value, before any surrender penalty.
- The German example (BL10000086, 121) is a full surrender after 7 years with **no penalty**; it cannot tell
  whether Neuron taxed the amount before or after a penalty.
- Tax rates (NRTAXR): CH VST 8% (threshold 5,000) unchanged since 1990; DE KST 25%, SOL 7.5% then 5.5% (1998), KIS
  9% (BW, BY 8%) from 2009, TFS 15% from 2018, HEV 50%; IT SOS 12.5%, 20% from 2012, 26% from 2014-07; IT BOL with a
  late entry (2012, entered 16 January) and a correction (2017-2019, corrected on 2019-07-15).
- The booked withholding tax matches the reported country in 498 of 498 payouts.
- In Italy and Germany, a payout with tax withheld is always a gain; a payout without is almost always a **loss**:
  IT 231 of 240, DE 165 of 195.

## Payout row, field by field

| Field | Rule in the code | Backed by | Payouts it decides |
|---|---|---|---:|
| country | address valid on the payout day, as known at processing (H3) | booked tax type 498/498; BL10000487 | 2,491 |
| base CH | payout converted to CHF on the payout day | 5,000 threshold compares the whole payout | 257 withheld |
| base IT, DE (gain) | payout in EUR - premiums converted on receipt day x share | DE example (COBOL, no penalty) | 241 withheld |
| base, nothing withheld | H1: as above, **losses clamped to 0.00** | nothing; H0 and H1 both 1/20 | 1,993 |
| withholding | base x rate known at processing, rounded by era | DE example | 498 |
| surcharges | DE: SOL + KIS on the KST | DE example (SOL only) | 88 |
| stamp duty | IT BOC: accrued BOL not yet collected x share | nothing for payouts | 295 |
| remittance date | DE 10th, IT 16th, CH month end + 30 days of the next month; stamp only: IT rule; weekend to Monday (H2) | DE: example; IT, CH: law only; H2: no gain | 680 |

177 of the 257 Swiss payouts with tax withheld are CHF policies (153 without a penalty). In those rows the base is
the payout itself, the tax a fixed 8% and the other amounts zero: if such rows are in the sample and fail, only the
remittance date (or the payout amount) can be the cause.

## Unverified rules, ranked by how many evaluated rows they could fail

1. **Losses reported as 0.00 (H5).** Neither H0 nor H1 changed it. Removing the clamp changes only the ~400 loss
   rows (IT 231, DE 165): all untaxed, so withholding, surcharges and annual amounts stay as they are.
2. **Remittance dates of CH and IT.** Only the German rule is confirmed. Candidates: the 10th of the next month for
   every country (Neuron's tax job ran on the 10th; the German example), the end of the next month, and None for
   rows with only stamp duty ("None if nothing was withheld").
3. **Surrender penalty (H4).** 334 full surrenders have a penalty (46 with tax withheld); our base uses the gross
   amount.
4. **Italian rates across 2012 and 2014.** The law taxes the gain accrued in each period at that period's rate; the
   code applies the rate of the payout day to the whole gain. 100 Italian payouts with tax withheld are after
   2014-06, 70 of them with premiums from before 2012.
5. **Italian stamp duty at payout (BOC, pro-rata BOL).** Never checked against a value.
6. German TFS, HEV and KIS: recent payouts only.
7. Surcharges written as `0` instead of `0.00` for CH and IT (410 rows): no effect under the published scorer, which
   compares numbers; free to fix.

## Next submissions

- **E4:** H5 (no clamp for losses), remittance dates back to the nominal ones (H2 brought no gain), surcharges as
  0.00. A gain can only come from H5, since the dates return to a version already scored.
- **E5:** the best date candidate from point 2, chosen by the E4 result.
- **E6 onwards:** H4, then the Italian rate split; keep every change that does not lower the count.
