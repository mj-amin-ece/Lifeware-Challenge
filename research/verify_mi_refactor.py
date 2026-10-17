"""Capture or compare complete local predictions and accounting for an MI refactor.

Run from the repository root with --legacy, --targets and --snapshot; later use
--compare on that snapshot in a fresh process. Snapshots are trusted local pickle
files and must stay outside the submission package.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import pickle
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'starter_kit'), str(ROOT / 'starter_kit/my_solution')]

import scoring
import submission
from accounting import policy_bookings
from business_calendar import calendar
from ledger import ledger
from projection import projected_values
from rules import extract_date, load


def collect(legacy, targets):
    """Keep complete task outputs; hash every booking and every unit-history array."""
    results = {}
    for name in scoring.TASKS:
        expected = scoring.read_targets(targets, name)
        started = time.perf_counter()
        results[name] = getattr(submission, name)(legacy, *scoring.arguments(name, expected))
        correct, total = scoring.accuracy(name, results[name], expected)
        print(f'{name}: {correct}/{total} = {correct / total:.4%}; '
              f'{len(results[name])} predictions; {time.perf_counter() - started:.1f}s', flush=True)
    for name, args in [('t5_outlier_detection', (legacy, targets)),
                       ('t7_tax_payout', (legacy,)), ('t7_tax_annual', (legacy,))]:
        results[name] = getattr(submission, name)(*args)
        print(f'{name}: {len(results[name])} results', flush=True)
    data = load(legacy)
    results['projection_years'] = projected_values(data)
    account = ledger(data)
    results['ledger_charges'] = dict(account.charges)
    results['ledger_units'] = {
        key: tuple((str(array.dtype), array.shape, hashlib.sha256(array.tobytes()).hexdigest())
                   for array in arrays) for key, arrays in account.units.items()
    }
    results['booking_hashes'], count = {}, 0
    for policy, bookings in policy_bookings(data, extract_date(data)):
        count += len(bookings)
        results['booking_hashes'][policy] = hashlib.sha256(repr(bookings).encode()).hexdigest()
    results['booking_count'] = count
    local_calendar = calendar(data)
    first, last = dt.date(1990, 1, 1), dt.date(2031, 1, 1)
    results['business_days'] = tuple(
        local_calendar.is_business_day(first + dt.timedelta(days=offset))
        for offset in range((last - first).days))
    extra_dates = [dt.date(1994, 1, 1), dt.date(2007, 8, 10), dt.date(2007, 8, 11),
                   dt.date(2019, 12, 31), dt.date(2026, 6, 30)]
    results['extra_valuations'] = submission.t3_surrender_value(legacy, extra_dates)
    print(f'Captured {count:,} individual bookings, {len(account.units):,} unit histories, '
          'yearly projections, extra valuations and 41 years of business days', flush=True)
    return results


def compare(actual, expected):
    """Require full equality, including policies without train targets."""
    assert actual.keys() == expected.keys(), 'Verification sections changed'
    for name, value in actual.items():
        if value != expected[name]:
            if isinstance(value, dict):
                keys = set(value) | set(expected[name])
                changed = sum(value.get(key) != expected[name].get(key) for key in keys)
                raise AssertionError(f'{name}: {changed} differing or missing keys')
            raise AssertionError(f'{name} changed')
        print(f'PASS exact baseline equality: {name}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy', required=True)
    parser.add_argument('--targets', required=True)
    parser.add_argument('--snapshot', type=pathlib.Path)
    parser.add_argument('--compare', type=pathlib.Path)
    args = parser.parse_args()
    results = collect(args.legacy, args.targets)
    if args.compare:
        with args.compare.open('rb') as source:
            compare(results, pickle.load(source))
    if args.snapshot:
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        with args.snapshot.open('wb') as output:
            pickle.dump(results, output, protocol=pickle.HIGHEST_PROTOCOL)
    mi = scoring.maintainability(ROOT / 'starter_kit/my_solution')
    print('Maintainability:', json.dumps(mi), flush=True)


if __name__ == '__main__':
    main()
