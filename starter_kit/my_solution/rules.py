"""Building blocks that every task uses: loading, parameter lookups, money rounding and the system change."""
import functools
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from legacy_loader import LegacyData

CENT = Decimal('0.01')
SYSTEM_CONVERSION = 800


@functools.cache
def load(legacy_dir):
    """
    Load the export once, all tasks share the decoded tables.

    Parameters:
    - legacy_dir (str): Folder with the NR*.csv files.

    Returns:
    - LegacyData: Decoded export.
    """
    return LegacyData(legacy_dir)


def conversion_date(data):
    """
    Day of the conversion from the COBOL system to Neuron NG (event 800, 2007-08-11 in this export).

    Parameters:
    - data (LegacyData): Decoded export.

    Returns:
    - pd.Timestamp: Conversion day.
    """
    events = data.table('NREVNT')
    return events[events.EV_EVTTP == SYSTEM_CONVERSION].EV_EFFDT.min()


def valid_on_date(items, date_column, table, prefix, on):
    """
    Attach to each item the row of `table` that is valid on the item's own date.

    A row is valid if VLDFR <= date <= VLDTO; if several are valid, the highest version VRSNR wins.

    Parameters:
    - items (pd.DataFrame): Rows that need a parameter, e.g. premium items.
    - date_column (str): Column of `items` with the date that decides, e.g. 'PR_RCVDT'.
    - table (pd.DataFrame): Table with a validity period, e.g. NRPOLH or NRCOMR.
    - prefix (str): Two-letter alias of `table`, e.g. 'PH'.
    - on (dict): {column of items: column of table} to join on, empty for a table without keys (e.g. NRILLU).

    Returns:
    - pd.DataFrame: The items joined with their valid row (items without one are dropped).
    """
    items = items.reset_index(drop=True).reset_index(names='item')
    merged = items.merge(table, left_on=list(on), right_on=list(on.values())) if on else items.merge(table, how='cross')
    valid = merged[(merged[f'{prefix}_VLDFR'] <= merged[date_column]) & (merged[date_column] <= merged[f'{prefix}_VLDTO'])]
    if f'{prefix}_VRSNR' in valid:
        valid = valid.sort_values(f'{prefix}_VRSNR')
    valid = valid.drop_duplicates('item', keep='last').sort_values('item')
    return valid.drop(columns='item').reset_index(drop=True)


def money(amount, truncate=False):
    """
    Round an exact amount to the cent: half up in Neuron NG, cut off (truncated) in the COBOL system.

    Parameters:
    - amount (Decimal): Exact amount, e.g. Decimal('399.205').
    - truncate (bool): True for a value the COBOL system calculated.

    Returns:
    - Decimal: Rounded amount, e.g. Decimal('399.21') (truncated: Decimal('399.20')).
    """
    return amount.quantize(CENT, ROUND_DOWN if truncate else ROUND_HALF_UP)
