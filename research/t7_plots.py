"""Presentation plots for t7: rule timeline, score progression, payout mix, the Italian rate split, sample coverage.

    python research/t7_plots.py [samples folder]     writes presentation/plots/t7_*.png
"""
import collections
import csv
import datetime as dt
import os
import sys
from decimal import Decimal

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'starter_kit', 'my_solution'))
os.chdir(ROOT)
import payout_taxes  # noqa: E402
captured = []


class Capture(payout_taxes.TaxModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        captured.append(self)


import taxes  # noqa: E402
taxes.TaxModule = Capture
from submission import load  # noqa: E402

OUT = os.path.join(ROOT, 'presentation', 'plots')
COLORS = {'CH': '#d62728', 'IT': '#2ca02c', 'DE': '#1f77b4', 'LU': '#9467bd'}
CONVERSION = dt.date(2007, 8, 11)
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})


def rule_timeline(module):
    """Every tax rate Neuron knew, as a step line per tax, with the system eras and the 2019 correction."""
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
    panels = {'CH': ['VST', 'STP'], 'IT': ['SOS', 'BOL'], 'DE': ['KST', 'SOL', 'KIS', 'TFS', 'HEV']}
    for ax, (country, kinds) in zip(axes, panels.items()):
        for kind in kinds:
            for row in sorted(module.rates.rows[(country, kind)], key=lambda r: (r[3], r[1])):
                region, start, end, version = row[0], row[1], min(row[2], dt.date(2026, 12, 31)), row[3]
                label = f'{kind}{" " + region if region else ""}{" v" + str(version) if version > 1 else ""}'
                ax.plot([start, end], [float(row[5]) * 100] * 2, lw=3 if version == 1 else 2,
                        ls='-' if version == 1 else '--', label=label)
        ax.axvline(CONVERSION, color='k', ls=':', lw=1)
        ax.set_ylabel(f'{country} rate %')
        ax.set_yscale('symlog', linthresh=1)
        handles, labels = ax.get_legend_handles_labels()
        unique = dict(zip(labels, handles))
        ax.legend(unique.values(), unique.keys(), ncol=6, fontsize=9, loc='upper left')
    axes[0].text(CONVERSION, axes[0].get_ylim()[1] * 0.6, '  COBOL -> Neuron NG', fontsize=9)
    axes[1].axvline(dt.date(2019, 7, 20), color='#ff7f0e', ls=':', lw=1)
    axes[1].text(dt.date(2019, 7, 20), 0.3, ' TAXFIX19:\n 0.15 % -> 0.2 %', fontsize=9, color='#ff7f0e')
    axes[0].set_title("Neuron's tax rules over time (NRTAXR): every rate change is a rule change")
    fig.tight_layout()
    fig.savefig(f'{OUT}/t7_rule_timeline.png', dpi=140)


def score_progression():
    """t7 leaderboard results of every upload, and what the published samples showed locally."""
    uploads = [('e8', 0, 11), ('s-simple', 0, 8), ('c3', 1, 9), ('c4', 0, 11), ('c6', 1, 11), ('m1', 1, 11),
               ('m3', 2, 12), ('m6', 10, 29), ('m7', 10, 29), ('m9', 10, 29)]
    names = [u[0] for u in uploads]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(names, [u[1] / 40 * 100 for u in uploads], 'o-', lw=2.5, label='t7 payout (leaderboard, of 40)')
    ax.plot(names, [u[2] / 30 * 100 for u in uploads], 's-', lw=2.5, label='t7 annual (leaderboard, of 30)')
    ax.axhline(100, color='grey', ls='--', lw=1)
    ax.text(len(names) - 1, 101.5, 'm6+ on the published samples: payout 40/40, annual 30/30', ha='right', fontsize=9)
    ax.axvspan(6.5, 9.5, color='#2ca02c', alpha=0.08)
    ax.text(7, 60, 'rules fitted on the\norganisers\' samples', fontsize=10, color='#2ca02c')
    ax.set_ylabel('exact rows %')
    ax.set_ylim(-3, 108)
    ax.set_title('t7 accuracy per upload: guessing from the law vs fitting the published samples')
    ax.legend(loc='center left')
    fig.tight_layout()
    fig.savefig(f'{OUT}/t7_score_progression.png', dpi=140)


def payout_mix(module, rows):
    """Payouts per year by country and by whether a tax was withheld: how the population shifts over time."""
    counts = collections.Counter()
    for (policy, event), row in rows.items():
        day = next(p[1] for p in module.payouts()[policy] if p[0] == event)
        counts[(day.year, row[0], 'withheld' if row[2] else 'nothing withheld')] += 1
    table = pd.Series(counts).unstack([1, 2]).fillna(0).sort_index()
    fig, ax = plt.subplots(figsize=(13, 5.5))
    bottom = pd.Series(0, index=table.index, dtype=float)
    for country in ['CH', 'IT', 'DE', 'LU']:
        for state, alpha in (('withheld', 1.0), ('nothing withheld', 0.35)):
            if (country, state) in table:
                values = table[(country, state)]
                ax.bar(table.index, values, bottom=bottom, color=COLORS[country], alpha=alpha,
                       label=f'{country} {state}')
                bottom += values
    ax.axvline(CONVERSION.year + 0.6, color='k', ls=':', lw=1)
    ax.text(CONVERSION.year + 0.7, bottom.max() * 0.9, 'Neuron NG', fontsize=9)
    ax.set_title('Payouts per year by residence and tax withheld (2,493 payouts)')
    ax.set_ylabel('payouts')
    ax.legend(ncol=4, fontsize=9, loc='upper left')
    fig.tight_layout()
    fig.savefig(f'{OUT}/t7_payout_mix.png', dpi=140)


