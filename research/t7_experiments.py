"""Compare T7 hypotheses without target leakage or modifying the submitted code.

Snapshots contain local predictions, never hidden targets. Run this script in a
fresh process for each source tree. The experiment matrix reports coverage and
agreement with booking presence, not competition accuracy.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import pathlib
import pickle
import sys
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIELDS = ('country', 'base', 'withholding', 'surcharges', 'stamp', 'remittance')


def changes(before, after, fields):
    common = before.keys() & after.keys()
    return {
        'rows_changed': sum(before[key] != after[key] for key in common),
        'added': len(after.keys() - before.keys()),
        'removed': len(before.keys() - after.keys()),
        'fields': {name: sum(before[key][i] != after[key][i] for key in common)
                   for i, name in enumerate(fields)},
    }


def examples(payout, annual):
    expected_payout = ('DE', Decimal('5628.16'), Decimal('1407.04'),
                       Decimal('77.38'), Decimal('0.00'), dt.date(2006, 8, 10))
    expected_annual = tuple(map(Decimal, ('0', '0', '0', '616.11', '0', '0', '0')))
    result = {'payout': payout.get(('BL10000086', 121)) == expected_payout,
              'annual': annual.get(('BL10000044', 2019)) == expected_annual}
    if not all(result.values()):
        raise AssertionError(f'Task example mismatch: {result}')
    return result


def snapshot(source, legacy, output):
    sys.path.insert(0, str(source))
    from rules import load
    from taxes import tax_results, ANNUAL_TAXES
    data = load(legacy)
    payout, annual = tax_results(data)
    source_digest = hashlib.sha256()
    for path in sorted(source.rglob('*.py')):
        source_digest.update(str(path.relative_to(source)).encode())
        source_digest.update(path.read_bytes())
    result = {'source_sha256': source_digest.hexdigest(), 'payout': payout, 'annual': annual}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pickle.dumps(result))
    summary = {'source_sha256': result['source_sha256'], 'payout_rows': len(payout),
               'annual_rows': len(annual), 'examples': examples(payout, annual)}
    print(json.dumps(summary, indent=2), flush=True)
    return data, payout, annual, ANNUAL_TAXES


def matrix(data, payout, annual, annual_taxes):
    from payout_taxes import TaxModule
    from rules import money
    module = TaxModule(data)
    payouts = module.payouts()
    events = data.table('NREVNT').set_index(['EV_POLNR', 'EV_EVTNR'])
    weak = collections.Counter()
    witnesses = []
    basis_counts = collections.Counter()
    fx_counts = collections.Counter()
    schedule_counts = {name: collections.Counter() for name in ('batch10', 'batch10_weekday')}
    original_amount = module.amount_paid
    assert all(row[2] >= 0 and row[3] >= 0 and row[4] >= 0 for row in payout.values())
    assert all((row[5] is None) == (row[2] + row[3] == 0) for row in payout.values())
    countries = {'CH': 'VST', 'IT': 'SOS', 'DE': 'KST'}
    tax_totals = collections.defaultdict(Decimal)
    for policy, entries in payouts.items():
        withdrawals = []
        for entry in entries:
            event, day, known, gross, share = entry
            key = (policy, event)
            address = module.residence.address(policy, day, known)
            country = address.AD_CNTRY
            row = payout[key]
            net = original_amount(policy, entry)
            kind = int(events.loc[key].EV_EVTTP)
            if net != gross:
                weak['penalty_amount_changed'] += 1
            if kind == 500:
                assert net == gross, 'Unverified death-benefit uplift entered the submitted model'
            if country == 'CH':
                _, threshold = module.rates.rate('CH', 'VST', day, known)
                booked = 'VST' in module.booked[key]
                for label, amount in [('gross', gross), ('net', net)]:
                    converted = module.convert(amount, policy, country, day)
                    predicted = address.AD_TAXST == 'E' and converted > Decimal(str(threshold))
                    weak[f'CH_{label}_disagreements'] += predicted != booked
                weak['CH_rows'] += 1
                gross_chf = module.convert(gross, policy, country, day)
                net_chf = module.convert(net, policy, country, day)
                if gross_chf > Decimal(str(threshold)) >= net_chf and address.AD_TAXST == 'E':
                    witnesses.append({'policy': policy, 'event': event, 'gross': str(gross_chf),
                                      'net': str(net_chf), 'booked': booked})
            if country in ('IT', 'DE'):
                net_gain = module.gain(policy, entry, withdrawals, country)
                module.amount_paid = lambda policy, item: item[3]
                gross_gain = module.gain(policy, entry, withdrawals, country)
                module.amount_paid = original_amount
                booked = countries[country] in module.booked[key]
                for label, gain in [('gross', gross_gain), ('net', net_gain)]:
                    weak[f'{country}_{label}_gain_sign_disagreements'] += (gain > 0) != booked
                    if kind != 500:
                        weak[f'{country}_{label}_nondeath_sign_disagreements'] += (gain > 0) != booked
                # Alternative bookkeeping model: one rounded premium account in
                # the current tax currency, reduced once per previous withdrawal.
                timeline = [(paid_day, 0, premium) for paid_day, premium, _ in module.premiums[policy]
                            if paid_day <= day]
                timeline += [(when, 1, fraction) for when, fraction in withdrawals]
                balance = Decimal(0)
                for when, action, amount in sorted(timeline):
                    if action == 0:
                        balance += module.convert(amount, policy, country, when)
                    else:
                        balance -= money(balance * amount, when < module.conversion)
                replay_gain = module.convert(net, policy, country, day) - money(balance * share, day < module.conversion)
                if replay_gain != net_gain:
                    basis_counts['changed_gains'] += 1
                    basis_counts['with_withholding' if booked else 'without_withholding'] += 1
                    basis_counts['changed_gain_sign'] += (replay_gain > 0) != (net_gain > 0)
                # Competing approach: keep the premium basis in policy currency
                # and convert the resulting gain only at the payout date.
                policy_basis = Decimal(0)
                for paid_day, premium, _ in module.premiums[policy]:
                    if paid_day <= day:
                        remaining = premium
                        for withdrawn_day, fraction in withdrawals:
                            if withdrawn_day >= paid_day:
                                remaining *= 1 - fraction
                        policy_basis += remaining
                fx_gain = module.convert(net - money(policy_basis * share, day < module.conversion),
                                         policy, country, day)
                fx_counts[f'{country}_sign_disagreements'] += (fx_gain > 0) != booked
                if kind != 500:
                    fx_counts[f'{country}_nondeath_sign_disagreements'] += (fx_gain > 0) != booked
                if fx_gain != net_gain:
                    fx_counts['changed_gains'] += 1
                    fx_counts['with_withholding' if booked else 'without_withholding'] += 1
            if row[5] is not None:
                following = (day.replace(day=28) + dt.timedelta(days=4)).replace(day=10)
                weekday = following + dt.timedelta(days=max(0, 7 - following.weekday())) if following.weekday() >= 5 else following
                for label, candidate in [('batch10', following), ('batch10_weekday', weekday)]:
                    if candidate != row[5]:
                        schedule_counts[label]['rows_changed'] += 1
                        schedule_counts[label][country] += 1
                if key == ('BL10000086', 121):
                    assert following == row[5] == weekday
            _, _, _, amounts = module.withholding(policy, entry, withdrawals, country, address.AD_REGIO)
            for tax, amount in amounts.items():
                tax_totals[(policy, day.year, tax)] += amount
            withdrawals.append((day, share))
    for (policy, year), values in annual.items():
        for name in ('VST', 'SOS', 'KST', 'SOL', 'KIS'):
            assert values[annual_taxes.index(name)] == tax_totals[(policy, year, name)]
    return {'booking_presence_agreement': dict(weak), 'threshold_witnesses': witnesses,
            'rounded_running_basis': dict(basis_counts),
            'payout_date_fx_for_entire_gain': dict(fx_counts),
            'date_alternatives': {key: dict(value) for key, value in schedule_counts.items()},
            'invariants': {'nonnegative_withholding_surcharges_stamp': True,
                           'none_date_without_withholding': True,
                           'annual_withholding_reconciles_to_payouts': True},
            'limitation': 'Booking presence and examples do not establish hidden amount or date accuracy.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=pathlib.Path, default=ROOT / 'starter_kit/my_solution')
    parser.add_argument('--legacy', type=pathlib.Path, default=ROOT / 'legacy')
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--baseline', type=pathlib.Path)
    parser.add_argument('--matrix', action='store_true')
    args = parser.parse_args()
    data, payout, annual, names = snapshot(args.source.resolve(), args.legacy.resolve(), args.output)
    report = {}
    if args.baseline:
        baseline = pickle.loads(args.baseline.read_bytes())
        report['versus_baseline'] = {
            'payout': changes(baseline['payout'], payout, FIELDS),
            'annual': changes(baseline['annual'], annual, names),
        }
    if args.matrix:
        report['experiments'] = matrix(data, payout, annual, names)
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
