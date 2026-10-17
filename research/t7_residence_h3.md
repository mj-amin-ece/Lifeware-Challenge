# T7 RESIDENCE — H3: the residence Neuron knew when it processed the payout

Prepared on 2026-10-17, on top of [T7 MONDAY — H2](t7_monday_h2.md) (commit `30f4abd`). Organizer result pending.

## Hypothesis

The task text says the payout row holds "the country of residence Neuron used". Addresses and policyholders are
versioned with a processing timestamp (`AD_CHGTS`, `HD_CHGTS`). A move that was reported after the payout was
processed cannot have been used by Neuron. H3 takes the address valid on the payout day among the versions entered
by the payout's processing time (`EV_CHGTS`); if none was entered yet, today's view is used as before.

## Local evidence

- For all 498 payouts with a withholding tax booked, the booked type (VST, SOS, KST) already matches the country of
  today's view, so H3 cannot break any of them, and it does not.
- BL10000487, event 96 (2024-02-05): today's view says DE, but Neuron booked Italian stamp duty (BOL, BOC) for this
  payout. The address known at processing time is IT. This is the one changed payout with bookings, and H3 agrees
  with them.

## Effect on the full local export

| Payout | H2 | H3 |
|---|---|---|
| BL10001113, 32 | CH, base 2,482.32 | LU, base 0.00 |
| BL10000261, 704 | DE, base 0.00 | CH, base 50,344.10 |
| BL10002693, 64 | LU, base 0.00 | CH, base 14,680.15 |
| BL10000487, 96 | DE, stamp 125.46, 2024-03-18 | IT, same amounts and date |

All other 2,487 payout rows and all 6,381 annual rows are unchanged; both examples of the task stay exact. t0-t5 do
not use these modules. Local MI 83.2.

## Reading the next result

H3 changes 4 of 2,491 payouts, so it most likely changes no evaluated row. A drop would point at one of the four
rows above; an unchanged count says nothing about H3. It is kept because the bookings support it, not because the
score can confirm it.
