"""Build and execute starter_kit/my_solution/notebooks/07_Task_t7_Without_Targets.ipynb."""
import pathlib
import sys

import nbformat
from nbclient import NotebookClient

out = pathlib.Path(sys.argv[1])
cells = []
md = lambda s: cells.append(nbformat.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbformat.v4.new_code_cell(s.strip()))

md("""
# Neuron Migration - t7 (tax audit) without target values

For the surprise task t7 we had no target values at all. The same method still works, with three other sources of
evidence instead of targets:

1. **Weak labels**: Neuron's tax bookings (NRTAXB) say *which* tax was booked for which payout and year, only the
   amounts are missing. A candidate rule must book exactly the same taxes (`tools/weak_labels.py`).
2. **The two examples of the task text**: a convention search over the open questions must reproduce them to the cent
   (`tools/convention_search.py`).
3. **Consistency**: every tax Neuron booked must get an amount.
""")

md("# Import libraries")
code("""
import sys
import datetime as dt
import pandas as pd
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

sys.path.insert(0, '..')
from rules import load, CENT
from taxes import TaxModule, tax_results
from stamp_duty import stamp_duty
from tools.weak_labels import agreement, share_agreeing, explain_disagreement
from tools.convention_search import search

pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 30)
""")

md("# Hyperparameters")
code("""
legacy_dir = '../../../legacy'

data = load(legacy_dir)

module = TaxModule(data)
""")

md("""
# 1 Weak labels: which taxes did Neuron book?

Every payout (withdrawal, surrender, death benefit) with the residence of its policyholder and the taxes Neuron booked
for it.
""")
code("""
cases = []
for policy, payouts in module.payouts().items():
    withdrawals = []
    for payout in payouts:
        event, day, _, amount, share = payout
        address = module.residence.address(policy, day)
        country = address.AD_CNTRY
        terms = module.policies[policy]
        cases.append({
            'policy': policy, 'event': event, 'day': day, 'country': country, 'objection': address.AD_TAXST == 'E',
            'church': address.AD_CHURCH == 'J',
            'payout_chf': float(module.convert(amount, policy, 'CH', day)),
            'gain': float(module.gain(policy, payout, withdrawals, country)) if country in ('DE', 'IT') else None,
            'years_held': relativedelta(day, terms.PH_BEGDT.date()).years, 'applied': terms.PH_APPDT,
            'taxes': '+'.join(sorted(module.booked[(policy, event)])) or '-'})
        withdrawals.append((day, share))
cases = pd.DataFrame(cases)
events = data.table('NREVNT').set_index(['EV_POLNR', 'EV_EVTNR']).EV_EVTTP
cases['death'] = [events[(p, e)] == 500 for p, e in zip(cases.policy, cases.event)]
pd.crosstab(cases.country, cases.taxes)
""")
md("""
Each country has its own taxes: VST only in Switzerland, SOS in Italy, KST/SOL/KIS in Germany, nothing in
Luxembourg. The Italian stamp duty (BOC) is also collected from holders who moved away from Italy.
""")

md("## Swiss withholding tax: objection to reporting and a threshold")
code("""
swiss = cases[cases.country == 'CH']
rule = swiss.objection & (swiss.payout_chf > 5000)
booked = swiss.taxes.str.contains('VST')
print('agreement:', round(share_agreeing(rule, booked), 4))
agreement(rule, booked)
""")
md("VST is withheld when the holder objected to the reporting (status E) and the payout is above CHF 5,000.")

md("## Taxes on the gain: Italy and Germany")
code("""
for country, tax in [('IT', 'SOS'), ('DE', 'KST')]:
    part = cases[(cases.country == country) & cases.gain.notna()]
    print(country, tax, 'agreement of \\"gain > 0\\" with the bookings:', round(share_agreeing(part.gain > 0, part.taxes.str.contains(tax)), 3))
""")
code("""
german = cases[(cases.country == 'DE') & cases.gain.notna()].copy()
german['APPLIED'] = german.applied
german['YEARS_HELD'] = german.years_held
german['DEATH'] = german.death
rules = explain_disagreement(german[['APPLIED', 'YEARS_HELD', 'DEATH']], german.gain > 0, german.taxes.str.contains('KST'))
""")
md("""
Where a German gain was not taxed, the tree points to contracts applied for before 2005 and paid out after 12 years or
more (the old German rule for life insurance) and to death benefits. The solution does not need to re-implement these
exemptions: it takes *which* taxes apply from Neuron's bookings and calculates their amounts.
""")

