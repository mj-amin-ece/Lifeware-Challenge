"""Compare decoder edge cases, discovery tools and rendered figures across refactors."""
import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
import pathlib
import sys
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR'] = str(ROOT / '.cache/matplotlib')
os.environ['MPLBACKEND'] = 'Agg'


def digest_figure(plt):
    buffer = io.BytesIO()
    plt.gcf().savefig(buffer, format='png')
    result = hashlib.sha256(buffer.getvalue()).hexdigest()
    plt.close('all')
    return result


def collect(solution):
    sys.path.insert(0, str(solution))
    import matplotlib.pyplot as plt
    import pandas as pd
    import legacy_formats as formats
    from tools import change_points, convention_search, policy_timeline, residuals, rule_finder, visuals, weak_labels

    result = {}
    for name, values in [('decode_date', ['', '0', '9999999', '1250131', '970630', '541131', '1240229']),
                         ('invalid_dates', ['', '0', '9999999', '541131', '1240230']),
                         ('decode_timestamp', ['', '20070811013000']),
                         ('decode_text', [' A  ', '', ' BL10000013  ']),
                         ('to_integers', ['', ' 123 ', '-456', '9999999'])]:
        result[name] = getattr(formats, name)(pd.Series(values)).to_json(date_format='iso')
    result['integer_fallback'] = formats.to_integers(pd.Series(['', '1.5', 'bad', '42'])).to_json()
    for scale in [0, 2, 6]:
        result[f'number_{scale}'] = formats.decode_number(pd.Series(['', '-12345', '12500']), scale).to_json()
    result['exact_money'] = str(formats.to_decimal(1234.56))
    birth, day = dt.date(1980, 2, 29), dt.date(2007, 8, 11)
    result['ages'] = [fn(birth, day) for fn in convention_search.CANDIDATES['age']]
    result['day_counts'] = [str(fn(birth, day)) for fn in convention_search.CANDIDATES['day count']]
    result['search'] = convention_search.search({'rate': [1, 2], 'mode': ['a', 'b']},
                                               lambda choice: int(choice['rate'] == 2)).to_json()
    exact = [Decimal('1.235'), Decimal('-1.235'), Decimal('4.201')]
    targets = [Decimal('1.24'), Decimal('-1.24'), Decimal('4.20')]
    result['rounding'] = residuals.rounding_modes(exact, targets).to_json()
    result['differences'] = residuals.classify_differences([0, 1, 2, 3], [0, 1.01, 4, 3.2]).to_json()
    result['ratios'] = residuals.implied_ratios([1, 2, 3, 4], [2, 4, 3, 2]).to_json()
    dates = pd.Series(pd.date_range('2000-01-01', periods=40, freq='30D'))
    wrong = pd.Series([True] * 20 + [False] * 20)
    features = pd.DataFrame({'date': dates, 'code': ['A'] * 20 + ['B'] * 20, 'number': range(40)})
    result['change_points'] = change_points.change_points(dates, wrong, min_rows=5).to_json(date_format='iso')
    result['features'] = rule_finder.prepare_features(features).to_json()
    with contextlib.redirect_stdout(io.StringIO()):
        result['rules'] = rule_finder.find_rules(features, wrong)
        result['weak_rules'] = weak_labels.explain_disagreement(features, [False] * 40, wrong)
    result['agreement'] = weak_labels.agreement([True, False, False], [True, True, False]).to_json()
    result['share_agreeing'] = weak_labels.share_agreeing([True, False, False], [True, True, False])
    plt.show = lambda: None
    visuals.plot_errors_by_era([('Example', [2006, 2007, 2008], {'Rule': [True, False, False]})],
                              pd.Timestamp('2007-08-11'))
    result['era_plot'] = digest_figure(plt)
    visuals.plot_statement_waterfall((100, 4, 5, 6, 7, 22), 'Example')
    result['statement_plot'] = digest_figure(plt)
    result['wrong_by_year'] = visuals.share_wrong_by_year([2000, 2000, 2001], [True, False, True]).to_json()
    rule_finder.plot_wrong_over_time(dates, wrong, 'Example')
    result['wrong_time_plot'] = digest_figure(plt)

    class Fixture:
        def __init__(self):
            self.tables = {name: pd.DataFrame({column: ['EXAMPLE', 'OTHER']})
                           for name, column in policy_timeline.POLICY_TABLES.items()}
            self.tables['NRPOLH'] = pd.DataFrame({'PH_POLNR': ['EXAMPLE'], 'PH_BRKNR': ['B1'],
                'PH_PRDCD': ['P1'], 'PH_VLDFR': pd.to_datetime(['2000-01-01']),
                'PH_VLDTO': pd.to_datetime(['2020-12-31']), 'PH_VRSNR': [1], 'PH_STATE': [10]})
            self.tables['NRRISK']['RK_PERNR'] = ['A1', 'A2']
            self.tables['NRHOLD']['HD_PERNR'] = ['A3', 'A2']
            self.tables['NRPERS'] = pd.DataFrame({'PS_PERNR': ['A1', 'A2', 'A3']})
            self.tables['NRBROK'] = pd.DataFrame({'BR_BRKNR': ['B1', 'B2']})
            self.tables['NRPROD'] = pd.DataFrame({'PD_PRDCD': ['P1', 'P2']})
            self.tables['NRPREM'] = pd.DataFrame({'PR_POLNR': ['EXAMPLE'], 'PR_STATE': ['P'],
                'PR_DUEDT': pd.to_datetime(['2001-01-01']), 'PR_AMTDU': [100]})
            self.tables['NREVNT'] = pd.DataFrame({'EV_POLNR': ['EXAMPLE', 'EXAMPLE'], 'EV_EVTTP': [110, 400],
                'EV_EFFDT': pd.to_datetime(['2001-01-01', '2002-02-01'])})

        def table(self, name):
            return self.tables[name]

        def codes(self, domain):
            return {'110': 'Premium', '400': 'Withdrawal'}

    story = policy_timeline.policy_story(Fixture(), 'EXAMPLE')
    result['policy_story'] = {name: frame.to_json(date_format='iso') for name, frame in story.items()}
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        policy_timeline.print_story(story)
    result['story_text'] = output.getvalue()
    policy_timeline.plot_timeline(story, str(ROOT / '.cache/mi-refactor/fixture.png'))
    result['timeline_plot'] = digest_figure(plt)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--solution', type=pathlib.Path, required=True)
    parser.add_argument('--snapshot', type=pathlib.Path)
    parser.add_argument('--compare', type=pathlib.Path)
    args = parser.parse_args()
    results = collect(args.solution.resolve())
    if args.compare:
        expected = json.loads(args.compare.read_text())
        assert results.keys() == expected.keys()
        for name, value in results.items():
            assert value == expected[name], f'{name} differs from baseline'
        print(f'PASS: {len(results)} decoder, discovery and figure checks match the committed baseline')
    if args.snapshot:
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(json.dumps(results, indent=2) + '\n')
        print(f'Saved {len(results)} decoder, discovery and figure baseline checks')


if __name__ == '__main__':
    main()
