# utils.pyは、アプリケーションで使用するユーティリティ関数を定義するためのモジュールです。
# ファイルの解析や、データの分析、グラフの作成などの関数を提供します。

import base64
import io
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from dash import dcc, html

def parse_contents(contents, filename):
    """
    アップロードされたファイルの内容を解析し、データフレームとカラムのリストを返します。
    """
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'pickle' in filename:
            df = pd.read_pickle(io.BytesIO(decoded))
        elif 'xlsx' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div(['このファイル形式はサポートされていません。'], style={'color': 'white'})
        
        columns = df.columns.tolist()
        return df, columns
    except Exception as e:
        return html.Div(['ファイルの処理中にエラーが発生しました。'], style={'color': 'white'})

def update_graph(n_clicks, datetime_col, price_col, position_flag_col, settlement_flag_col, quantity_col, contents, filename, strategy):
    if n_clicks > 0:
        df, _ = parse_contents(contents[0], filename[0])

        df[datetime_col] = pd.to_datetime(df[datetime_col])

        error_messages = []

        # position-flag-columnの値が-1, 0, 1, NaN、または空文字列のみであることを確認
        if position_flag_col and not set(df[position_flag_col].astype(str).str.strip().unique()).issubset({'-1.0', '0.0', '1.0', 'nan', ''}):
            error_messages.append("Position flag column must contain only -1, 0, 1, NaN, or empty string.")

        # 決済フラグの値が0, 1, NaN、または空文字列のみであることを確認
        if settlement_flag_col and settlement_flag_col != 'None' and not set(df[settlement_flag_col].astype(str).str.strip().unique()).issubset({'0.0', '1.0', 'nan', ''}):
            error_messages.append("Settlement flag column must contain only 0, 1, NaN, or empty string.")

        if quantity_col and quantity_col != 'None':
            quantity_values = df[quantity_col].astype(str).str.strip()
            if (pd.to_numeric(quantity_values, errors='coerce') < 0).any():
                error_messages.append("Quantity column must contain only positive numeric values or empty strings.")

        if error_messages:
            return html.Div([
                html.H5("Error"),
                html.Ul([html.Li(error) for error in error_messages]),
            ], style={'color': 'red'})



        # 決済フラグと数量フラグの有無に応じて計算方法を分ける
        if settlement_flag_col is not None and quantity_col is not None:
            # 決済フラグと数量フラグが存在する場合の計算
            df['利益'] = np.nan
            position_open = None
            position_quantity = 0
            for i in range(len(df)):
                if df.loc[i, position_flag_col] != 0 and position_open is None:
                    position_open = i
                    position_quantity = df.loc[i, quantity_col]
                elif df.loc[i, settlement_flag_col] == 1 and position_open is not None:
                    settled_quantity = min(position_quantity, df.loc[i, quantity_col])
                    df.loc[i, '利益'] = (df.loc[i, price_col] - df.loc[position_open, price_col]) * df.loc[position_open, position_flag_col] * settled_quantity
                    position_quantity -= settled_quantity
                    if position_quantity == 0:
                        position_open = None
        elif settlement_flag_col is None and quantity_col is not None:
            # 決済フラグが存在せず、数量フラグのみ存在する場合の計算
            df['利益'] = np.nan
            position_open = None
            for i in range(len(df)):
                if df.loc[i, position_flag_col] != 0 and position_open is None:
                    position_open = i
                elif position_open is not None and df.loc[i, position_flag_col] == -df.loc[position_open, position_flag_col]:
                    df.loc[i, '利益'] = (df.loc[i, price_col] - df.loc[position_open, price_col]) * df.loc[position_open, position_flag_col] * df.loc[position_open, quantity_col]
                    position_open = None
        elif settlement_flag_col is None and quantity_col is None:
            # 決済フラグと数量フラグが存在しない場合の計算
            df['利益'] = np.nan
            position_open = None
            for i in range(len(df)):
                if df.loc[i, position_flag_col] != 0 and position_open is None:
                    position_open = i
                elif position_open is not None and df.loc[i, position_flag_col] == -df.loc[position_open, position_flag_col]:
                    df.loc[i, '利益'] = (df.loc[i, price_col] - df.loc[position_open, price_col]) * df.loc[position_open, position_flag_col]
                    position_open = None
        else:
            # 決済フラグのみ存在する場合の計算（変更なし）
            df['利益'] = np.nan
            position_open = None
            for i in range(len(df)):
                if df.loc[i, position_flag_col] != 0 and position_open is None:
                    position_open = i
                elif settlement_flag_col is not None and df.loc[i, settlement_flag_col] == 1 and position_open is not None:
                    df.loc[i, '利益'] = (df.loc[i, price_col] - df.loc[position_open, price_col]) * df.loc[position_open, position_flag_col]
                    position_open = None
                    position_open = None

        df['累積利益'] = df['利益'].fillna(0).cumsum()
        df['累積利益率'] = df['累積利益'] / df[price_col].iloc[0]
        
        # ポジションの開始と終了点の特定
        position_start = df[df[position_flag_col] != 0][datetime_col]
        if settlement_flag_col is not None:
            position_end = df[(df[settlement_flag_col] == 1) | (df[position_flag_col] == 0)][datetime_col]
        else:
            position_end = df[df[position_flag_col] == -df[position_flag_col].shift(1)][datetime_col]

        # シャープレシオの計算
        risk_free_rate = 0.0  # 無リスク利子率（適切な値に調整）
        returns = df['利益'].fillna(0)
        sharpe_ratio = (returns.mean() - risk_free_rate) / returns.std()

