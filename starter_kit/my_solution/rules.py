"""Building blocks that every task uses: loading, parameter lookups and money rounding."""
import functools
from decimal import Decimal, ROUND_HALF_UP

from legacy_loader import LegacyData

CENT = Decimal('0.01')


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


def valid_on_date(items, date_column, table, prefix, on):
    """
    Attach to each item the row of `table` that is valid on the item's own date.

    A row is valid if VLDFR <= date <= VLDTO; if several are valid, the highest version VRSNR wins.

    Parameters:
    - items (pd.DataFrame): Rows that need a parameter, e.g. premium items.
    - date_column (str): Column of `items` with the date that decides, e.g. 'PR_RCVDT'.
    - table (pd.DataFrame): Table with a validity period, e.g. NRPOLH or NRCOMR.
    - prefix (str): Two-letter alias of `table`, e.g. 'PH'.
    - on (dict): {column of items: column of table} to join on.

    Returns:
    - pd.DataFrame: The items joined with their valid row (items without one are dropped).
    """
    merged = items.reset_index(drop=True).reset_index(names='item').merge(
        table, left_on=list(on), right_on=list(on.values()))
    valid = merged[(merged[f'{prefix}_VLDFR'] <= merged[date_column]) & (merged[date_column] <= merged[f'{prefix}_VLDTO'])]
    if f'{prefix}_VRSNR' in valid:
        valid = valid.sort_values(f'{prefix}_VRSNR')
    valid = valid.drop_duplicates('item', keep='last').sort_values('item')
    return valid.drop(columns='item').reset_index(drop=True)


def money(amount):
    """
    Round an exact amount to the cent, half up (commercial rounding).

    Parameters:
    - amount (Decimal): Exact amount, e.g. Decimal('399.205').

    Returns:
    - Decimal: Rounded amount, e.g. Decimal('399.21').
    """
    return amount.quantize(CENT, ROUND_HALF_UP)
