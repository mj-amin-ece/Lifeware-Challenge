# T7 plan for the remaining evaluations

Written 2026-10-17, 21:50. Deadline Sunday 11:00; one evaluation every two hours; the same 20 payout and 20 annual
cases are reused. Scores so far: payout 1/20 and annual 15/20 for H0, H1 and H2+H3. E5 is being evaluated.

## What we know

- **Gates are right.** Which tax applies comes from Neuron's bookings; country 498/498, Swiss threshold on the net
  amount 1,660/1,660, stamp duty collected when accrued 283/283, church tax 88/88, SOL on every German tax.
- **Amounts are mostly right.** The annual rows hold the same withheld amounts as the payout rows (VST, SOS, KST,
  SOL, KIS) plus the Italian duty, and they score 15/20. The German example pins the FX conventions uniquely; the
  Italian example pins the duty; the bookings pin the net-of-penalty amount and the partial collection of the duty.
- **The Swiss base is the whole payout, for every contract type.** Swiss law taxes single-premium contracts on
  the gain, but Neuron withheld on all 163 loss-making payouts above the threshold (36 of them single premium), so
  the base is the payout; the gain model is ruled out.
- **The fields only the payout row has are the remittance date and the duty collected.** The collection logic
  matches every booking, so the Swiss and Italian remittance dates are the prime suspects for the taxed rows. Only the
  German date (10th of the next month) is confirmed. Neuron's tax job ran on the 10th of every month, Sundays
  included.
- Still unverifiable locally: the base of untaxed rows (0.00, clamped gain or signed gain), the death amount, the
  German church-tax formula, the Italian rate split, the German partial exemption.

## Candidates, all exported to ~/Desktop/t7_candidates/<name>/my_solution (branches of the same name)

| Name | Content |
|---|---|
| e5-main | E5: net of penalty, death benefit, no date without withholding, signed losses, law dates |
| e6-dates | E5 + remittance on the 10th of the next month for every country (410 rows change) |
| e6-dates-clamp | e6-dates + losses back to a base of 0.00 |
| e6-safe | Version-2 (penalty, no date without withholding; deaths and stamp duty unchanged) + losses 0.00 + the 10th: only evidence-backed changes, for a drop to 0/20 |
| e7-kis | E5 + German KST = base / (4 + church rate) for church members (29 rows) |
| e7-kis-dates | e6-dates + the same church-tax formula |

## Slot by slot

| When | Upload | Rule |
|---|---|---|
| ~23:40, R5 known | R5 ≥ 1: **e6-dates**. R5 = 0: **e6-safe** | the date test has the highest reach, so it goes first whatever R5 says; at 0/20 every unverified bet is undone at once |
| ~01:40 or morning, R6 known | R6 > R5: **e7-kis-dates**. R6 < R5: **e7-kis**. R6 = R5: **e7-kis-dates** if R5 = 1, else **e7-kis** | a tie at 1/20 means no taxed row passes under either date rule; the 10th is Neuron's observed job day, so it keeps the tie |
| last result before 11:00 | R7 ≥ R6: keep the church-tax formula, else drop it | |
| by 10:55 | push the best combination to ch-NaMa main; `git merge` of the chosen branch into main | |

Annual must stay near 15/20 throughout; a drop after E5 points at the net-of-penalty sums or the death benefit, a
drop after e7 at the church-tax formula.

Version-2 (branch of that name, notes in t7_version2_experiments.md) is E5 without the death benefit and the net
stamp-duty basis; its recommended next upload is the same date test.

## Reverts, one line each

- Losses to 0.00: `withholding.py`, `base = max(self.gain(...), Decimal('0.00'))`.
- Death as the value of the units: `tax_data.py`, `amount_paid`, return `money(sold, ...)` for DEATH.
- Stamp-only rows with an Italian date again: `payout_taxes.py`, the `remitted = ...` line of E4.
