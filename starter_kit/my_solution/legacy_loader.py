"""Loader for the Neuron legacy export (NR*.csv).

Every column is decoded with the data dictionary NRDICT, so the same code reads every table:

- `C` text columns are trimmed (`'BL10000001  '` -> `'BL10000001'`).
- `N(s)` columns are integers with `s` implied decimals (`N(2)`: `123456` -> 1234.56).
- `D` columns are dates `CYYMMDD` (`1250131` -> 2025-01-31, `970630` -> 1997-06-30),
  `0` means no date (NaT) and `9999999` an open end (OPEN_END).
- `T` columns are timestamps `YYYYMMDDHHMMSS`.
"""
import json
import os
import pathlib
from decimal import Decimal

import pandas as pd

# Stand-in for the open end date 9999999 (pandas cannot store year 9999)
OPEN_END = pd.Timestamp('2200-12-31')
NO_DATE = 0
OPEN_END_CODE = 9999999

DEFAULT_LEGACY_DIR = pathlib.Path(__file__).resolve().parents[2] / 'legacy'


def decode_date(values):
    """
    Decode legacy dates CYYMMDD into timestamps.

    Parameters:
    - values (pd.Series): Raw dates as text, e.g. '1250131' or '970630'.

    Returns:
    - pd.Series: Timestamps, NaT for 0 or empty, OPEN_END for 9999999.
    """
    codes = pd.to_numeric(values, errors='coerce').fillna(NO_DATE).astype('int64')
    real = (codes != NO_DATE) & (codes != OPEN_END_CODE)

    # CYYMMDD: the century digit C counts from 1900
    year = 1900 + codes[real] // 10000
    month = codes[real] // 100 % 100
    month_start = pd.to_datetime(pd.DataFrame({'year': year, 'month': month, 'day': 1}))

    # COBOL accepted impossible days such as 31 November: clamp them to the last day of the month
    day = (codes[real] % 100).clip(upper=month_start.dt.days_in_month)

    dates = pd.Series(pd.NaT, index=values.index, dtype='datetime64[ns]')
    dates[real] = month_start + pd.to_timedelta(day - 1, unit='D')
    dates[codes == OPEN_END_CODE] = OPEN_END
    return dates


def invalid_dates(values):
    """
    Find legacy dates CYYMMDD whose day does not exist in its month (e.g. 541131 = 31 Nov 1954).

    Parameters:
    - values (pd.Series): Raw dates as text.

    Returns:
    - pd.Series: The raw values that `decode_date` had to clamp.
    """
    codes = pd.to_numeric(values, errors='coerce').fillna(NO_DATE).astype('int64')
    real = codes[(codes != NO_DATE) & (codes != OPEN_END_CODE)]
    yyyymmdd = (19000000 + real).astype(str)
    return values[real.index][pd.to_datetime(yyyymmdd, format='%Y%m%d', errors='coerce').isna()]


def decode_number(values, scale):
    """
    Decode fixed-point integers with `scale` implied decimals.

    Parameters:
    - values (pd.Series): Raw integers as text, empty means no value.
    - scale (int): Number of implied decimals.

    Returns:
    - pd.Series: Int64 for scale 0, otherwise float64 (exact enough to explore; use `to_decimal` to calculate).
    """
    numbers = pd.to_numeric(values.str.strip().replace('', None), errors='coerce')
    if scale == 0:
        return numbers.astype('Int64')
    return numbers / 10 ** scale


def to_decimal(value, scale=2):
    """
    Convert a decoded float back into an exact Decimal with `scale` decimals.

    Parameters:
    - value (float): Decoded value, e.g. 1234.56.
    - scale (int): Number of decimals of the source column.

    Returns:
    - Decimal: Exact value, e.g. Decimal('1234.56').
    """
    return Decimal(round(value * 10 ** scale)).scaleb(-scale)


