"""Build and execute starter_kit/my_solution/notebooks/06_Generic_Toolkit.ipynb."""
import pathlib
import sys

import nbformat
from nbclient import NotebookClient

out = pathlib.Path(sys.argv[1])
cells = []
md = lambda s: cells.append(nbformat.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbformat.v4.new_code_cell(s.strip()))

md("""
# Neuron Migration - The generic toolkit

Our method is one loop for every target: write the simplest rule, mark the values it gets wrong, ask the tools *why*,
turn the answer into code. None of the tools below knows anything about insurance; each answers one question that
comes up in every legacy migration. This notebook shows each tool rediscovering, on its own, a rule we found in t0-t4.

| Question | Tool | Rule it rediscovers here |
|---|---|---|
| When did the system change its behaviour? | `tools/change_points.py` | the COBOL -> Java conversion in August 2007 |
| What do the differences say? | `tools/residuals.py` | COBOL charged by the day (days / 360) and cut off the cents; whole-franc differences are manual corrections |
| Which convention is it? | `tools/convention_search.py` | the order of the charges in the offer; Actual/360 with cut-off rounding |
| Which days are holidays? | `business_calendar.py` | the public holidays of Ticino, learned from the price days |
| Under which conditions is a rule wrong? | `tools/rule_finder.py` | see notebooks 02 and 03 |
""")

md("# Import libraries")
code("""
import sys
import itertools
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

sys.path.insert(0, '..')
sys.path.insert(0, '../../../research')
from rules import load, conversion_date, CENT
from projection import maturity_values
from business_calendar import calendar
from charges import ChargeRun
from market import Market
from policies import policy_base
from tools.change_points import change_points
from tools.residuals import implied_ratios, rounding_modes, classify_differences, ROUNDING_MODES
from tools.convention_search import search, CANDIDATES
import t2_search
import t3_calibrate
""")

md("# Hyperparameters")
code("""
legacy_dir = '../../../legacy'

targets_dir = '../../../targets'

sample_offers = 800

sample_charges = 4000

data = load(legacy_dir)
""")

md("""
# 1 When did the behaviour change?

We calculate the offers (t2) with the Neuron NG conventions for every year and mark the wrong ones. The change-point
finder only gets the application dates and the flags.
""")
code("""
offers = t2_search.policies().sample(sample_offers, random_state=3)
years = pd.read_csv(f'{targets_dir}/t2_projection_year.csv')
target_years = years.groupby('policy_id').value.apply(lambda values: [Decimal(str(v)).quantize(CENT) for v in values])
neuron_ng = {'pdate': 'app', 'growth': 'r12', 'order': 'charges_first', 'round': True, 'entry_round': True,
             'amc': 'pot2', 'age_at': 'year', 'age': 'nearest6', 'era': False, 'seq': ('adm', 'amc', 'rsk')}
wrong = [t2_search.project(offer, neuron_ng, years=2) != target_years[pid][:2] for pid, offer in offers.iterrows()]

print('conversion event in the data:', conversion_date(data).date())
change_points(offers.PH_APPDT, wrong)
""")
md("The best split falls between 2007-08-02 and 2007-08-24 and explains every offer: the conversion of 2007-08-11.")

md("""
# 2 What do the differences say?

## Implied ratios
The monthly management charges of the COBOL era, calculated the Neuron NG way (value x rate / 12), against Neuron's
amounts. The holdings before each charge come from the diagnostic bookings (`research/t3_calibrate.py`), so only the
charge formula is tested.
""")
code("""
bookings = t3_calibrate.bookings_with_targets()
positions = t3_calibrate.charge_events(bookings)
amc = bookings[bookings.BK_BKTYP == 'AMC'][['BK_POLNR', 'BK_EVTNR', 'BK_FNDID', 'BK_POTCD', 'amount']]
positions = positions.merge(amc, on=['BK_POLNR', 'BK_EVTNR', 'BK_FNDID', 'BK_POTCD'])
cobol = positions[positions.cobol].sample(sample_charges, random_state=1)

# Management charge rate of each position (pot rate or agreement), from the solution's charge run
policies = {policy.PH_POLNR: policy for policy in policy_base(data).itertuples()}
run = ChargeRun(data, Market(data), conversion_date(data).date())
def rate(row):
    policy, day = policies[row.BK_POLNR], row.trade.date()
    return run.management_rate(policy, row.BK_POTCD, run.tariff(policy, day), day)
cobol['rate'] = [rate(row) for row in cobol.itertuples()]
cobol['value_exact'] = [Decimal(str(value)).quantize(CENT) for value in cobol.value]
cobol['target'] = [Decimal(str(amount)).quantize(CENT) for amount in cobol.amount]

ng_charges = [(value * rate / 12).quantize(CENT, ROUND_HALF_UP) for value, rate in zip(cobol.value_exact, cobol.rate)]
implied_ratios(ng_charges, cobol.target, top=6)
""")
md("The ratios cluster at 31/360 x 12 and 28/360 x 12: COBOL charged the management fee by the actual days / 360.")

