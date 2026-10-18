"""Subgroup discovery on the t7 sample rows a version gets wrong.

    python research/t7_subgroups.py <dump.pkl of a version> <samples folder>

The dump holds (payout rows, annual rows) of a version, as written by t7_dump.py. Every sample row is described by
neutral features of the data (no target values), labelled wrong or right, and research/subgroup_discovery.py ranks
the groups where the version is wrong most often.
"""
import csv
import os
import pickle
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'starter_kit'))
sys.path.insert(0, os.path.join(ROOT, 'starter_kit', 'my_solution'))
sys.path.insert(0, os.path.join(ROOT, 'research'))
os.chdir(ROOT)
import scoring_t7  # noqa: E402
from subgroup_discovery import covering, discover  # noqa: E402
from submission import load  # noqa: E402
from tax_data import TaxData  # noqa: E402

KINDS = {400: 'withdrawal', 410: 'surrender', 500: 'death'}
TAXES = ['ch_stp', 'ch_vst', 'it_sos', 'it_bol', 'de_kst', 'de_sol', 'de_kis']


def features(module, samples, predictions):
    """One row per sample value: neutral features and whether the prediction was wrong."""
    payouts = {(policy, p[0]): (p, i) for policy, ps in module.payouts().items() for i, p in enumerate(ps)}
    years = {}
    for (policy, event), (payout, _) in payouts.items():
        kind = KINDS[int(module.event_types[(policy, event)])]
        years.setdefault((policy, payout[1].year), set()).add(kind)
    fixed = {row.TB_POLNR for row in module.bookings.itertuples() if row.TB_USRID == 'TAXFIX19'}
    rows = []
    for name in ('sample_1', 'sample_2'):
        for task in scoring_t7.TASKS:
            targets = scoring_t7.read_targets(os.path.join(samples, name), task)
            predicted = scoring_t7.normalize(task, predictions[task])
            for key, target in targets.items():
                policy = key[0]
                row = {'wrong': predicted.get(key) != target, 'currency': module.policies[policy].PH_CCY,
                       'TAXFIX19 policy': policy in fixed}
                if task == 't7_tax_payout':
                    payout, position = payouts[key]
                    row.update({'table': 'payout', 'country': target[0], 'year': payout[1].year,
                                'era': 'COBOL' if payout[1] < module.conversion else 'NG',
                                'event': KINDS[int(module.event_types[key])], 'tax withheld': target[2] != 0,
                                'duty collected': target[4] != 0, 'later payout': position > 0})
                else:
                    present = [tax for tax, value in zip(TAXES, target) if value != 0]
                    events = years.get(key, set())
                    row.update({'table': 'annual', 'country': present[0][:2].upper(), 'year': key[1],
                                'era': 'COBOL' if key[1] < module.conversion.year else 'NG',
                                'taxes': '+'.join(present), 'payout in year': bool(events),
                                'surrender or death in year': bool(events & {'surrender', 'death'})})
                rows.append(row)
    return pd.DataFrame(rows)


def main():
    payout, annual = pickle.load(open(sys.argv[1], 'rb'))
    module = TaxData(load(os.path.join(ROOT, 'legacy')))
    table = features(module, sys.argv[2], {'t7_tax_payout': payout, 't7_tax_annual': annual})
    columns = [c for c in table.columns if c != 'wrong']
    print(f'{len(table)} sample rows, {int(table.wrong.sum())} wrong ({table.wrong.mean():.0%})\n')
    with pd.option_context('display.width', 160, 'display.max_colwidth', 70):
        print(discover(table, 'wrong', columns, depth=2, top=10).to_string(index=False))
    print('\nSequential covering (one cause per round):')
    for round_, subgroup, rows, wrong, rate in covering(table, 'wrong', columns):
        print(f'  {round_}. {subgroup}: {wrong} of {rows} rows wrong ({rate:.0%})')
    print(f'  rows wrong overall: {int(table.wrong.sum())}')


if __name__ == '__main__':
    main()
