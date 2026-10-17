"""Compare runtime and peak RSS in alternating, sequential fresh processes.

Both versions use the same Python environment, input files and hash seed. Full
runs execute T0-T5 followed by both T7 entry points; standalone T7 runs measure
the tax evaluator's independent loading/accounting cost. Target scoring, snapshot
retention and the research-only accounting checks are excluded from timing.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import resource
import statistics
import subprocess
import sys
import time


def worker(args):
    sys.path.insert(0, str(args.solution.resolve()))
    wall_start, cpu_start = time.perf_counter(), time.process_time()
    import submission
    imported = time.perf_counter() - wall_start
    tasks = []
    if args.worker == 'full':
        tasks += [('t0_commission', (args.legacy,)),
                  ('t1_next_due_dates', (args.legacy, dt.date(2026, 6, 30))),
                  ('t2_projected_maturity_value', (args.legacy,)),
                  ('t3_surrender_value', (args.legacy, [dt.date(2006, 12, 31),
                                                      dt.date(2020, 4, 30), dt.date(2025, 12, 31)])),
                  ('t4_annual_statement', (args.legacy,)),
                  ('t5_outlier_detection', (args.legacy, args.targets))]
    tasks += [('t7_tax_payout', (args.legacy,)), ('t7_tax_annual', (args.legacy,))]
    measured = {}
    for name, parameters in tasks:
        started = time.perf_counter()
        result = getattr(submission, name)(*parameters)
        measured[name] = {'seconds': time.perf_counter() - started, 'rows': len(result)}
        del result
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss_bytes = usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024
    print(json.dumps({'wall_seconds': time.perf_counter() - wall_start,
                      'cpu_seconds': time.process_time() - cpu_start,
                      'peak_rss_bytes': rss_bytes, 'import_seconds': imported,
                      'tasks': measured}), flush=True)


def summarize(records):
    summary = {}
    for scenario in ['full', 't7']:
        if not any(r['scenario'] == scenario for r in records):
            continue
        by_version = {}
        for version in ['baseline', 'candidate']:
            values = [r for r in records if r['scenario'] == scenario and r['version'] == version]
            by_version[version] = {
                metric: {'median': statistics.median(r[metric] for r in values),
                         'min': min(r[metric] for r in values),
                         'max': max(r[metric] for r in values)}
                for metric in ['wall_seconds', 'cpu_seconds', 'peak_rss_bytes', 'import_seconds']}
        changes = {
            metric: 100 * (by_version['candidate'][metric]['median'] /
                           by_version['baseline'][metric]['median'] - 1)
            for metric in ['wall_seconds', 'cpu_seconds', 'peak_rss_bytes']}
        summary[scenario] = {'versions': by_version, 'median_change_percent': changes}
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=pathlib.Path)
    parser.add_argument('--candidate', type=pathlib.Path)
    parser.add_argument('--legacy', required=True)
    parser.add_argument('--targets', required=True)
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--scenarios', nargs='+', choices=['full', 't7'], default=['full', 't7'])
    parser.add_argument('--candidate-first', action='store_true')
    parser.add_argument('--output', type=pathlib.Path)
    parser.add_argument('--worker', choices=['full', 't7'])
    parser.add_argument('--solution', type=pathlib.Path)
    args = parser.parse_args()
    if args.worker:
        worker(args)
        return
    assert args.baseline and args.candidate and args.output and args.repeat > 0
    records = []
    for scenario in args.scenarios:
        for pair in range(args.repeat):
            baseline_first = (pair % 2 == 0) != args.candidate_first
            order = ['baseline', 'candidate'] if baseline_first else ['candidate', 'baseline']
            for version in order:
                solution = getattr(args, version).resolve()
                command = [sys.executable, str(pathlib.Path(__file__).resolve()), '--worker', scenario,
                           '--solution', str(solution), '--legacy', args.legacy, '--targets', args.targets]
                environment = dict(os.environ, PYTHONHASHSEED='0')
                process = subprocess.run(command, env=environment, check=True, capture_output=True, text=True)
                result = json.loads(process.stdout)
                result.update(scenario=scenario, pair=pair + 1, version=version)
                records.append(result)
                print(f"{scenario} pair {pair + 1} {version}: {result['wall_seconds']:.2f}s wall, "
                      f"{result['cpu_seconds']:.2f}s CPU, {result['peak_rss_bytes'] / 1024**2:.1f} MiB peak RSS",
                      flush=True)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps({'python': sys.version, 'platform': sys.platform,
                                                   'baseline': str(args.baseline.resolve()),
                                                   'candidate': str(args.candidate.resolve()),
                                                   'records': records}, indent=2) + '\n')
    report = json.loads(args.output.read_text())
    report['summary'] = summarize(records)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], indent=2), flush=True)


if __name__ == '__main__':
    main()
