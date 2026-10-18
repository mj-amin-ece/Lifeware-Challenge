"""Subgroup discovery: find the groups of rows where a rule is wrong far more often than on average.

Generic, not built for one task: give it a table with one row per checked value, a boolean column saying whether
the rule was wrong, and the columns to describe the rows with. It searches every condition `column == value` and
every pair of them, and ranks the groups by weighted relative accuracy (WRAcc):

    WRAcc = (rows in group / all rows) * (error rate in group - error rate overall)

A group scores high when it is large and much worse than average, so the top groups point to the conditions under
which the rule breaks. Unlike a decision tree, every group is scored on its own, so a second, independent cause is
not hidden below the first split.
"""
import itertools

import pandas as pd


def conditions(table, columns, max_values=12):
    """All conditions `column == value` for the given columns, skipping values that describe a single row."""
    found = []
    for column in columns:
        counts = table[column].value_counts()
        for value in counts[counts > 1].index[:max_values]:
            found.append((column, value))
    return found


def wracc(mask, wrong):
    """Weighted relative accuracy of the group `mask` for the boolean target `wrong`."""
    size = mask.sum()
    if size == 0:
        return float('-inf'), 0, 0.0
    return size / len(wrong) * (wrong[mask].mean() - wrong.mean()), size, wrong[mask].mean()


def discover(table, target, columns, depth=2, top=10, min_size=3):
    """
    Best subgroups for the boolean column `target` of `table`.

    Parameters:
    - table (pd.DataFrame): One row per checked value.
    - target (str): Boolean column, True where the rule was wrong.
    - columns (list): Columns used to describe the groups.
    - depth (int): Number of conditions per group (1 or 2).
    - top (int): Number of groups to return.
    - min_size (int): Smallest group to report.

    Returns:
    - pd.DataFrame: description, rows, wrong rows, error rate, WRAcc; best first.
    """
    wrong = table[target].astype(bool)
    single = conditions(table, columns)
    results = []
    for size in range(1, depth + 1):
        for combo in itertools.combinations(single, size):
            if len({column for column, _ in combo}) < size:
                continue
            mask = pd.Series(True, index=table.index)
            for column, value in combo:
                mask &= table[column] == value
            quality, rows, rate = wracc(mask, wrong)
            if rows >= min_size:
                covered = frozenset(table.index[mask & wrong])
                results.append((' AND '.join(f'{c} = {v}' for c, v in combo), rows, len(covered), rate, quality, covered))
    ranked = pd.DataFrame(results, columns=['subgroup', 'rows', 'wrong', 'error rate', 'WRAcc', 'covered'])
    # the same wrong rows described twice: keep the best description only
    ranked = ranked.sort_values('WRAcc', ascending=False).drop_duplicates('covered', keep='first')
    return ranked.drop(columns='covered').head(top)


def covering(table, target, columns, rounds=4, purity=0.75, depth=2, min_size=2):
    """
    Sequential covering: one cause at a time. Take the best group with an error rate of at least `purity`, set its
    rows aside and search again on the rest, so a second, smaller cause is not drowned by the first.

    Returns:
    - list: (round, subgroup, rows, wrong rows, error rate) per cause found.
    """
    rest, found = table.copy(), []
    for round_ in range(1, rounds + 1):
        if not rest[target].any():
            break
        ranked = discover(rest, target, columns, depth=depth, top=200, min_size=min_size)
        clean = ranked[ranked['error rate'] >= purity]
        if clean.empty:
            break
        best = clean.iloc[0]
        found.append((round_, best.subgroup, best.rows, best.wrong, best['error rate']))
        mask = pd.Series(True, index=rest.index)
        for condition in best.subgroup.split(' AND '):
            column, value = condition.split(' = ', 1)
            mask &= rest[column].astype(str) == value
        rest = rest[~mask]
    return found
