import sys
from pathlib import Path

import pandas as pd
import numpy as np
from dash import html

# Ensure the application package is importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

from application.utils import update_graph


def create_sample_df():
    return pd.DataFrame({
        'datetime': pd.date_range('2023-01-01', periods=2, freq='D'),
        'price': [100, 110],
        'position_flag': [1, 0],
        'settlement_flag': [0, 1],
        'quantity': [1, 1],
    })


def test_profit_and_cumulative_profit_ratio():
    df = create_sample_df()
    result = update_graph(
        1,
        'datetime',
        'price',
        'position_flag',
        'settlement_flag',
        'quantity',
        None,
        ['test.csv'],
        'current',
        df,
    )
    calc_df = result['df']
    assert np.isclose(calc_df.loc[1, 'profit'], 10)
    assert np.isclose(calc_df.loc[1, 'cumulative profit ratio'], 0.1)


def test_missing_price_column_error():
    df = pd.DataFrame({
        'datetime': pd.date_range('2023-01-01', periods=2, freq='D'),
        'position_flag': [1, 0],
        'settlement_flag': [0, 1],
        'quantity': [1, 1],
    })
    result = update_graph(
        1,
        'datetime',
        'price',
        'position_flag',
        'settlement_flag',
        'quantity',
        None,
        ['test.csv'],
        'current',
        df,
    )
    assert isinstance(result, html.Div)
    assert result.children[1].children[0].children == 'Price column "price" not found in the dataframe.'


def test_invalid_position_flag_error():
    df = pd.DataFrame({
        'datetime': pd.date_range('2023-01-01', periods=2, freq='D'),
        'price': [100, 110],
        'position_flag': [2, 0],
        'settlement_flag': [0, 1],
        'quantity': [1, 1],
    })
    result = update_graph(
        1,
        'datetime',
        'price',
        'position_flag',
        'settlement_flag',
        'quantity',
        None,
        ['test.csv'],
        'current',
        df,
    )
    assert isinstance(result, html.Div)
    assert result.children[1].children[0].children == 'Position flag column must contain only -1, 0, 1, NaN, or empty string.'