md("## Rounding mode")
code("""
months = [(row.trade.date() - relativedelta(months=1), row.trade.date()) for row in cobol.itertuples()]
cobol['previous'] = [policies[row.BK_POLNR].PH_BEGDT.date() + relativedelta(
    months=(row.trade.year - policies[row.BK_POLNR].PH_BEGDT.year) * 12 + row.trade.month - policies[row.BK_POLNR].PH_BEGDT.month - 1)
    for row in cobol.itertuples()]
exact = [value * rate * Decimal((day.date() - previous).days) / 360
         for value, rate, day, previous in zip(cobol.value_exact, cobol.rate, cobol.trade, cobol.previous)]
rounding_modes(exact, cobol.target)
""")
md("With the day count found, only cutting off the cents reproduces the COBOL amounts.")

md("## Differences that follow no rule")
code("""
maturity = pd.read_csv(f'{targets_dir}/t2_projected_maturity_value.csv')
calculated = maturity_values(data)
classify_differences([calculated[policy] for policy in maturity.policy_id],
                     [Decimal(str(value)).quantize(CENT) for value in maturity.maturity_value])
""")
md("Every value is exact except 8 that differ by whole francs: the manual corrections of t2 (task t5).")

md("""
# 3 Which convention is it?

## The order of the charges in the offer
Every order of admin fee, management charge and risk charge, with growth before or after the charges, on 40 offers.
""")
code("""
single_premium = t2_search.policies().query("PH_PRDCD == 'FLSP'").head(40)
fixed = {key: [value] for key, value in neuron_ng.items() if key not in ('order', 'seq')} | {'era': [True]}
options = fixed | {'order': ['charges_first', 'growth_first'], 'seq': list(itertools.permutations(['adm', 'amc', 'rsk']))}
ranking = search(options, lambda choice: [t2_search.project(offer, choice, years=3) == target_years[pid][:3]
                                          for pid, offer in single_premium.iterrows()], top=5)
ranking[['order', 'seq', 'exact']]
""")

md("## Day count and rounding from the standard candidates")
code("""
def management_charges(choice):
    mode = ROUNDING_MODES[choice['rounding']]
    return [(value * rate * choice['day count'](previous, day.date())).quantize(CENT, mode) == target
            for value, rate, previous, day, target in zip(cobol.value_exact, cobol.rate, cobol.previous, cobol.trade, cobol.target)]

search({'day count': CANDIDATES['day count'], 'rounding': CANDIDATES['rounding']}, management_charges, top=5)
""")
md("Out of 12 standard combinations, Actual/360 with cut-off rounding reproduces the COBOL management charges.")

md("""
# 4 Which days are holidays?

The business calendar learns its holidays from the days without fund prices: fixed dates and days after Easter that
never have a price. Nothing about Ticino is written in the code.
""")
code("""
business_days = calendar(data)
print('fixed dates:', business_days.fixed)
print('days after Easter Sunday:', business_days.after_easter)
print('holidays 2027:', sorted(business_days.holidays(2027)))
""")
md("""
The learned rules are the public holidays of Ticino (Epiphany, St Joseph, St Peter and Paul, ... Easter Monday,
Ascension, Whit Monday, Corpus Christi). For another country's data the same code would learn that country's calendar.

# Summary

Each step of our discoveries can be repeated by a tool that knows nothing about insurance. For a new target the loop
is the same: calculate a first version, then ask `change_points` *when* it breaks, `rule_finder` *where*,
`residuals` *how*, and let `convention_search` decide between the candidate rules.
""")

nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata['kernelspec'] = {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}
NotebookClient(nb, timeout=3600, kernel_name='python3', resources={'metadata': {'path': str(out.parent)}}).execute()
nbformat.write(nb, out)
print('written', out)
