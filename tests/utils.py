"""Module for testing utility functions."""


import numpy as np
import pandas as pd


def is_empty(value, empty_values = ('', [], None, np.nan)):
    """Whether an object is empty or not from scraping point of view."""
    if type(value) == str:
        value = value.strip()
    if type(value) == list:
        if len(value) == 0:
            return True
        else:
            return all(is_empty(el) for el in value)
    elif type(value) == dict:
        if len(value) == 0:
            return True
        else:
            return all(is_empty(el) for el in value.values())
    else:
        return value in empty_values


def calc_field_emptiness(df, empty_values=('', [], None, np.nan)):
    """Calculate emptiness of DataFrame columns."""
    stats = []
    for col in df:
        empty = df[col].apply(is_empty, empty_values=empty_values)
        n_empty = empty.sum()
        n_total = len(empty)
        empty_pct = n_empty / n_total * 100
        stats.append({
            'field': col,
            'n_empty': n_empty,
            'n_total': n_total,
            'empty_pct': round(empty_pct, 1)
        })
    stats_df = pd.DataFrame(stats).sort_values('empty_pct', ascending=False)
    return stats_df
