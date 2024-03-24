# layouts.pyは、アプリケーションのレイアウトを定義するためのモジュールです。
# create_layout関数を提供し、アプリケーションのメインレイアウトを作成します。

from dash import dcc, html

def create_layout():
    """
    アプリケーションのメインレイアウトを作成して返します。
    """
    return html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'margin': '10px', 'color': 'white'
            },
            multiple=True
        ),
        html.Div(id='output-data-upload'),
        html.Div(id='output-graph')
    ], style={'backgroundColor': '#1a1a1a', 'padding': '20px'})