# layouts.pyは、アプリケーションのレイアウトを定義するためのモジュールです。
# create_layout関数を提供し、アプリケーションのメインレイアウトを作成します。

from dash import dcc, html

def create_layout():
    return html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='output-data-upload'),
        html.Div(id='output-graph')
    ], style={'backgroundColor': '#1a1a1a', 'padding': '20px'})