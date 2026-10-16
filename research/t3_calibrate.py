"""Exploration: predict every charge booking of the train policies from the holdings before it (teacher forcing).

The holdings come from the target units of the earlier bookings, so a wrong booking does not spoil the next ones and
every formula can be checked on its own.
"""
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'starter_kit' / 'my_solution'))
from legacy_loader import LegacyData  # noqa: E402

D = LegacyData(cache_dir=ROOT / '.cache')
CONVERSION = pd.Timestamp('2007-08-11')


def latest_prices():
    fp = D.table('NRFPRC').sort_values('FP_CHGTS').drop_duplicates(['FP_FNDID', 'FP_PRCDT'], keep='last')
    return fp.set_index(['FP_FNDID', 'FP_PRCDT'])


def fx_rates():
    """CHF per unit of each currency on every day (last rate on or before the day)."""
    fx = D.table('NRFXRT').assign(FX_CCY=lambda t: t.FX_CCY.str.upper())
    fx = fx.pivot(index='FX_RATDT', columns='FX_CCY', values='FX_RATE')
    days = pd.date_range(fx.index.min(), '2026-12-31')
    return fx.reindex(days).ffill()


def bookings_with_targets():
    tb = pd.read_parquet(ROOT / '.cache' / 't3_booking.parquet').set_index('booking_id')
    train = set(tb.policy_id)
    bk = D.table('NRBOOK')
    bk = bk[bk.BK_POLNR.isin(train)].copy()
    ev = D.table('NREVNT')
    reversed_events = set(zip(ev[ev.EV_EVTTP == 900].EV_POLNR, ev[ev.EV_EVTTP == 900].EV_REVNR))
    corrections = set(zip(ev[ev.EV_EVTTP == 990].EV_POLNR, ev[ev.EV_EVTTP == 990].EV_EVTNR))
    ignored = reversed_events | corrections
    bk = bk[[(p, e) not in ignored for p, e in zip(bk.BK_POLNR, bk.BK_EVTNR)]]
    bk['units'] = bk.BK_BOOKID.map(tb.units).fillna(bk.BK_UNITS)
    bk['amount'] = bk.BK_BOOKID.map(tb.amount_pc).fillna(bk.BK_AMTPC)
    bk['price'] = bk.BK_BOOKID.map(tb.price).fillna(bk.BK_PRICE)
    bk = bk.sort_values('BK_BOOKID')
    bk['cum'] = bk.groupby(['BK_POLNR', 'BK_FNDID', 'BK_POTCD']).units.cumsum()
    bk['hold_before'] = bk.cum - bk.units
    return bk


def charge_events(bk):
    """One row per charge event, fund and pot, with the holding before the event and its value."""
    charges = bk[bk.BK_BKTYP.isin(['ADM', 'AMC', 'RSK'])]
    pos = charges.groupby(['BK_POLNR', 'BK_EVTNR', 'BK_FNDID', 'BK_POTCD']).agg(
        trade=('BK_TRDDT', 'first'), pricedate=('BK_PRCDT', 'first')).reset_index()
    # The charge run at 01:30 sees only the units traded before the charge day
    daily = bk.groupby(['BK_POLNR', 'BK_FNDID', 'BK_POTCD', 'BK_TRDDT']).units.sum().groupby(
        level=[0, 1, 2]).cumsum().rename('hold').reset_index().sort_values('BK_TRDDT')
    pos = pd.merge_asof(pos.sort_values('trade'), daily, left_on='trade', right_on='BK_TRDDT',
                        by=['BK_POLNR', 'BK_FNDID', 'BK_POTCD'], allow_exact_matches=False).drop(columns='BK_TRDDT')
    pos['hold'] = pos.hold.fillna(0)
    prices = latest_prices()
    pos['bid'] = prices.FP_BIDPR.reindex(list(zip(pos.BK_FNDID, pos.pricedate))).values
    fund_ccy = D.table('NRFUND').set_index('FD_FNDID').FD_CCY
    pol_ccy = D.table('NRPOLH').drop_duplicates('PH_POLNR').set_index('PH_POLNR').PH_CCY
    rates = fx_rates()
    # Fund currency per policy currency, unrounded, on the trade date
    pos['fx'] = [rates.at[day, pc] / rates.at[day, fc] for day, pc, fc in
                 zip(pos.trade, pos.BK_POLNR.map(pol_ccy), pos.BK_FNDID.map(fund_ccy))]
    cobol = pos.trade < CONVERSION
    exact = pos.hold * pos.bid / pos.fx
    pos['value'] = np.where(cobol, np.floor(exact * 100 + 1e-9), np.floor(exact * 100 + 0.5 + 1e-9)) / 100
    pos['cobol'] = cobol
    return pos


if __name__ == '__main__':
    bk = bookings_with_targets()
    pos = charge_events(bk)
    pos.to_pickle(ROOT / 'research' / 't3_positions.pkl')
    bk.to_pickle(ROOT / 'research' / 't3_bookings.pkl')
    print(len(pos), 'positions')
