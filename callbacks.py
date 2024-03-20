# callbacks.pyは、アプリケーションのコールバック関数を定義するためのモジュールです。
# register_callbacks関数を提供し、アプリケーションにコールバック関数を登録します。

from dash import dcc, html, Input, Output, State
from utils import parse_contents, update_graph

def register_callbacks(app):
    """
    アプリケーションにコールバック関数を登録します。
    """
    @app.callback(Output('output-data-upload', 'children'),
                Input('upload-data', 'contents'),
                State('upload-data', 'filename'))
    def update_output(list_of_contents, list_of_names):
        """
        ファイルがアップロードされたときに呼び出されるコールバック関数です。
        ファイルの内容を解析し、データ分析に必要な列を選択するためのドロップダウンを作成します。
        """
        if list_of_contents is not None:
            df, columns = parse_contents(list_of_contents[0], list_of_names[0])
            return html.Div([
                dcc.Dropdown(
                    id='datetime-column',
                    options=[{'label': col, 'value': col} for col in columns],
                    placeholder='Select datetime column'
                ),
                dcc.Dropdown(
                    id='price-column',
                    options=[{'label': col, 'value': col} for col in columns],
                    placeholder='Select price column'
                ),
                dcc.Dropdown(
                    id='position-flag-column',
                    options=[{'label': col, 'value': col} for col in columns],
                    placeholder='Select position flag column'
                ),
                dcc.Dropdown(
                    id='settlement-flag-column',
                    options=[{'label': col, 'value': col} for col in columns]+ [{'label': 'None', 'value': 'None'}],
                    placeholder='Select settlement flag column'
                ),
                dcc.Dropdown(
                    id='quantity-column',
                    options=[{'label': col, 'value': col} for col in columns]+ [{'label': 'None', 'value': 'None'}],
                    placeholder='Select quantity column'
                ),
                dcc.Dropdown(
                id='strategy-dropdown',
                options=[
                        {'label': 'Current CSV', 'value': 'current'},
                        {'label': 'Buy & Hold', 'value': 'buy_and_hold'}
                    ],
                value='current',
                clearable=False
                ),
                html.Button('Analyze', id='analyze-button', n_clicks=0)
            ])

    @app.callback(Output('output-graph', 'children'),
        Input('analyze-button', 'n_clicks'),
        Input('strategy-dropdown', 'value'),
        State('datetime-column', 'value'),
        State('price-column', 'value'),
        State('position-flag-column', 'value'),
        State('settlement-flag-column', 'value'),
        State('quantity-column', 'value'),
        State('upload-data', 'contents'),
        State('upload-data', 'filename'))
    def update_output_graph(n_clicks, strategy, datetime_col, price_col, position_flag_col, settlement_flag_col, quantity_col, contents, filename):
        """
        分析ボタンがクリックされたときに呼び出されるコールバック関数です。
        選択された列を使用してデータを分析し、結果のグラフを作成します。
        """
        if n_clicks > 0:
            settlement_flag_col = None if settlement_flag_col == 'None' else settlement_flag_col
            quantity_col = None if quantity_col == 'None' else quantity_col
            return update_graph(n_clicks, datetime_col, price_col, position_flag_col, settlement_flag_col, quantity_col, contents, filename, strategy)
        else:
            return html.Div()
