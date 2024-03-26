import pandas as pd
import numpy as np

"""
コメントアウトされているコードは、データフレームを作成する関数です。
使用の際は、コメントアウトを解除してください。

この関数を使用して、データフレームを作成し、ダッシュボードの入力データとして使用できます。
ただし、ポジションフラグ、決済フラグ、数量については、ダッシュボードの入力データとして使用するために、
適切な形式に沿ってデータフレームを作成する必要があります。
"""


"""
def get_dataframe():
    data = {
        'datetime': pd.date_range(start='2023-01-01', periods=100, freq='D'),
        'price': np.random.randint(100, 200, size=100),
        'position_flag': np.random.choice([-1, 0, 1], size=100),
        'settlement_flag': np.random.choice([0, 1], size=100),
        'quantity': np.random.randint(1, 10, size=100)
    }
    return pd.DataFrame(data)
"""