def italian_split(module, policy='BL10001596', event=178):
    """One real payout: the gain accrued in each Italian rate period, and the tax it gives."""
    payout = next(p for p in module.payouts()[policy] if p[0] == event)
    _, day, known, _, share = payout
    begin = module.policies[policy].PH_BEGDT.date()
    days = pd.date_range(begin, day, freq='QE').date.tolist() + [day]
    values = [float(module.convert(module.policy_value(policy, d), policy, 'IT', d)) for d in days]
    basis = [float(module.premium_basis(policy, d, [], 'IT')) for d in days]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.plot(days, values, lw=2.5, color='#2ca02c', label='policy value (EUR)')
    ax.plot(days, basis, lw=2, color='grey', ls='--', label='premiums paid (EUR)')
    periods = [(begin, dt.date(2011, 12, 31), '12.5 %'), (dt.date(2012, 1, 1), dt.date(2014, 6, 30), '20 %'),
               (dt.date(2014, 7, 1), day, '26 %')]
    for (start, end, label), color in zip(periods, ('#e8f4e8', '#fff3d6', '#fde0dd')):
        ax.axvspan(max(start, begin), end, color=color, alpha=0.9, zorder=0)
        ax.text(max(start, begin) + (end - max(start, begin)) / 2, max(values) * 1.02, label, ha='center',
                fontsize=12, fontweight='bold')
    gain = module.gain(policy, payout, [], 'IT')
    tax = module.italian_tax(policy, payout, [], gain)
    ax.set_title(f'Italian substitute tax by rate period, {policy} event {event} ({share:.0%} withdrawn on {day}):\n'
                 f'gain {gain:,.2f} EUR, tax {tax.quantize(Decimal("0.01")):,.2f} = {tax / gain:.1%} effective '
                 f'(a flat 26 % would give {gain * Decimal("0.26"):,.2f})')
    ax.set_ylabel('EUR')
    ax.legend(loc='lower right')
    fig.tight_layout()
    fig.savefig(f'{OUT}/t7_italian_split.png', dpi=140)


def sample_coverage(module, rows, samples):
    """Where the 2,493 payouts are and where the published samples looked: the distribution mismatch."""
    seen = set()
    for name in ('sample_1', 'sample_2'):
        with open(os.path.join(samples, name, 't7_tax_payout.csv')) as f:
            seen |= {(r[0].strip(), int(r[1])) for r in csv.reader(f) if r[0] != 'policy_id'}
    kinds = {400: 'withdrawal', 410: 'surrender', 500: 'death'}
    data, sampled = collections.Counter(), collections.Counter()
    for (policy, event), row in rows.items():
        day = next(p[1] for p in module.payouts()[policy] if p[0] == event)
        state = 'withheld' if row[2] else ('duty only' if row[4] else 'none')
        key = (f'{row[0]} {state}', f'{kinds[int(module.event_types[(policy, event)])]}, '
                                    f'{"COBOL" if day < CONVERSION else "NG"}')
        data[key] += 1
        sampled[key] += (policy, event) in seen
    rows_ = sorted({k[0] for k in data}, key=lambda r: -sum(v for k, v in data.items() if k[0] == r))
    cols = sorted({k[1] for k in data})
    fig, ax = plt.subplots(figsize=(13, 6))
    grid = [[data[(r, c)] for c in cols] for r in rows_]
    ax.imshow([[min(v, 400) for v in line] for line in grid], cmap='Blues', aspect='auto')
    for i, r in enumerate(rows_):
        for j, c in enumerate(cols):
            if data[(r, c)]:
                ax.text(j, i, f'{data[(r, c)]}\n({sampled[(r, c)]})', ha='center', va='center', fontsize=9,
                        color='#b2182b' if not sampled[(r, c)] else 'black')
    ax.set_xticks(range(len(cols)), cols, rotation=20)
    ax.set_yticks(range(len(rows_)), rows_)
    ax.set_title('Payouts per pattern, and (in brackets) how many the published samples checked; red = never checked')
    fig.tight_layout()
    fig.savefig(f'{OUT}/t7_sample_coverage.png', dpi=140)


def main():
    data = load(os.path.join(ROOT, 'legacy'))
    rows, _ = taxes.tax_results(data)
    module = captured[0]
    rule_timeline(module)
    score_progression()
    payout_mix(module, rows)
    italian_split(module)
    if len(sys.argv) > 1:
        sample_coverage(module, rows, sys.argv[1])


if __name__ == '__main__':
    main()
