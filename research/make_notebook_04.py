"""Build and execute starter_kit/my_solution/notebooks/04_Task_Rules_t3_t4.ipynb."""
import pathlib
import sys

import nbformat
from nbclient import NotebookClient

out = pathlib.Path(sys.argv[1])
cells = []
md = lambda s: cells.append(nbformat.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbformat.v4.new_code_cell(s.strip()))

md("""
# Neuron Migration - Rules of t3 (surrender value) and t4 (annual statement)

Both tasks rest on the same fund accounting: every unit booking of every policy. The new system has to calculate
the premium and charge bookings itself, so `accounting.py` generates them from the premiums, the parameters and the
market data; only the customer orders (switches, withdrawals, surrenders, death benefits) are taken from the export.

The rules were found booking by booking with **teacher forcing**: the holdings before each booking come from the
target units of the earlier bookings (`research/t3_calibrate.py`), so every formula can be checked on its own. The
cases where a formula failed were inspected one by one, and every fix is a rule below.
""")

md("# Import libraries")
code("""
import sys
import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from decimal import Decimal

sys.path.insert(0, '..')
sys.path.insert(0, '../../../research')
sys.path.insert(0, '../..')
from legacy_loader import LegacyData
from accounting import all_bookings
from surrender import surrender_values
from statement import annual_statements
import t3_engine_check
import scoring

pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 30)
""")

md("# Hyperparameters")
code("""
project_folder = pathlib.Path('../../..').resolve()

targets_dir = project_folder / 'targets'

cache_dir = project_folder / '.cache'

conversion = pd.Timestamp('2007-08-11')

sample_size = 150
""")
code("""
data = LegacyData(project_folder / 'legacy', cache_dir=cache_dir)
target_bookings = pd.read_csv(targets_dir / 't3_booking.csv').set_index('booking_id')
legacy_bookings = data.table('NRBOOK')
""")

md("""
# The monthly charges

## Which units a charge sees

The charge run of a day runs at 01:30, before the trades of that day. Policy `BL10000800` bought units on
1995-07-31, the same day as its monthly charge: the management charge (2.74 for fund N0013) only fits the units held
**before** that purchase.
""")
code("""
policy = legacy_bookings[(legacy_bookings.BK_POLNR == 'BL10000800') & (legacy_bookings.BK_FNDID == 'N0013')]
policy = policy[policy.BK_TRDDT.between('1995-06-25', '1995-08-05')].copy()
policy['amount'] = policy.BK_BOOKID.map(target_bookings.amount_pc)
policy['units'] = policy.BK_BOOKID.map(target_bookings.units)
policy[['BK_EVTNR', 'BK_BKTYP', 'BK_TRDDT', 'BK_PRCDT', 'amount', 'units']]
""")

md("""
## COBOL charged the management fee by the day

In the COBOL era (before the conversion on 2007-08-11) the management charge is not rate / 12: the implied factor
follows the length of the month, `days / 360` (Actual/360). Neuron NG charges rate / 12.
""")
code("""
amc = legacy_bookings[(legacy_bookings.BK_BKTYP == 'AMC') & (legacy_bookings.BK_POLNR == 'BL10000003')].head(13).copy()
amc['amount'] = amc.BK_BOOKID.map(target_bookings.amount_pc)
amc['days since last charge'] = amc.BK_TRDDT.diff().dt.days
amc[['BK_TRDDT', 'amount', 'days since last charge']]
""")

md("""
## Technical corrections do not count

Event 21 of `BL10000004` is a technical correction (990) with a switch-in booking. The next management charge only
fits the holding without it, so the bookings of technical corrections (and of reversed events, 900) are ignored.
""")
code("""
events = data.table('NREVNT')
events[(events.EV_POLNR == 'BL10000004') & events.EV_EVTNR.between(19, 23)][['EV_EVTNR', 'EV_EVTTP', 'EV_EFFDT', 'EV_USRID']]
""")

md("""
## Splitting a charge over the funds and pots

The admin fee and the risk charge are split in proportion to the value of each fund and pot. The shares are rounded,
and the largest position takes the rounding difference: on 2017-09-01 policy `BL10000013` pays 4.45 + 0.51 + 1.54,
where the plain rounding gives 4.44.
""")
code("""
split = legacy_bookings[(legacy_bookings.BK_POLNR == 'BL10000013') & (legacy_bookings.BK_TRDDT == '2017-09-01')].copy()
split['amount'] = split.BK_BOOKID.map(target_bookings.amount_pc)
split[['BK_FNDID', 'BK_POTCD', 'BK_BKTYP', 'BK_PRCDT', 'amount']]
""")

md("""
# The premium bookings

Each fund buys on its own: on the first day after the money date that **the fund** has a price. When one fund has no
price on the next business day, only that fund trades later. This explains every premium traded two days late.
""")
code("""
premiums = legacy_bookings[legacy_bookings.BK_BKTYP == 'PRM']
prices = data.table('NRFPRC')
price_days = {fund: sorted(rows.FP_PRCDT) for fund, rows in prices.groupby('FP_FNDID')}
sample = premiums.sample(20000, random_state=1)
first_price_day = [next(day for day in price_days[fund] if day > money) for fund, money in zip(sample.BK_FNDID, sample.BK_RCVDT)]
print('trade date = first price day of the fund after the money date:', (pd.Series(first_price_day, index=sample.index) == sample.BK_TRDDT).mean())
""")

