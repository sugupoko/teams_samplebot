# Teams Bot 作り方メモ

Microsoft Teams 用ボットを Python で作るときの手順。M365 Agents Toolkit を起点に、Custom Engine Agent としてスキャフォールドし、API キーなどはダミーで埋めて開発フローに乗せる。

## 前提

- VS Code に **Microsoft 365 Agents Toolkit** 拡張をインストール済み
- Python 3.10+ / Node.js / Azure Functions Core Tools (デバッグ用)
- M365 開発者テナント（Teams サイドロード可能なアカウント）

## 流れ

### 1. M365 Agents Toolkit でプロジェクト作成

VS Code 左サイドバー → **Microsoft 365 Agents Toolkit** → `Create a New Agent/App`。

- **App type**: `Custom Engine Agent`
- **Programming language**: `Python`
- **Folder / App name**: 任意（例: `python_bot`）

これで `python_bot/` 配下に以下が生成される:

```
python_bot/
├── appPackage/        # Teams マニフェスト・アイコン
├── env/               # 環境ごとの設定 (.env.local 等)
├── infra/             # Azure ARM/Bicep
├── src/               # Bot 本体 (Python)
├── m365agents.yml     # Toolkit 用の lifecycle 定義
├── m365agents.local.yml
└── m365agents.playground.yml
```

### 2. Custom Engine Agent を選ぶ理由

- 自前の LLM / 検索 / アプリのロジックをバックエンドに繋げる前提のテンプレート
- Declarative Agent ではなく、コード（Python）で応答を組み立てる
- Bot Framework SDK 互換のメッセージハンドラがそのまま使える

### 3. API キーなどはダミーで埋める

`.env` / `env/.env.local` に Toolkit が変数を吐くので、**実物のキーを入れる前にダミー値で起動確認**する。

```dotenv
# python_bot/.env (例)
BOT_ID=00000000-0000-0000-0000-000000000000
BOT_PASSWORD=dummy-password
AZURE_OPENAI_API_KEY=dummy-key
AZURE_OPENAI_ENDPOINT=https://dummy.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

ダミーのまま `Local debug` で Teams App Test Tool（Playground）を起動できる。実通信が必要な経路に入った時点で本物に差し替える。

### 4. 依存関係インストール

```bash
cd python_bot
python -m venv .venv
source .venv/bin/activate     # Windows は .venv\Scripts\activate
pip install -r src/requirements.txt
```

### 5. ローカル実行

VS Code のデバッグから:

- **Debug in Test Tool** … ブラウザの Playground で UI 確認（M365 アカウント不要）
- **Debug in Teams (Edge/Chrome)** … 実 Teams にサイドロードして確認

`m365agents.local.yml` の `provision` → `deploy` → `preview` が順に走り、トンネル(devtunnel)経由で Teams からローカルの Bot へ繋がる。

### 6. コードを書く

`src/bot.py` などのメッセージハンドラを編集する。最小例:

```python
from botbuilder.core import TurnContext
from teams import Application

bot_app = Application()

@bot_app.message("/ping")
async def ping(context: TurnContext, _state):
    await context.send_activity("pong")
```

### 7. デプロイ（後回しで可）

`Provision` → `Deploy` → `Publish` の順で Azure リソース作成 + コード配備 + Teams 申請。最初はローカルだけで十分。

## 全体フロー（開発 → 配布）

```
[開発フェーズ]
1. ローカルでコーディング & Playground で動作確認
2. F5 デバッグでテナントにサイドロード（自分だけテスト）
        ↓
[本番化フェーズ]
3. Azure / AWS にリソースを provision & deploy
4. アプリパッケージ（zip）を作成
        ↓
[配布フェーズ]
5. Teams 管理者にアプリ承認依頼
6. 管理者が Teams 管理センターで「組織のアプリ」として公開
7. ユーザーが Teams アプリストアの「組織で構築」タブから追加
```

### 各フェーズの補足

- **2 → 3 の間に staging を挟むのが安全**
  F5 ローカルデバッグの次に、いきなり本番ではなく dev/staging 用に provision & deploy を一段挟む。Toolkit なら `env/.env.dev` を作って環境を分ける。トンネル無しで Azure 上の挙動を確認できる。

- **4. zip は Toolkit が自動生成**
  `Zip Teams App Package` コマンドで `appPackage/build/appPackage.<env>.zip` が出力される。env ごとに manifest の Bot ID やドメインが差し替わるので、**本番 env でビルドしたものを申請に回す**。

- **5. 申請時に必要になりがちなもの**
  - zip 本体
  - アイコン（color / outline）
  - アプリ説明・スクリーンショット
  - 必要な権限スコープ
  - プライバシーポリシー URL / 利用規約 URL
  - テナントによっては Purview のデータ取扱区分

- **6. 管理者側の公開オプション**
  - 「組織のアプリ」として手動承認・公開
  - **App setup policy** で特定ユーザー / グループに自動ピン留め
  - **App permission policy** で利用可否を制御

- **7. ユーザーへの見え方**
  「組織で構築」タブから手動追加のほか、App setup policy でピン留めされていれば Teams 起動時に左サイドへ自動表示。ユーザーが自分で探す必要がない状態を作れる。

## ラインナップ（このリポジトリの予定）

- `python_bot/` — 素の Custom Engine Agent 雛形（生成直後）
- 今後追加予定:
  - エコー / コマンドボット
  - Azure OpenAI 連携
  - RAG (Azure AI Search)
  - Adaptive Card 応答
  - 外部 API 連携サンプル

## 参考

- Microsoft 365 Agents Toolkit (旧 Teams Toolkit)
- Bot Framework SDK for Python
- Teams AI Library for Python