class LegacyData:
    def __init__(self, legacy_dir=DEFAULT_LEGACY_DIR, cache_dir=None):
        """
        Access to all tables of a Neuron export, decoded and cached in memory.

        Parameters:
        - legacy_dir (str): Folder with the NR*.csv files.
        - cache_dir (str): Optional folder for parquet copies of the decoded tables.
          Reading NRBOOK (8M rows) from parquet takes seconds instead of minutes.

        Returns:
        - None
        """
        self.legacy_dir = pathlib.Path(legacy_dir)
        self.cache_dir = pathlib.Path(cache_dir) if cache_dir else None
        self.tables = {}
        self.issues = []

        # The data dictionary describes every column, including its own
        raw_dict = self.read_raw('NRDICT')
        self.dictionary = {
            (row.DC_TABLE.strip(), row.DC_COLUMN.strip()): (row.DC_TYPE.strip(), int(row.DC_SCALE or 0))
            for row in raw_dict.itertuples()
        }

    def read_raw(self, name):
        """
        Read a table as text, exactly as exported.

        Parameters:
        - name (str): Table name, e.g. 'NRPOLH'.

        Returns:
        - pd.DataFrame: All columns as str, empty fields as ''.
        """
        path = self.legacy_dir / f'{name}.csv'
        return pd.read_csv(path, sep=';', dtype=str, keep_default_na=False, encoding='utf-8')

    def decode(self, name, raw):
        """
        Decode every column of a raw table with its type from NRDICT.

        Parameters:
        - name (str): Table name.
        - raw (pd.DataFrame): Table as read by `read_raw`.

        Returns:
        - pd.DataFrame: Decoded table.
        """
        decoders = {
            'C': lambda values, scale: values.str.strip(),
            'N': decode_number,
            'D': lambda values, scale: decode_date(values),
            'T': lambda values, scale: pd.to_datetime(values.replace('', None), format='%Y%m%d%H%M%S'),
        }
        table = pd.DataFrame(index=raw.index)
        for column in raw.columns:
            kind, scale = self.dictionary[(name, column)]
            table[column] = decoders[kind](raw[column], scale)

            # Keep a record of every impossible date that was clamped
            if kind == 'D':
                for row, value in invalid_dates(raw[column]).items():
                    self.issues.append({'table': name, 'column': column, 'row': row, 'raw': value})
        return table

    def table(self, name):
        """
        Get a decoded table, from memory, the parquet cache or the csv file.

        Parameters:
        - name (str): Table name, e.g. 'NRPOLH'.

        Returns:
        - pd.DataFrame: Decoded table.
        """
        if name in self.tables:
            return self.tables[name]

        cache_path = self.cache_dir / f'{name}.parquet' if self.cache_dir else None
        issues_path = self.cache_dir / f'{name}.issues.json' if self.cache_dir else None
        if cache_path and cache_path.exists():
            table = pd.read_parquet(cache_path)
            self.issues.extend(json.loads(issues_path.read_text()))
        else:
            known_issues = len(self.issues)
            table = self.decode(name, self.read_raw(name))
            if cache_path:
                os.makedirs(self.cache_dir, exist_ok=True)
                table.to_parquet(cache_path)
                issues_path.write_text(json.dumps(self.issues[known_issues:]))

        self.tables[name] = table
        return table

    def codes(self, domain):
        """
        Get the English text of every code of a domain from NRCODE.

        Parameters:
        - domain (str): Code domain, e.g. 'EVTTP' or 'STATE'.

        Returns:
        - dict: {code: English text}
        """
        code_table = self.table('NRCODE')
        rows = code_table[code_table.CD_DOMAIN == domain]

        # The rows of the export have only one text field, so the English text sits in CD_TXTDE
        texts = rows.CD_TXTEN.where(rows.CD_TXTEN != '', rows.CD_TXTDE)
        return dict(zip(rows.CD_CODE, texts))

    def table_names(self):
        """
        List the names of all tables in the export.

        Returns:
        - list: Table names, e.g. ['NRADDR', 'NRAGRE', ...].
        """
        return sorted(path.stem for path in self.legacy_dir.glob('NR*.csv'))


def valid_on(table, prefix, date, keys):
    """
    Pick the row valid on `date` per key in a versioned table.

    A row is valid if VLDFR <= date <= VLDTO (both days included). If several rows are valid,
    the highest version number VRSNR wins (see SCHEMA.md).

    Parameters:
    - table (pd.DataFrame): Decoded versioned table, e.g. NRPOLH.
    - prefix (str): Two-letter alias of the table, e.g. 'PH'.
    - date (pd.Timestamp): Day on which the rows must be valid.
    - keys (list): Key columns, e.g. ['PH_POLNR'].

    Returns:
    - pd.DataFrame: One row per key.
    """
    date = pd.Timestamp(date)
    valid = table[(table[f'{prefix}_VLDFR'] <= date) & (date <= table[f'{prefix}_VLDTO'])]
    return valid.sort_values(f'{prefix}_VRSNR').groupby(keys, as_index=False).last()
