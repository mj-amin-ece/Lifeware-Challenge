"""Submission of the Neuron migration challenge.

Each function gets the folder `legacy_dir` with the NR*.csv files and returns the calculated values.
Dates are `datetime.date`, amounts are `decimal.Decimal`. The rules live in one module per task:

- commission.py: t0, commission of the paid premiums
- schedule.py: t1, next due dates and collection dates
- rules.py: what all tasks share (parameter lookups, rounding, business calendar)
- legacy_loader.py: reads and decodes the export with the data dictionary NRDICT
"""
import datetime as dt
from decimal import Decimal

from commission import commission
from rules import load
from schedule import next_due_dates


def t0_commission(legacy_dir) -> dict[tuple[str, int], Decimal]:
    """{(policy_id, due_nr): commission}"""
    return commission(load(legacy_dir))


def t1_next_due_dates(legacy_dir, extract_date: dt.date) -> dict[tuple[str, int], tuple[dt.date, dt.date]]:
    """{(policy_id, n): (due_date, collection_date)} for the due dates after `extract_date`, n = 1, 2, ..."""
    return next_due_dates(load(legacy_dir), extract_date)


def t2_projected_maturity_value(legacy_dir) -> dict[str, Decimal]:
    """{policy_id: maturity_value}"""
    return {}


def t3_surrender_value(legacy_dir, valuation_dates: list[dt.date]) -> dict[tuple[str, dt.date], Decimal]:
    """{(policy_id, valuation_date): surrender_value}"""
    return {}


def t4_annual_statement(legacy_dir) -> dict[tuple[str, int], tuple[Decimal, ...]]:
    """{(policy_id, year): (premiums, entry_charges, admin_fees, management_fees, risk_charges, total_charges)}"""
    return {}


def t5_outlier_detection(legacy_dir, targets_dir) -> set[tuple[str, object]]:
    """{(task, key)} of the values that were changed by hand.

    `targets_dir` holds the target files (t0 to t4) of the policies to check, in the format of `targets/`. This is
    the only function that may read target files. Example keys: ("t2_projected_maturity_value", "BL10000042"),
    ("t4_annual_statement", ("BL10000042", 2021)).
    """
    return set()
