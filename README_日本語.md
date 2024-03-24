[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-<VERSION>-blue?logo=docker)](https://www.docker.com/)
![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)

# Trade Simulation Dashboard
＊＊本文並びに、本アプリはClaude3を利用して大部分を作成しております。＊＊


Trade Simulation Dashboard は、CSVファイルから取引データを分析・可視化し、トレード戦略のパフォーマンスを評価するためのWebアプリケーションです。

対象ユーザーはシステムトレーダーや暗号資産トレーダー（botter）を想定しています。

本アプリの作成背景としては、多くの手法(古典的なインジケータを用いたものから深層学習を用いた複雑なアルゴリズムまで)によってトレード戦略は模索されておりますが、"ポジションの保有・解消のタイミングと数量を算出して、リターンを計算する"というシミュレーション部分は共通していると考えたからです。実際backtesting.pyなどのライブラリも存在します。

これら既存ライブラリとの差別化点は、以下の通りです。
- インタラクティブな可視化とメトリクスの表示
- 必要最低限かつ一枚絵のダッシュボ一ドであること
- トレード戦略のパフォーマンスと買い持ち戦略の比較(今後は保存した他の戦略との比較も追加予定です)

#### 注意 今バージョンでは取引手数料の概念も未実装ですが、今後追加する予定です（プルリクエストは大歓迎です）。
## 機能

- トレードデータを含むCSVファイルのアップロード
- 分析に必要なカラムの選択（datetime、price、position flag、settlement flag、quantity）
    - datetime : 分析対象の資産のタイムスタンプカラムを選択してください
    - price : 分析対象の資産の価格カラムを選択してください
    - position flag: ロングまたはショートのポジションを示すカラムを選択してください。1はロング、-1はショート、0はアクションなしを表します
    - settlement flag: ポジションの決済を示すカラムを選択してください。1は決済、0はアクションなしを表します。これに該当するカラムが存在しない場合は、"None"を選択してください
    - quantity : 数量を表すカラムを選択してください。0または正の値が含まれている必要があります。これに該当するカラムが存在しない場合は、"None"を選択してください
    
    settlement flagとquantity columnsはデータに存在しない場合でも、アプリケーションは機能します。その場合は、それらのカラムに対して"None"を選択してください。
    
- 選択したデータの検証と前処理
- 選択したデータに基づいたインタラクティブな可視化とメトリクスの生成
- トレード戦略のパフォーマンスと買い持ち戦略の比較
- 累積リターン、ドローダウン、シャープレシオなどの主要なメトリクスの表示

![alt text](/image_folder/image.png)

## 始め方

### 前提条件

- Python 3.x
- pipパッケージマネージャー

### インストール(Docker利用無し)

1. リポジトリをクローンします:

```bash
git clone https://github.com/ammtjm/Trade_Simulation_DashBoard.git
```

2. プロジェクトディレクトリに移動します:

```bash
cd Trade_Simulation_DashBoard/application
```

3. 必要な依存関係をインストールします:

```bash
pip install -r requirements.txt
```

### インストール(Docer利用)

1. リポジトリをクローンします:

```bash
git clone https://github.com/ammtjm/Trade_Simulation_DashBoard.git
```

2. プロジェクトディレクトリに移動します:

```bash
cd Trade_Simulation_DashBoard
```

3. Dockerイメージをビルドします:

```bash
docker build -t trade-sim-dashboard .
```

4. Dockerコンテナを実行します:

```bash
docker run -p 8050:8050 trade-sim-dashboard
```

### 使い方

1. アプリケーションを実行します:

```bash
python app.py
```

2. Webブラウザを開き、`http://localhost:8050`にアクセスします。

3. テストを行うには、同じディレクトリにある`test.csv`ファイルをアップロードしてください。

4. "Features"セクションで説明されているように、分析に関連するカラムを選択します。

5. "Analyze"ボタンをクリックして、可視化とメトリクスを生成します。

6. 生成されたグラフとメトリクスを探索し、トレード戦略のパフォーマンスについての洞察を得ます。

![alt text](/image_folder/image-1.png)

## メトリクス

Trade Simulation Dashboardは、トレード戦略のパフォーマンスを評価するためのさまざまなメトリクスを提供します。以下は、コードに基づいて計算される主要なメトリクスです:

1. 累積リターン:
   - 累積リターンは、各トレードの損益を表す'Profit'カラムの合計として計算されます。
   - Formula: `df['Cumulative Profit'] = df['Profit'].fillna(0).cumsum()`

2. 累積リターン率:
   - 累積リターン率は、累積利益を資産の初期価格で割ることで計算されます。
   - Formula: `df['Cumulative Profit Ratio'] = df['Cumulative Profit'] / df[price_col].iloc[0]`

3. シャープレシオ:
   - シャープレシオは、リスク調整後のリターンを測定するメトリクスであり、リスク1単位あたりの超過リターンを表します。
   - リスクフリーレートを平均リターンから差し引き、その結果をリターンの標準偏差で割ることで計算されます。
   - Formula: `sharpe_ratio = (returns.mean() - risk_free_rate) / returns.std()`

4. 最大ドローダウン:
   - 最大ドローダウンは、累積リターンのピークからトラフまでの最大の割合の減少を表します。
   - 累積リターンの最大ピークを見つけ、その後の最低トラフを特定することで計算されます。
   - Formula:
     ```python
     df['Max'] = df['Cumulative Profit Ratio'].cummax()
     df['Drawdown'] = df['Cumulative Profit Ratio'] - df['Max']
     max_drawdown_ratio = df['Drawdown'].min()
     ```

5. 勝率:
   - 勝率は、総トレード数に対する利益のあるトレードの割合を表します。
   - 利益が正のトレードの数を総トレード数で割ることで計算されます。
   - Formula: `win_rate = winning_trades / total_trades`

6. 平均利益と平均損失:
   - 平均利益は、'Profit'カラムの正の値の平均を取ることで計算されます。
   - 平均損失は、'Profit'カラムの負の値の平均を取ることで計算されます。
   - Formulas:
     - `avg_profit = df[df['Profit'] > 0]['Profit'].mean()`
     - `avg_loss = df[df['Profit'] < 0]['Profit'].mean()`

7. 利益係数:
   - 利益係数は、平均利益の絶対値を平均損失の絶対値で割った値です。
   - トレード戦略の収益性を示します。
   - Formula: `profit_factor = -avg_profit / avg_loss`

8. ポジション期間比率:
   - ポジション期間比率は、トレード戦略がポジション（ロングまたはショート）を保有している時間の割合を表します。
   - ポジションフラグが0でない行の数を総行数で割ることで計算されます。
   - Formula: `position_period_ratio = len(df[df[position_flag_col] != 0]) / len(df)`

これらのメトリクスは、トレード戦略のパフォーマンスと特性についての貴重な洞察を提供します。これらのメトリクスを分析することで、ユーザーは自らのトレードアプローチの収益性、リスク、有効性を評価することができます。

注意: コードでは、'Profit'カラムはポジションフラグ、決済フラグ、数量カラムに基づいて計算され、トレード戦略の特定のルールと条件を考慮していることを前提としています。

## ファイル構成

- `app.py`: レイアウトと設定を定義するメインのアプリケーションファイルです。
- `callbacks.py`: ユーザーとのインタラクションを処理し、可視化を更新するためのコールバック関数が含まれています。
- `layouts.py`: アプリケーションのレイアウトコンポーネントを定義します。
- `utils.py`: データ処理と分析のためのユーティリティ関数が含まれています。
- `requirements.txt`: アプリケーションの実行に必要なPythonパッケージの一覧が記載されています。
- `assets/`: CSSファイルなどの静的アセットを保存するためのディレクトリです。

## 貢献

貢献は大歓迎です！問題を見つけた場合や改善の提案がある場合は、Issueを開くかプルリクエストを送信してください。

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細については、[LICENSE](LICENSE)ファイルを参照してください。

## 謝辞

- [Dash](https://dash.plotly.com/) - アプリケーションの構築に使用されたWebフレームワークです。
- [Plotly](https://plotly.com/) - インタラクティブな可視化を作成するために使用されたグラフィックライブラリです。
- [Pandas](https://pandas.pydata.org/) - トレードデータの処理と分析に使用されたデータ操作ライブラリです。

---

```mermaid
graph LR
    A[app.py] --> B[callbacks.py]
    A --> C[layouts.py]
    A --> D[utils.py]
    B --> D
    C --> D
    A --> E[assets/]
    E --> F[styles.css]
```

このダイアグラムでは:
- `app.py`は、他のモジュールをインポートして使用するメインのアプリケーションファイルです。
- `callbacks.py`には、コールバック関数が含まれており、データ処理のために`utils.py`とやり取りします。
- `layouts.py`は、レイアウトコンポーネントを定義し、データ処理のために`utils.py`とやり取りします。
- `utils.py`には、`callbacks.py`と`layouts.py`の両方で使用されるユーティリティ関数が含まれています。
- `assets/`は、`styles.css`などの静的アセットを保存するディレクトリです。

## Author
X アカウント：[めるしー](https://twitter.com/fx24959482)