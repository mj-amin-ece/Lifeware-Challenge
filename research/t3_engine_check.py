"""Exploration: run the accounting engine on a sample of train policies and compare with NRBOOK and the targets.

    python t3_engine_check.py 200
"""
import pathlib
import sys
import time

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'starter_kit' / 'my_solution'))
from accounting import all_bookings, ignored_events  # noqa: E402
from legacy_loader import LegacyData  # noqa: E402

POLICY_COLUMNS = {'NRPOLH': 'PH_POLNR', 'NRRISK': 'RK_POLNR', 'NRALLO': 'AL_POLNR', 'NRAGRE': 'AG_POLNR',
                  'NRPREM': 'PR_POLNR', 'NREVNT': 'EV_POLNR', 'NRBOOK': 'BK_POLNR', 'NRHOLD': 'HD_POLNR'}


def sample_data(n, seed=1, policies=()):
    """LegacyData restricted to n random train policies plus `policies` (the conversion event is kept)."""
    data = LegacyData(ROOT / 'legacy', cache_dir=ROOT / '.cache')
    train = pd.read_csv(ROOT / 'targets' / 't2_projected_maturity_value.csv').policy_id
    chosen = set(train.sample(n, random_state=seed)) | set(policies)
    for name, column in POLICY_COLUMNS.items():
        table = data.table(name)
        keep = table[column].isin(chosen)
        if name == 'NREVNT':
            keep |= table.EV_EVTTP == 800
        data.tables[name] = table[keep]
    return data, chosen


def compare(bookings, data):
    """Join the calculated charge and premium bookings with NRBOOK and the target amounts and units."""
    tb = pd.read_parquet(ROOT / '.cache' / 't3_booking.parquet').set_index('booking_id')
    bk = data.table('NRBOOK')
    ignored = ignored_events(data)
    bk = bk[[(p, e) not in ignored for p, e in zip(bk.BK_POLNR, bk.BK_EVTNR)]]
    bk = bk[bk.BK_BKTYP.isin(['PRM', 'ADM', 'AMC', 'RSK'])]
    target = pd.DataFrame({'policy': bk.BK_POLNR, 'type': bk.BK_BKTYP, 'fund': bk.BK_FNDID, 'pot': bk.BK_POTCD,
                           'trade': [d.date() for d in bk.BK_TRDDT], 'money_date': [d.date() if pd.notna(d) else None for d in bk.BK_RCVDT],
                           't_amount': bk.BK_BOOKID.map(tb.amount_pc).values, 't_units': bk.BK_BOOKID.map(tb.units).values})
    calc = bookings[bookings.type.isin(['PRM', 'ADM', 'AMC', 'RSK'])].copy()
    calc['amount'] = calc.amount.astype(float)
    calc['units'] = calc.units.astype(float)
    keys = ['policy', 'type', 'fund', 'pot', 'trade']
    target['n'] = target.groupby(keys).cumcount()
    calc['n'] = calc.groupby(keys).cumcount()
    merged = calc.merge(target.drop(columns='money_date'), on=keys + ['n'], how='outer', indicator=True)
    merged['ok'] = (merged._merge == 'both') & np.isclose(merged.amount, merged.t_amount, rtol=0, atol=0.001) & np.isclose(merged.units, merged.t_units, atol=1e-9, rtol=0)
    return merged


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    data, chosen = sample_data(n)
    started = time.time()
    bookings = all_bookings(data, pd.Timestamp('2026-06-30').date())
    print(f'{len(bookings)} bookings of {n} policies in {time.time() - started:.1f}s')
    merged = compare(bookings, data)
    print(pd.crosstab(merged.type, merged._merge))
    print('exact by type:', merged.groupby('type').ok.mean().round(5).to_dict())
    first_bad = merged[~merged.ok].sort_values('trade').groupby('policy').head(1)
    print(first_bad[['policy', 'type', 'fund', 'pot', 'trade', 'amount', 't_amount', 'units', 't_units', '_merge']].head(20).to_string())
    merged.to_pickle(ROOT / 'research' / 't3_engine_check.pkl')
