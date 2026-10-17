"""Score the t7 functions locally with the organisers' scoring_t7.py, or write their results as the official files.

    python check_t7.py                       scores against ../targets_t7/ if that folder exists
    python check_t7.py --write predictions   writes t7_tax_payout.csv and t7_tax_annual.csv in the official format

Without targets the script still reports how many rows the official normalizer accepts: a row it cannot convert
counts as wrong.
"""
import argparse
import csv
import pathlib
import time

import scoring_t7
from check import DEFAULT, load_submission

COLUMNS = {
    "t7_tax_payout": ["policy_id", "event_nr", "country", "taxable_base", "withholding", "surcharges", "stamp_duty",
                      "remittance_date"],
    "t7_tax_annual": ["policy_id", "year", "ch_stp", "ch_vst", "it_sos", "it_bol", "de_kst", "de_sol", "de_kis"],
}


def write(folder, task, predictions):
    """Write predictions as the official csv file: the key columns, then the value columns, dates as ISO or empty."""
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / f"{task}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS[task])
        for key, value in sorted(predictions.items()):
            writer.writerow([*key, *("" if v is None else v for v in value)])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--submission", default=DEFAULT / "my_solution")
    parser.add_argument("--legacy", default=DEFAULT.parent / "legacy")
    parser.add_argument("--targets", default=DEFAULT.parent / "targets_t7")
    parser.add_argument("--write", help="folder for the result files", default=None)
    args = parser.parse_args()
    submission = load_submission(args.submission)
    for task in scoring_t7.TASKS:
        started = time.time()
        predictions = getattr(submission, task)(str(args.legacy))
        accepted = scoring_t7.normalize(task, predictions)
        line = f"{task:30s} {len(predictions):6d} rows, {len(accepted):6d} accepted by the scorer"
        if pathlib.Path(args.targets).exists():
            targets = scoring_t7.read_targets(args.targets, task)
            correct, total = scoring_t7.accuracy(task, predictions, targets)
            line += f"   {correct:6d} / {total:6d} = {correct / total:8.4%}"
        print(f"{line}   {time.time() - started:6.1f}s")
        if args.write:
            write(pathlib.Path(args.write), task, predictions)


if __name__ == "__main__":
    main()
