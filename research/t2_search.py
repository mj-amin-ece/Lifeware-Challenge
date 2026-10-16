"""Exploration: search the projection conventions that reproduce the t2 year values exactly."""
import itertools
import pathlib
import sys
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
from dateutil.relativedelta import relativedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'starter_kit' / 'my_solution'))
from legacy_loader import LegacyData

D = LegacyData(cache_dir=pathlib.Path(__file__).resolve().parents[1] / '.cache')
T = str(pathlib.Path(__file__).resolve().parents[1] / 'targets') + '/'
CENT = Decimal('0.01')


def r2(x):
    return Decimal(x).quantize(CENT, ROUND_HALF_UP) if not isinstance(x, Decimal) else x.quantize(CENT, ROUND_HALF_UP)


def dec(x, s=6):
    return Decimal(round(x * 10 ** s)).scaleb(-s)


def policies():
    mv = pd.read_csv(T + 't2_projected_maturity_value.csv')
    ph = D.table('NRPOLH')
    first = ph.sort_values('PH_VRSNR').drop_duplicates('PH_POLNR').set_index('PH_POLNR')
    rk1 = D.table('NRRISK').query('RK_RSKNR==1').set_index('RK_POLNR')
    br = D.table('NRBROK').set_index('BR_BRKNR')
    pers = D.table('NRPERS').set_index('PS_PERNR')
    pol = first.loc[mv.policy_id].join(rk1).join(pers[['PS_BIRTH', 'PS_SEX', 'PS_SMOKE']], on='RK_PERNR')
    pol['opt'] = pol.RK_TARKEY.str[6]
    pol['fam'] = pol.RK_TARKEY.str[:2]
    pol['gen'] = pol.RK_TARKEY.str[3:5]
    pol['sexb'] = pol.RK_TARKEY.str[2]
    pol['tier'] = pol.PH_BRKNR.map(br.BR_TIER)
    return pol


def param(table, prefix, date, **keys):
    t = D.table(table)
    m = (t[f'{prefix}_VLDFR'] <= date) & (date <= t[f'{prefix}_VLDTO'])
    for k, v in keys.items():
        m &= t[k] == v
    return t[m].iloc[0]


MORT = None


def qx(table, sex, age):
    global MORT
    if MORT is None:
        m = D.table('NRMORT')
        MORT = {(r.MO_TABID, r.MO_SEX, int(r.MO_AGE)): dec(r.MO_QX) for r in m.itertuples()}
    return MORT[(table, sex, min(age, 110))]


def age_on(birth, day, mode):
    years = relativedelta(day, birth).years
    if mode == 'last':
        return years
    # nearest birthday
    nxt = birth + relativedelta(years=years + 1)
    prev = birth + relativedelta(years=years)
    return years + 1 if (nxt - day) < (day - prev) else years


def project(p, opts, years=None):
    """Monthly projection with the switchable conventions in opts. Returns list of year-end values."""
    pdate = p.PH_APPDT if opts['pdate'] == 'app' else p.PH_BEGDT
    rate = dec(param('NRILLU', 'IL', pdate).IL_RATE)
    ch = param('NRCHRG', 'CG', pdate, CG_TARFAM=p.fam, CG_TARGEN=p.gen)
    entry = dec(param('NRENTC', 'EC', pdate, EC_TIER=p.tier).EC_RATE)
    admin = dec(ch.CG_ADMFEE, 2)
    amc1, amc2 = dec(ch.CG_AMCP1), dec(ch.CG_AMCP2)
    smk = dec(ch.CG_SMKFAC) if p.PS_SMOKE == 'J' else Decimal(1)
    load = Decimal(1) + dec(p.RK_LOAD)
    sex = p.PS_SEX if p.sexb == 'U' else {'M': '1', 'W': '2'}[p.sexb]
    si = dec(p.RK_SUMIN, 2)
    prem = dec(p.PH_PREMI, 2)
    freq = {'M': 1, 'Q': 3, 'H': 6, 'J': 12, 'E': 0}[p.PH_FREQ]
    inimon = {'FLKL': 24, 'FLFX': 12, 'FLSP': 0}[p.PH_PRDCD]
    begin, end = p.PH_BEGDT, p.PH_ENDDT
    months = (end.year - begin.year) * 12 + end.month - begin.month
    g = rate / 12 if opts['growth'] == 'r12' else Decimal(float((1 + rate) ** (Decimal(1) / 12)) - 1)
    v = Decimal(0)
    out = []
    rnd = (lambda x: r2(x)) if opts['round'] else (lambda x: x)
    for m in range(months):
        day = begin + relativedelta(months=m)
        if (freq and m % freq == 0) or (freq == 0 and m == 0):
            v += rnd(prem * (1 - entry)) if opts['entry_round'] else prem * (1 - entry)
        if opts['order'] == 'growth_first':
            v = rnd(v * (1 + g))
        amc = amc1 if m < inimon and opts['amc'] == 'pot1_initial' else amc2
        age_day = day if opts['age_at'] == 'month' else begin + relativedelta(years=m // 12)
        age = age_on(p.PS_BIRTH, age_day, opts['age'])
        q = qx(ch.CG_MORTTB, sex, age)
        sar = {'A': v * Decimal('0.01'), 'B': max(si - v, Decimal(0)), 'C': si}[p.opt]
        risk = rnd(sar * q * load * smk / 12)
        v = v - rnd(admin) - rnd(v * amc / 12) - risk
        if opts['order'] == 'charges_first':
            v = rnd(v * (1 + g))
        if (m + 1) % 12 == 0:
            out.append(r2(v))
            if years and len(out) >= years:
                break
    if months % 12:
        out.append(r2(v))
    return out


OPTIONS = {
    'pdate': ['app', 'beg'],
    'growth': ['r12', 'geo'],
    'order': ['charges_first', 'growth_first'],
    'round': [True, False],
    'entry_round': [True],
    'amc': ['pot1_initial'],
    'age_at': ['month', 'year'],
    'age': ['last', 'nearest'],
}

if __name__ == '__main__':
    pol = policies()
    py = pd.read_csv(T + 't2_projection_year.csv')
    target = py.groupby('policy_id').value.apply(lambda s: [Decimal(str(x)).quantize(CENT) for x in s])
    subset = pol[(pol.PH_PRDCD == sys.argv[1])].head(int(sys.argv[2])) if len(sys.argv) > 2 else pol.head(100)
    keys = list(OPTIONS)
    results = []
    for combo in itertools.product(*OPTIONS.values()):
        opts = dict(zip(keys, combo))
        ok_y1 = ok_all = 0
        for pid, p in subset.iterrows():
            v = project(p, opts, years=3)
            t = target[pid][:3]
            ok_y1 += v[0] == t[0]
            ok_all += v[:len(t)] == t
        results.append((ok_y1, ok_all, opts))
    for r in sorted(results, key=lambda r: -r[0])[:8]:
        print(r[0], r[1], r[2])