# プロットの作成
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df[datetime_col], y=df[price_col], mode='lines', name='価格', line=dict(color='#3498db')))
        fig.add_trace(go.Scatter(x=position_start, y=df[price_col][df[position_flag_col] != 0], mode='markers', name='ポジション開始', marker=dict(color='#2ecc71', size=8)))
        if settlement_flag_col is not None:
            fig.add_trace(go.Scatter(x=position_end, y=df[price_col][(df[settlement_flag_col] == 1) | (df[position_flag_col] == 0)], mode='markers', name='ポジション終了', marker=dict(color='#e74c3c', size=8)))
        else:
            fig.add_trace(go.Scatter(x=position_end, y=df[price_col][df[position_flag_col] == -df[position_flag_col].shift(1)], mode='markers', name='ポジション終了', marker=dict(color='#e74c3c', size=8)))
        fig.update_layout(
            xaxis=dict(title='日時', gridcolor='#333', zerolinecolor='#333'),
            yaxis=dict(title='価格', gridcolor='#333', zerolinecolor='#333'),
        )

        # ポジション保有期間の密度グラフ
        fig_position_density = go.Figure()
        fig_position_density.add_trace(go.Scatter(x=df[datetime_col], y=(df[position_flag_col] != 0).astype(int), mode='lines', name='ポジション保有密度', line=dict(color='#00B16B')))
        fig_position_density.update_layout(
            xaxis=dict(title='日時', gridcolor='#333', zerolinecolor='#333'),
            yaxis=dict(title='ポジション保有密度', gridcolor='#333', zerolinecolor='#333'),
        )

        # 累積利益率の推移グラフ
        fig_cumulative_profit_ratio = go.Figure()
        fig_cumulative_profit_ratio.add_trace(go.Scatter(x=df[datetime_col], y=df['累積利益率'], mode='lines', name='累積利益率', line=dict(color='#f1c40f')))
        fig_cumulative_profit_ratio.update_layout(
            xaxis=dict(title='日時', gridcolor='#333', zerolinecolor='#333'),
            yaxis=dict(title='累積利益率', gridcolor='#333', zerolinecolor='#333'),
        )

        # 累積利益率の推移グラフ
        fig_cumulative_profit_ratio = go.Figure()
        fig_cumulative_profit_ratio.add_trace(go.Scatter(x=df[datetime_col], y=df['累積利益率'], mode='lines', name='累積利益率', line=dict(color='#f1c40f')))

        # Unit_PnLの計算
        df['Unit_PnL'] = df['利益'].fillna(0)

        # 第二軸にUnit_PnLの棒グラフを追加
        fig_cumulative_profit_ratio.add_trace(go.Bar(x=df[datetime_col], y=df['Unit_PnL'], name='Unit_PnL', yaxis='y2', marker=dict(color='#2ecc71', opacity=0.6)))

        fig_cumulative_profit_ratio.update_layout(
            xaxis=dict(title='日時', gridcolor='#333', zerolinecolor='#333'),
            yaxis=dict(title='累積利益率', gridcolor='#333', zerolinecolor='#333'),
            yaxis2=dict(title='Unit_PnL', overlaying='y', side='right', gridcolor='#333', zerolinecolor='#333'),
            legend=dict(x=0.02, y=0.98, orientation='v', font=dict(color='white')),
            plot_bgcolor='#222',
            paper_bgcolor='#222',
            font=dict(color='white'),
            hovermode='x unified',
        )


        # シャープレシオの推移グラフ
        fig_sharpe_ratio = go.Figure()
        fig_sharpe_ratio.add_trace(go.Scatter(x=df[datetime_col], y=returns.expanding().apply(lambda x: (x.mean() - risk_free_rate) / x.std() if len(x) > 1 else np.nan), mode='lines', name='シャープレシオ', line=dict(color='#EF4123')))
        fig_sharpe_ratio.update_layout(
            xaxis=dict(title='日時', gridcolor='#333', zerolinecolor='#333'),
            yaxis=dict(title='シャープレシオ', gridcolor='#333', zerolinecolor='#333'),
        )

        # マックスドローダウン期間とマックスドローダウンの計算
        df['ピーク'] = df['累積利益率'].cummax()
        df['ドローダウン'] = df['累積利益率'] - df['ピーク']
        max_drawdown_ratio = df['ドローダウン'].min()
        max_drawdown_start = df[df['ドローダウン'] == max_drawdown_ratio][datetime_col].iloc[0]
        max_drawdown_end = df[df[datetime_col] > max_drawdown_start][datetime_col].iloc[0]

        # 勝率、平均利益、平均損失、利益因子の計算
        total_trades = len(df[df['利益'].notnull()])
        winning_trades = len(df[(df['利益'].notnull()) & (df['利益'] > 0)])
        win_rate = winning_trades / total_trades
        avg_profit = df[df['利益'] > 0]['利益'].mean()
        avg_loss = df[df['利益'] < 0]['利益'].mean()
        profit_factor = -avg_profit / avg_loss if avg_loss != 0 else np.inf

        # 最終累積利益率とポジション保有期間の割合の計算
        final_cumulative_profit_ratio = df['累積利益率'].iloc[-1]
        position_period_ratio = len(df[df[position_flag_col] != 0]) / len(df)

        # Buy&Holdの結果を計算
        df_buy_and_hold = df.copy()
        df_buy_and_hold['利益'] = df_buy_and_hold[price_col] - df_buy_and_hold[price_col].iloc[0]
        df_buy_and_hold['累積利益'] = df_buy_and_hold['利益']
        df_buy_and_hold['累積利益率'] = df_buy_and_hold['累積利益'] / df_buy_and_hold[price_col].iloc[0]
        df_buy_and_hold['ポジション保有密度'] = 1

        # Buy&Holdのシャープレシオの計算
        risk_free_rate = 0.0  # 無リスク利子率（適切な値に調整）
        returns_buy_and_hold = df_buy_and_hold['利益']
        sharpe_ratio_buy_and_hold = (returns_buy_and_hold.mean() - risk_free_rate) / returns_buy_and_hold.std()

        # Buy&Holdのマックスドローダウン期間とマックスドローダウンの計算
        df_buy_and_hold['ピーク'] = df_buy_and_hold['累積利益率'].cummax()
        df_buy_and_hold['ドローダウン'] = df_buy_and_hold['累積利益率'] - df_buy_and_hold['ピーク']
        max_drawdown_ratio_buy_and_hold = df_buy_and_hold['ドローダウン'].min()
        max_drawdown_start_buy_and_hold = df_buy_and_hold[df_buy_and_hold['ドローダウン'] == max_drawdown_ratio_buy_and_hold][datetime_col].iloc[0]
        max_drawdown_end_buy_and_hold = df_buy_and_hold[df_buy_and_hold[datetime_col] > max_drawdown_start_buy_and_hold][datetime_col].iloc[0]

        # Buy&Holdの最終累積利益率の計算
        final_cumulative_profit_ratio_buy_and_hold = df_buy_and_hold['累積利益率'].iloc[-1]

        # ポジション保有期間の密度グラフ(Buy&Hold)
        fig_position_density.add_trace(go.Scatter(x=df_buy_and_hold[datetime_col], y=df_buy_and_hold['ポジション保有密度'], mode='lines', name='ポジション保有密度(Buy&Hold)', line=dict(color='#3498db')))

        # 累積利益率の推移グラフ(Buy&Hold)
        fig_cumulative_profit_ratio.add_trace(go.Scatter(x=df_buy_and_hold[datetime_col], y=df_buy_and_hold['累積利益率'], mode='lines', name='累積利益率(Buy&Hold)', line=dict(color='#9b59b6')))

        # シャープレシオの推移グラフ(Buy&Hold)
        fig_sharpe_ratio.add_trace(go.Scatter(x=df_buy_and_hold[datetime_col],
                                            y=returns_buy_and_hold.expanding().apply(lambda x: (x.mean() - risk_free_rate) / x.std() if len(x) > 1 else np.nan), 
                                            mode='lines', name='シャープレシオ(Buy&Hold)', line=dict(color='#5AFF19')))




        # レイアウトの作成
        layout = go.Layout(
            legend=dict(x=0.02, y=0.98, orientation='v', font=dict(color='white')),
            plot_bgcolor='#222',
            paper_bgcolor='#222',
            font=dict(color='white'),
            hovermode='x unified',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
        )

        fig.update_layout(layout)
        fig_position_density.update_layout(layout)
        fig_cumulative_profit_ratio.update_layout(layout)
        fig_sharpe_ratio.update_layout(layout)

        if strategy == 'current':
            final_cumulative_profit_ratio_display = f'{final_cumulative_profit_ratio:.2%}'
            profit_factor_display = f'{profit_factor:.2f}' if profit_factor != np.inf else 'N/A'
            max_drawdown_ratio_display = f'{max_drawdown_ratio:.2%}'
            sharpe_ratio_display = f'{sharpe_ratio:.2f}'
            avg_profit_display = f'{avg_profit:.2f}'
            avg_loss_display = f'{avg_loss:.2f}'
            position_period_ratio_display = f'{position_period_ratio:.2%}'
            win_rate_display = f'{win_rate:.2%}'
        else:
            final_cumulative_profit_ratio_display = f'{final_cumulative_profit_ratio_buy_and_hold:.2%}'
            profit_factor_display = 'N/A'
            max_drawdown_ratio_display = f'{max_drawdown_ratio_buy_and_hold:.2%}'
            sharpe_ratio_display = f'{sharpe_ratio_buy_and_hold:.2f}'
            avg_profit_display = 'N/A'
            avg_loss_display = 'N/A'
            position_period_ratio_display = '100.00%'
            win_rate_display = 'N/A'

        return html.Div([
            html.H5(filename[0], style={'color': 'white'}),
            html.H6(datetime.datetime.utcnow(), style={'color': 'white'}),
            html.Div([
                html.Div([
                    html.Div([
                        html.Div('累積利益率', style={'color': 'white', 'fontSize': '14px'}),
                        html.Div(final_cumulative_profit_ratio_display, style={'color': 'red', 'fontSize': '24px'}),
                    ], className='metric-panel', style={'backgroundColor': '#2a2a2a'}),
                    html.Div([
                        html.Div('利益因子', style={'color': 'white', 'fontSize': '14px'}),
                        html.Div(profit_factor_display, style={'color': 'green', 'fontSize': '24px'}),
                    ], className='metric-panel', style={'backgroundColor': '#2a2a2a'}),
                    html.Div([
                        html.Div('Max Drawdown', style={'color': 'white', 'fontSize': '14px'}),
                        html.Div(max_drawdown_ratio_display, style={'color': '#6495ED', 'fontSize': '24px'}),
                    ], className='metric-panel', style={'backgroundColor': '#2a2a2a'}),
                    html.Div([
                        html.Div('シャープレシオ', style={'color': 'white', 'fontSize': '14px'}),
                        html.Div(sharpe_ratio_display, style={'color': 'orange', 'fontSize': '24px'}),
                    ], className='metric-panel', style={'backgroundColor': '#2a2a2a'}),
                    html.Div([
                        html.Div('平均利益', style={'color': 'white', 'fontSize': '14px'}),
                        html.Div(avg_profit_display, style={'color': 'white', 'fontSize': '24px'}),
                    ], className='metric-panel', style={'backgroundColor': '#2a2a2a'}),
                    html.Div([
                        html.Div('平均損失', style={'color': 'white', 'fontSize': '14px'}),
                        html.Div(avg_loss_display, style={'color': 'white', 'fontSize': '24px'}),
                    ], className='metric-panel', style={'backgroundColor': '#2a2a2a'}),
                    html.Div([
                        html.Div('ポジション保有期間の割合', style={'color': 'white', 'fontSize': '14px'}),
                        html.Div(position_period_ratio_display, style={'color': 'white', 'fontSize': '24px'}),
                    ], className='metric-panel', style={'backgroundColor': '#2a2a2a'}),
                    html.Div([
                        html.Div('勝率', style={'color': 'white', 'fontSize': '14px'}),
                        html.Div(win_rate_display, style={'color': 'white', 'fontSize': '24px'}),
                    ], className='metric-panel', style={'backgroundColor': '#2a2a2a'}),
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '10px', 'marginBottom': '20px'}),
        ], style={'marginBottom': '20px'}),
        html.Div([
            html.Div([
            dcc.Graph(figure=fig)
        ], className='graph-panel', style={'width': 'calc(50% - 10px)'}),
        html.Div([
            dcc.Graph(figure=fig_position_density)
        ], className='graph-panel', style={'width': 'calc(50% - 10px)'}),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'gap': '20px', 'marginBottom': '20px'}),
        html.Div([
        html.Div([
            dcc.Graph(figure=fig_cumulative_profit_ratio)
        ], className='graph-panel', style={'width': 'calc(50% - 10px)'}),
        html.Div([
            dcc.Graph(figure=fig_sharpe_ratio)
        ], className='graph-panel', style={'width': 'calc(50% - 10px)'}),
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'gap': '20px', 'marginBottom': '20px'}),
    ])
    else:
        return html.Div()