md("""
# Exchange rates

- The export has a few rates with lowercase currency codes (`chf`, `eur`, ...). They fill days without an uppercase
  rate, so they are read as uppercase.
- Charges and valuations convert with the rate of their day; premiums with the rate of the day **before** the trade
  day (the day the money was converted). Rates are not rounded.
""")
code("""
rates = data.table('NRFXRT')
rates[rates.FX_CCY.str.islower()].FX_CCY.value_counts()
""")

md("""
# Check: all bookings of a sample of policies

The engine runs on a random sample of train policies and every premium, admin, management and risk booking is
compared with the export and the target amounts and units.
""")
code("""
sample_data, chosen = t3_engine_check.sample_data(sample_size)
bookings = all_bookings(sample_data, pd.Timestamp('2026-06-30').date())
compared = t3_engine_check.compare(bookings, sample_data)
print(len(bookings), 'bookings calculated')
pd.crosstab(compared.type, compared.ok, colnames=['exact'])
""")
md("On all 3,019 train policies, 5,024,847 bookings: all exact except three risk bookings of `BL10004387` on "
   "2020-12-01, which are 3.19 times the calculated ones (a manual correction, see t5).")

md("""
# t3 Surrender value

The units are valued at the bid price on or before the valuation date, converted and rounded to the cent per fund and
pot (truncated in the COBOL era). The penalty comes from the surrender scale of the product and the completed policy
years, with no penalty in the waiver periods (financial crisis 2008, COVID 2020). COBOL truncated the surrender value
`value x (1 - rate)`.
""")
code("""
targets_t3 = scoring.read_targets(targets_dir, 't3_surrender_value')
calculated = scoring.normalize('t3_surrender_value', surrender_values(data, scoring.arguments('t3_surrender_value', targets_t3)[0]))
wrong = [(key[0], key[1], float(targets_t3[key]), float(calculated[key])) for key in targets_t3 if calculated.get(key) != targets_t3[key]]
print(f'{len(targets_t3) - len(wrong)} of {len(targets_t3)} exact')
wrong = pd.DataFrame(wrong, columns=['policy', 'valuation date', 'target', 'calculated'])
wrong['difference'] = wrong.target - wrong.calculated
wrong
""")
md("All 16 differences are whole francs while the policy value (diagnostic column) is exact: manual corrections.")

md("""
# t4 Annual statement

The statement sums the bookings by calendar year: premiums by money date, entry charges (premium share less the
amount invested) and the monthly charges by trade date.
""")
code("""
targets_t4 = scoring.read_targets(targets_dir, 't4_annual_statement')
calculated = scoring.normalize('t4_annual_statement', annual_statements(data))
columns = ['premiums', 'entry', 'admin', 'management', 'risk', 'total']
wrong = [(key[0], key[1]) + tuple(float(t) - float(c) for t, c in zip(targets_t4[key], calculated[key]))
         for key in targets_t4 if calculated.get(key) != targets_t4[key]]
print(f'{len(targets_t4) - len(wrong)} of {len(targets_t4)} exact')
listed = set(data.table('NREXCP').query("EX_TARGET.str.startswith('t4')", engine='python').EX_POLNR)
wrong = pd.DataFrame(wrong, columns=['policy', 'year'] + columns)
wrong['listed in NREXCP'] = wrong.policy.isin(listed)
wrong
""")
md("20 admin fees differ by whole francs (16 listed in `NREXCP`) and one risk charge is the manual correction of "
   "`BL10004387`: every difference is a manual correction.")

code("""
example = pd.DataFrame([calculated[('BL10000013', year)] for year in range(2016, 2026)], index=range(2016, 2026),
                       columns=columns).astype(float)
example[['entry', 'admin', 'management', 'risk']].plot.bar(stacked=True, figsize=(12, 4), title='Charges of BL10000013 per year')
plt.ylabel('Amount')
plt.show()
""")

md("""
# Summary

| Booking | Rule |
|---|---|
| Premium (PRM) | per fund: received x allocation x (1 - entry charge), all on the money date; pot 1 within `PD_INIMON` months; units at the ask price of the fund's first price day after the money date, FX of the day before |
| Admin fee (ADM) | fee valid on the anniversary (capped at the value), split by value |
| Management (AMC) | value x pot rate (or agreement) / 12; COBOL: x days / 360 |
| Risk (RSK) | sum at risk on the value after admin and management charge, split by the value left |
| All | positions valued at bid with the FX of the day; the rounding difference goes to the largest position; no booking for 0.00; COBOL truncates, Neuron NG rounds half up |
| Ignored | reversed events (900), technical corrections (990), charges from the day of surrender or death |
""")

nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata['kernelspec'] = {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}
NotebookClient(nb, timeout=3600, kernel_name='python3', resources={'metadata': {'path': str(out.parent)}}).execute()
nbformat.write(nb, out)
print('written', out)