md("""
# 2 The examples of the task text

## German taxable base: BL10000086, surrender of 2006-07-17 (5,628.16)
Open questions: on which day are the premiums converted into EUR, and how are the converted amounts rounded?
""")
code("""
policy, event = 'BL10000086', 121
payout = next(p for p in module.payouts()[policy] if p[0] == event)
premiums = module.premiums[policy]
paid = data.table('NRPREM').query('PR_POLNR == @policy and PR_STATE == "P"').set_index('PR_EVTNR').PR_DUEDT
rate = lambda day: module.market.rate('USD', day) / module.market.rate('EUR', day)

def german_base(choice):
    mode = {'cut off': ROUND_DOWN, 'half up': ROUND_HALF_UP}[choice['rounding']]
    day_of = {'money received': lambda day, number: day, 'due date': lambda day, number: paid[number].date()}[choice['premium day']]
    basis = sum((amount * rate(day_of(day, number))).quantize(CENT, mode) for day, amount, number in premiums if day <= payout[1])
    return int((payout[3] * rate(payout[1])).quantize(CENT, mode) - basis == Decimal('5628.16'))

search({'premium day': ['money received', 'due date'], 'rounding': ['cut off', 'half up']}, german_base)
""")
md("Only premiums converted on the day the money was received, cut off to the cent (COBOL era), give 5,628.16.")

md("""
## Italian stamp duty: BL10000044, 2019 (616.11)
Open questions: which exchange rate converts the policy value, and how is the rate correction of July 2019 booked?
""")
code("""
policy = 'BL10000044'
values = {year: module.policy_value(policy, dt.date(year, 12, 31)) for year in [2017, 2018, 2019]}
to_eur = lambda value, day: value * module.market.rate('CHF', day) / module.market.rate('EUR', day)
fix_day = dt.date(2019, 7, 20)

def stamp_duty_2019(choice):
    day_of = (lambda year: dt.date(year, 12, 31)) if choice['conversion'] == '31 December' else (lambda year: fix_day)
    duty = lambda year, rate: (to_eur(values[year], day_of(year)) * rate).quantize(CENT, ROUND_HALF_UP)
    if choice['correction'] == 'new booking - old booking':
        fix = sum(duty(year, Decimal('0.002')) - duty(year, Decimal('0.0015')) for year in [2017, 2018])
    else:
        fix = sum(duty(year, Decimal('0.0005')) for year in [2017, 2018])
    return int(duty(2019, Decimal('0.002')) + fix == Decimal('616.11'))

search({'conversion': ['31 December', 'booking day'], 'correction': ['new booking - old booking', 'rate difference']},
       stamp_duty_2019)
""")
md("""
The policy value of 31 December converted with the rate of that day, and the correction booked as the new booking
minus the original one (both rounded): Neuron re-booked the years 2017 and 2018 when the rate was corrected in 2019.

# 3 The solution on the examples and the consistency check
""")
code("""
payout_rows, annual_rows = tax_results(data)
print('BL10000086, 121:', payout_rows[('BL10000086', 121)])
print('BL10000044, 2019:', annual_rows[('BL10000044', 2019)])
""")
code("""
withheld = {'VST': 2, 'SOS': 2, 'KST': 2, 'BOC': 4}
bookings = data.table('NRTAXB')
check = []
for row in bookings[bookings.TB_TAXTP.isin(list(withheld))].itertuples():
    result = payout_rows.get((row.TB_POLNR, row.TB_EVTNR))
    if result is not None:
        check.append({'tax': row.TB_TAXTP, 'amount calculated': result[withheld[row.TB_TAXTP]] > 0})
check = pd.DataFrame(check)
pd.crosstab(check.tax, check['amount calculated'])
""")
md("""
Every tax that Neuron booked for a payout gets an amount.

# What is not confirmed yet

Without targets, these parts follow the law and the data structure but could not be checked to the cent:
- the remittance dates of Switzerland (30 days after the end of the month) and Italy (16th of the next month); the
  German one (10th of the next month) matches the example;
- the share of the year in the stamp duty booked at a payout (days / 365);
- the German partial exemption (from 2018) and half-income rule, which apply only to recent payouts;
- whether payouts without withholding still report a base: the next organizer evaluation tests reporting the Swiss
  payout amount or the nonnegative Italian/German gain, with the existing German adjustments, even without withholding.

As soon as the organisers' actuary returns values for a few policies, the same tools (residuals, convention search)
will settle these points.
""")

nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata['kernelspec'] = {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}
NotebookClient(nb, timeout=3600, kernel_name='python3', resources={'metadata': {'path': str(out.parent)}}).execute()
nbformat.write(nb, out)
print('written', out)
