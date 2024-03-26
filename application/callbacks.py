# callbacks.pyは、アプリケーションのコールバック関数を定義するためのモジュールです。
# register_callbacks関数を提供し、アプリケーションにコールバック関数を登録します。

from dash import dcc, html, Input, Output, State
from utils import parse_contents, update_graph
import os
import pandas as pd
import importlib.util
from dash import callback_context

def register_callbacks(app):
    @app.callback(Output('output-data-upload', 'children'),
                  Input('url', 'pathname'))
    def check_input_directory(pathname):
        input_dir = 'Input'
        files = [f for f in os.listdir(input_dir) if f.endswith('.py') and f != '__pycache__']
        if files:
            file_path = os.path.join(input_dir, files[0])
            if os.path.isfile(file_path):
                spec = importlib.util.spec_from_file_location("module.name", file_path)
                if spec is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'get_dataframe'):
                        try:
                            df = module.get_dataframe()
                            return html.Div([
                                dcc.Store(id='input-dataframe', data=df.to_json(orient='split')),
                                dcc.Store(id='input-filename', data=files[0]),
                                dcc.Dropdown(
                                    id='strategy-dropdown',
                                    options=[
                                        {'label': 'Current CSV', 'value': 'current'},
                                        {'label': 'Buy & Hold', 'value': 'buy_and_hold'}
                                    ],
                                    value='current',
                                    clearable=False
                                ),
                                html.Button('Analyze', id='analyze-button', n_clicks=0, className='analyze-button')
                            ])
                        except Exception as e:
                            return html.Div([f'Error in the Python file: {str(e)}'], style={'color': 'white'})
                    else:
                        return html.Div([
                            html.Div(['The Python file does not contain a get_dataframe function.']),
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
                            html.Div(id='output-data-upload-1')
                        ], style={'color': 'white'})
                else:
                    return html.Div(['The Python file is not a valid module.'], style={'color': 'white'})
            else:
                return html.Div(['No valid Python file found in the Input directory.'], style={'color': 'white'})
        else:
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
                html.Div(id='output-data-upload-1')
            ])

    @app.callback(Output('output-data-upload-1', 'children'),
                  Input('upload-data', 'contents'),
                  State('upload-data', 'filename'))
    def update_output(list_of_contents, list_of_names):
        if list_of_contents is not None:
            df, columns = parse_contents(list_of_contents[0], list_of_names[0])

            return html.Div([
                dcc.Store(id='input-dataframe', data=df.to_json(orient='split')),
                dcc.Store(id='input-filename', data=list_of_names[0]),
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='datetime-column',
                            options=[{'label': col, 'value': col} for col in columns],
                            placeholder='Select datetime column'
                        )
                    ], className='three columns'),
                    html.Div([
                        dcc.Dropdown(
                            id='price-column',
                            options=[{'label': col, 'value': col} for col in columns],
                            placeholder='Select price column'
                        )
                    ], className='three columns'),
                    html.Div([
                        dcc.Dropdown(
                            id='position-flag-column',
                            options=[{'label': col, 'value': col} for col in columns],
                            placeholder='Select position flag column'
                        )
                    ], className='three columns'),
                    html.Div([
                        dcc.Dropdown(
                            id='settlement-flag-column',
                            options=[{'label': col, 'value': col} for col in columns] + [{'label': 'None', 'value': 'None'}],
                            placeholder='Select settlement flag column'
                        )
                    ], className='three columns'),
                    html.Div([
                        dcc.Dropdown(
                            id='quantity-column',
                            options=[{'label': col, 'value': col} for col in columns] + [{'label': 'None', 'value': 'None'}],
                            placeholder='Select quantity column'
                        )
                    ], className='three columns'),
                    html.Div([
                        dcc.Dropdown(
                            id='strategy-dropdown',
                            options=[
                                {'label': 'Current CSV', 'value': 'current'},
                                {'label': 'Buy & Hold', 'value': 'buy_and_hold'}
                            ],
                            value='current',
                            clearable=False
                        )
                    ], className='three columns'),
                    html.Div([
                            html.Button('Analyze', id='analyze-button-csv', n_clicks=0, className='analyze-button')
                        ], className='three columns')
                ], className='row')
            ])

    @app.callback(Output('output-graph', 'children', allow_duplicate=True),
                  Input('analyze-button', 'n_clicks'),
                  State('strategy-dropdown', 'value'),
                  State('input-dataframe', 'data'),
                  State('input-filename', 'data'),
                  prevent_initial_call='initial_duplicate')
    def update_output_graph_get_dataframe(n_clicks, strategy, json_data, filename):
        if n_clicks > 0:
            if json_data:
                df = pd.read_json(json_data, orient='split')
                datetime_col = 'datetime'
                price_col = 'price'
                position_flag_col = 'position_flag'
                settlement_flag_col = 'settlement_flag' if 'settlement_flag' in df.columns else None
                quantity_col = 'quantity' if 'quantity' in df.columns else None
                filename = filename

                result = update_graph(n_clicks, datetime_col, price_col, position_flag_col, settlement_flag_col, quantity_col, None, filename, strategy, df)

                output_dir = 'Output_folder'
                os.makedirs(output_dir, exist_ok=True)

                df = result['df']
                df_buy_and_hold = result['df_buy_and_hold']

                output_file = os.path.join(output_dir, f'{os.path.splitext(filename)[0]}_result.xlsx')

                with pd.ExcelWriter(output_file) as writer:
                    df.to_excel(writer, sheet_name='Current Strategy', index=False)
                    df_buy_and_hold.to_excel(writer, sheet_name='Buy and Hold', index=False)

                    metrics = {
                        'Cumulative Profit Ratio': result['final_cumulative_profit_ratio'],
                        'Profit Factor': result['profit_factor'],
                        'Max Drawdown': result['max_drawdown_ratio'],
                        'Sharpe Ratio': result['sharpe_ratio'],
                        'Avg Profit': result['avg_profit'],
                        'Avg Loss': result['avg_loss'],
                        'Position Period Ratio': result['position_period_ratio'],
                        'Win Rate': result['win_rate']
                    }

                    metrics_df = pd.DataFrame.from_dict(metrics, orient='index', columns=['Value'])
                    metrics_df.to_excel(writer, sheet_name='Metrics')

                return result['layout']
        else:
            return html.Div()

    @app.callback(Output('output-graph', 'children', allow_duplicate=True),
                  Input('analyze-button-csv', 'n_clicks'),
                  State('strategy-dropdown', 'value'),
                  State('input-dataframe', 'data'),
                  State('input-filename', 'data'),
                  State('datetime-column', 'value'),
                  State('price-column', 'value'),
                  State('position-flag-column', 'value'),
                  State('settlement-flag-column', 'value'),
                  State('quantity-column', 'value'),
                  prevent_initial_call='initial_duplicate')
    def update_output_graph_csv(n_clicks, strategy, json_data, filename, datetime_col, price_col, position_flag_col, settlement_flag_col, quantity_col):
        if n_clicks > 0:
            if json_data:
                df = pd.read_json(json_data, orient='split')
                settlement_flag_col = None if settlement_flag_col == 'None' else settlement_flag_col
                quantity_col = None if quantity_col == 'None' else quantity_col
                filename = filename

                if datetime_col is None or datetime_col not in df.columns:
                    return html.Div(['No datetime column found in the dataframe.'], style={'color': 'white'})
                if price_col is None or price_col not in df.columns:
                    return html.Div(['No price column found in the dataframe.'], style={'color': 'white'})
                if position_flag_col is None or position_flag_col not in df.columns:
                    return html.Div(['No position flag column found in the dataframe.'], style={'color': 'white'})

                result = update_graph(n_clicks, datetime_col, price_col, position_flag_col, settlement_flag_col, quantity_col, None, filename, strategy, df)

                output_dir = 'Output_folder'
                os.makedirs(output_dir, exist_ok=True)

                df = result['df']
                df_buy_and_hold = result['df_buy_and_hold']

                output_file = os.path.join(output_dir, f'{os.path.splitext(filename)[0]}_result.xlsx')

                with pd.ExcelWriter(output_file) as writer:
                    df.to_excel(writer, sheet_name='Current Strategy', index=False)
                    df_buy_and_hold.to_excel(writer, sheet_name='Buy and Hold', index=False)

                    metrics = {
                        'Cumulative Profit Ratio': result['final_cumulative_profit_ratio'],
                        'Profit Factor': result['profit_factor'],
                        'Max Drawdown': result['max_drawdown_ratio'],
                        'Sharpe Ratio': result['sharpe_ratio'],
                        'Avg Profit': result['avg_profit'],
                        'Avg Loss': result['avg_loss'],
                        'Position Period Ratio': result['position_period_ratio'],
                        'Win Rate': result['win_rate']
                    }

                    metrics_df = pd.DataFrame.from_dict(metrics, orient='index', columns=['Value'])
                    metrics_df.to_excel(writer, sheet_name='Metrics')

                return result['layout']
            else:
                return html.Div(['No file uploaded.'], style={'color': 'white'})
        else:
            return html.Div()