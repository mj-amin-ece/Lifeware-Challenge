"""Verify the isolated T7 MONDAY experiment against a trusted local snapshot.

Run from the repository root. Baseline pickle files are local verification
artifacts, never submission inputs. The full collector also checks accounting
and policies without public targets.
"""
import argparse
from collections import Counter
import datetime as dt
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import pickle
import time

from verify_mi_refactor import ROOT, collect, compare
import scoring
from tax_rules import remittance_date


def check_date_cases():
    """Exercise country deadlines, weekends and calendar boundaries."""
    cases = [
        ('DE', '2006-07-17', '2006-08-10'),  # PDF example, weekday unchanged
        ('DE', '2026-09-23', '2026-10-12'),  # Saturday 10 October
        ('DE', '2026-04-03', '2026-05-11'),  # Sunday 10 May
        ('IT', '2026-04-03', '2026-05-18'),  # Saturday 16 May
        ('IT', '2026-07-03', '2026-08-17'),  # Sunday 16 August
        ('IT', '2026-11-30', '2026-12-16'),  # weekday unchanged
        ('CH', '2026-04-01', '2026-06-01'),  # Saturday 30 May, month rollover
        ('CH', '2026-07-31', '2026-08-31'),  # Sunday 30 August
        ('CH', '2018-11-15', '2018-12-31'),  # Sunday 30 December
        ('CH', '2000-01-31', '2000-03-01'),  # leap-year February
        ('CH', '2025-01-31', '2025-03-03'),  # Sunday 2 March
        ('DE', '2026-12-31', '2027-01-11'),  # year rollover, Sunday 10 January
        ('IT', '2026-12-31', '2027-01-18'),  # year rollover, Saturday 16 January
        ('CH', '2026-11-30', '2026-12-30'),  # weekday unchanged
        ('DE', '2020-03-31', '2020-04-10'),  # Good Friday: holidays not adjusted
        ('CH', '2007-07-31', '2007-08-30'),  # before system conversion
    ]
    for country, payout, expected in cases:
        actual = remittance_date(country, dt.date.fromisoformat(payout))
        assert actual == dt.date.fromisoformat(expected), (country, payout, actual, expected)
    print(f'PASS {len(cases)} independent date fixtures', flush=True)


def check_outputs(actual, baseline):
    """Only weekend remittance dates may differ, always to the next Monday."""
    old_rows, new_rows = baseline['t7_tax_payout'], actual['t7_tax_payout']
    assert old_rows.keys() == new_rows.keys(), 'Payout keys changed'
    changed = []
    for key, old in old_rows.items():
        new = new_rows[key]
        assert len(new) == len(old) == 6, f'{key}: unexpected payout shape'
        assert new[:5] == old[:5], f'{key}: non-date payout fields changed'
        previous, current = old[-1], new[-1]
        if previous is None:
            assert current is None, f'{key}: absent date changed'
        elif previous.weekday() < 5:
            assert current == previous, f'{key}: weekday date changed'
        else:
            assert current.weekday() == 0, f'{key}: did not move to Monday'
            assert (current - previous).days in (1, 2), f'{key}: incorrect date shift'
            changed.append({'policy': key[0], 'event': key[1], 'country': old[0],
                            'before': previous.isoformat(), 'after': current.isoformat()})

    # Require full equality elsewhere after independently validating every payout.
    compare({name: value for name, value in actual.items() if name != 't7_tax_payout'},
            {name: value for name, value in baseline.items() if name != 't7_tax_payout'})
    assert new_rows[('BL10000086', 121)] == (
        'DE', *map(Decimal, ['5628.16', '1407.04', '77.38', '0.00']),
        dt.date(2006, 8, 10)), 'PDF payout example changed'
    assert actual['t7_tax_annual'][('BL10000044', 2019)] == (
        Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('616.11'),
        Decimal('0.00'), Decimal('0.00'), Decimal('0.00')), 'PDF annual example changed'
    report = {'payout_rows': len(new_rows), 'annual_rows': len(actual['t7_tax_annual']),
              'dated_payouts': sum(row[-1] is not None for row in old_rows.values()),
              'changed_payouts': len(changed),
              'changed_by_country': dict(Counter(row['country'] for row in changed)),
              'changed_rows': changed}
    print(f"PASS only {len(changed)} weekend dates changed: {report['changed_by_country']}", flush=True)
    print('PASS both PDF examples', flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy', required=True)
    parser.add_argument('--targets', required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check_date_cases()
    with args.baseline.open('rb') as source:
        baseline = pickle.load(source)
    started = time.perf_counter()
    actual = collect(args.legacy, args.targets)
    report = check_outputs(actual, baseline)
    report['verification_seconds'] = time.perf_counter() - started
    report['maintainability'] = scoring.maintainability(ROOT / 'starter_kit/my_solution')
    report['source_sha256'] = {
        str(path.relative_to(ROOT / 'starter_kit/my_solution')):
            hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / 'starter_kit/my_solution').rglob('*.py'))}
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / 'after.pkl').open('wb') as destination:
        pickle.dump(actual, destination, protocol=pickle.HIGHEST_PROTOCOL)
    (args.output / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f"MI: {report['maintainability']['index']}; report: {args.output / 'comparison.json'}", flush=True)


if __name__ == '__main__':
    main()
