import dash
from dash import dcc, html
from layouts import create_layout
from callbacks import register_callbacks

'''
アプリケーションのメインファイルです。
このファイルは、アプリケーションのエントリーポイントとして機能し、
アプリケーションのレイアウトとコールバックを定義します。
'''

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=['assets/styles.css'])
app.layout = create_layout()
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

if __name__ == '__main__':
    register_callbacks(app)
    app.run_server(debug=True, host='0.0.0.0', port=8050)