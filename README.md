# Teams Bot 作り方メモ

Microsoft Teams 用ボットを Python で作るときの手順。M365 Agents Toolkit を起点に、Custom Engine Agent としてスキャフォールドし、API キーなどはダミーで埋めて開発フローに乗せる。

## 📖 このリポジトリの読み方

サンプルが **段階的に難しくなる** ように並んでいる。最初から全部読まなくてOK。**まず `hello/` を動かす → `command_bot/` で発展形を見る** の順で進めるのがおすすめ。

| ディレクトリ | 役割 | 何を学べるか |
|---|---|---|
| **[`hello/`](./hello/)** | 最小サンプル | Bot Framework のハンドラがどう書かれるかの全体像。`on_members_added` / `on_message` / `on_message_reaction` / `on_typing` / `on_error` など **9 種類のハンドラ見本** が並んでいる。「どんなイベントが取れるか」の地図として使う |
| **[`command_bot/`](./command_bot/)** | コマンドディスパッチ版 | `@bot <コマンド名> <引数>` を解析して、用途別に処理を振り分けるパターン。`search` / `summarize` / `echo` / `ping` などの **実用ユースケースの土台**。LLM や RAG を後から差し込みやすい構造になっている |
| **[`python_bot/`](./python_bot/)** | Toolkit 標準テンプレート | Microsoft 365 Agents Toolkit が生成する素の雛形 + ダミー LLM クライアント。`@bot help` / `@bot summary` などの組み込みコマンド付き。Toolkit の出力を確認したいときに見る |

### 進め方の目安

1. **`hello/`** を F5 で起動 → Playground でメッセージのやり取りができることを確認。`agent.py` のハンドラを 1 つずつ眺めて「Bot って結局これだけのもの」と腹落ちさせる
2. **`command_bot/`** に移って、コマンド型 Bot のディスパッチ構造を理解。`COMMANDS` 辞書に自分で `handle_xxx` を追加してみる
3. ここで初めて **AI / 検索 / 外部 API の差し込み** を考える（`handle_search` の TODO 箇所が出発点）

> **どれもまずダミーで動く**。本物の API キーや Azure リソースは、AI を有効化する段階で初めて必要になる。

---

## 🔰 初心者に優しい Teams Bot の作り方

「Teams Bot って何から触ればいいの？」という人向けの最短ルート。**まずはローカルで動かして "おはよう" に "おはよう" と返すまで** を目指す。難しいことはあとから足せばいい。

### そもそも Teams Bot とは

Teams のチャット欄に常駐して、ユーザーのメッセージに自動で返事するプログラム。LINE Bot や Slack Bot の Teams 版だと思えばだいたい合ってる。

仕組みはシンプル:

```
[ユーザー] → Teams → Microsoft のサーバ → あなたの Bot プログラム → 返信 → Teams → [ユーザー]
```

「あなたの Bot プログラム」の部分を Python で書く。それだけ。

### 知っておくべき登場人物

| 名前 | 役割 | ざっくり言うと |
|---|---|---|
| **Microsoft 365 Agents Toolkit** | VS Code 拡張機能 | プロジェクトの雛形を作って、ローカル実行・デプロイまで面倒見てくれる便利屋 |
| **Custom Engine Agent** | テンプレート種別 | 自分で Python を書いて応答する型。一番自由度が高い |
| **Microsoft 365 Agents Playground** | ブラウザ上のテストツール | Teams を起動しなくても Bot を試せる練習場 |
| **F5 デバッグ** | VS Code の機能 | キー1つで Bot を起動して、自分の Teams に表示できる |
| **manifest.json** | Bot の名刺 | アプリ名・アイコン・どこで動くかが書かれた設定ファイル |
| **テナント** | M365 の組織アカウント | あなた専用の Teams 環境（開発用に無料で作れる） |

### 必要なもの

1. **PC**（Windows / Mac / Linux 何でも OK）
2. **VS Code**（無料）
3. **Python 3.10〜3.11**（[公式サイト](https://www.python.org/) からインストール）
4. **Node.js**（Toolkit の内部で使う。公式サイトから LTS 版）
5. **Microsoft 365 開発者アカウント**（[無料登録ページ](https://developer.microsoft.com/microsoft-365/dev-program)）
   - 普段使いの Microsoft アカウントとは別に、開発専用のテナントを作るのが安全

### Step 1: VS Code に拡張を入れる

VS Code を開いて、左の四角いアイコン（Extensions）から:

- **Microsoft 365 Agents Toolkit** を検索してインストール
- **Python** 拡張もまだなら入れる

### Step 2: プロジェクトを作る

VS Code 左サイドバーの **M365 Agents Toolkit アイコン** をクリック → `Create a New Agent/App`。

ウィザードで以下を選ぶ:

1. App type → **`Custom Engine Agent`**（自分で Python を書くやつ）
2. Programming language → **`Python`**
3. フォルダと名前を決める（例: `python_bot`）

数秒で雛形ができる。`src/agent.py` がメインのファイル。

### Step 3: API キーは「dummy」で OK

最初はわざと **本物の API キーを入れない**。これが大事。

- `env/.env.local.user` の `SECRET_AZURE_OPENAI_API_KEY` などはダミー値（`dummy` でいい）
- ダミーのままでもテンプレートには **DummyClient**（偽の AI）が組み込まれていて、起動確認はできる
- 本物のキーは「実際に AI を呼ぶ段階」になってから入れる

> **なぜダミーから始めるのか**: いきなり本物のキーを入れて動かすと、エラーの原因が「キーが間違っているのか」「コードが間違っているのか」「設定が間違っているのか」分からなくなる。ダミーで起動確認 → 本物に差し替え、の順だと切り分けが楽。

### Step 4: 仮想環境を作って依存関係を入れる

VS Code でコマンドパレット（`Ctrl+Shift+P` / `Cmd+Shift+P`）を開いて:

```
Python: Create Environment
```

を実行 → `venv` を選択 → `src/requirements.txt` をチェック。

これで Python の隔離環境ができて、必要なライブラリが自動で入る。

### Step 5: Playground で動かす（一番簡単）

VS Code の左下の「実行とデバッグ」から **`Debug in Test Tool`**（または `Microsoft 365 Agents Playground`）を選んで **F5**。

ブラウザが開いて、チャット画面が表示される。何か喋りかけてみる:

- 普通のメッセージ → 「This is a dummy response from the agent.」と返ってくる
- `@bot help` → ヘルプメニュー
- `@bot summary` → 過去の会話履歴

**ここまで来たら勝ち**。Bot プログラムは確実に動いている。

### Step 6: 自分の Teams に出す

実際の Teams に Bot を出したくなったら:

1. M365 Agents Toolkit の **Account** セクションで開発者アカウントにサインイン
2. 「実行とデバッグ」で **`Debug in Teams (Edge)`** を選んで F5
3. ブラウザで Teams が開いて、Bot のインストールボタンが出る → Add
4. Bot とチャットできる！

> 内部では「devtunnel」というトンネルが立ち上がって、Teams からあなたの PC のローカル Bot にメッセージが届く仕組み。閉じると Bot は止まる。

### Step 7: コードを書き換えてみる

`src/agent.py` の中の応答メッセージを書き換えて、もう一度 F5。すぐに反映される。

例えば 135 行目あたり:

```python
await context.send_activity("Hi there! I'm an agent to chat with you.")
```

を

```python
await context.send_activity("こんにちは！何か手伝うことある？")
```

にして保存 → F5。これで自分だけの挨拶を返す Bot になった。

### FAQ

#### Q1. エンドポイントは何を入れればいい？

「エンドポイント」は文脈ごとに別物。**hello bot のように AI を使わない最小サンプルなら全部空 or 自動入力でOK**。本物の値が必要になるのは「Azure OpenAI に繋ぐ」「Azure にデプロイする」段階から。

| 求められる場面 | 何のエンドポイント？ | 入れる値 |
|---|---|---|
| `env/.env.*.user` の `AZURE_OPENAI_ENDPOINT` | Azure OpenAI のリソース URL | AI を使わないなら空 or `dummy`。使うなら `https://<リソース名>.openai.azure.com/`（Azure ポータルの「Keys and Endpoint」） |
| `env/.env.local` の `BOT_ENDPOINT` / `BOT_DOMAIN` | Teams が Bot を呼ぶ URL（ローカル時は devtunnel） | 自分で入れない。F5 デバッグ時に Toolkit が自動で埋める |
| Azure ポータルの Bot リソース「Messaging endpoint」 | Bot Framework が Bot を呼ぶ URL | `https://<App Service名>.azurewebsites.net/api/messages`。Toolkit の `provision` が自動設定するので手動入力は基本不要 |
| ローカル実行時の `localhost:3978` | あなたの Bot が待ち受けているポート | デフォルトのまま。Playground / Teams からはこのポートに届く |

#### Q2. F5 で「ポートが使われている」エラーが出る

別の Bot プロセスが残っている。ターミナルで `Ctrl+C` で停止、それでもダメなら PC を再起動。

#### Q3. Teams に Bot が表示されない

サイドロードが許可されていない普段使いのアカウントを使っている可能性が高い。M365 開発者アカウント（無料登録）でサインインし直す。

#### Q4. 「python が見つからない」と言われる

venv が有効化されていない。VS Code のコマンドパレットから `Python: Select Interpreter` で `.venv` の Python を選択する。

#### Q5. 何度起動しても古い応答が返ってくる

Toolkit のキャッシュが残っている。コマンドパレットから `Clear development cache` を実行してから再起動。

#### Q6. `import microsoft_agents` でエラーになる

依存関係が venv に入っていない。`pip install -r src/requirements.txt` を再実行。

#### Q7. API キーが無くても動く？

動く。hello bot は AI を呼ばないので不要。Azure OpenAI の DummyClient テンプレート（python_bot 側）も、ダミー値のまま起動・応答確認まで可能。本物が必要になるのは AI 呼び出しを有効化したとき。

#### Q8. 公開申請のとき何を準備すればいい？

このページの「リリース前に書き換えるべき箇所」を参照。manifest.json のテンプレート文字列・アイコン・プライバシーポリシー URL・利用規約 URL が主な差し替え対象。

#### Q9. ローカルでは動くのに Teams に Push するとエラーになる

devtunnel が切れている / Bot Framework の Messaging endpoint が古い devtunnel URL のまま、というのが多い。F5 を再実行すると新しい URL で再登録される。

#### Q10. 会話履歴を残したい

`MemoryStorage` はプロセス再起動で消えるインメモリ実装。永続化したいなら Azure Blob Storage / Cosmos DB 用のストレージ実装に差し替える。

### 次に何をするか

ここまで来たら、以下の順で世界が広がる:

1. **応答パターンを増やす** → `agent.py` に `if "天気" in text: ...` みたいな分岐を追加
2. **本物の AI に繋ぐ** → `DummyClient()` を `AzureOpenAI(...)` に差し替え、`env/.env.*.user` に本物のキーを入れる
3. **Adaptive Card で見た目をリッチに** → ボタンや画像付きの返答を作れる
4. **外部 API を呼ぶ** → 天気 API、社内システム、何でも繋げる
5. **Azure にデプロイして 24 時間動かす** → このページの「全体フロー」セクションへ

### 最初の壁を越えるコツ

- **欲張らない**: 最初の 1 時間は「F5 で Playground が開く」だけを目標に。AI も Azure も忘れていい
- **エラーは検索する**: 出たエラーをそのまま Google に貼ると、だいたい先人が同じ場所で詰まっている
- **公式サンプルを読む**: [Agents-for-python リポジトリ](https://github.com/microsoft/Agents-for-python) に動くサンプルがいっぱい
- **保存したら F5**: 「コード変えた → F5 → 試す」のループを早く回せると上達が速い

---

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

## リリース前に書き換えるべき箇所

Teams アプリとして公開申請に出す前にテンプレート値のまま残っている箇所を差し替える。

### 1. `appPackage/manifest.json`

| キー | テンプレート初期値 | 差し替え内容 |
|---|---|---|
| `developer.name` | `"My App, Inc."` | 開発元名 |
| `developer.websiteUrl` | `https://www.example.com` | 実在するサイト URL |
| `developer.privacyUrl` | `https://www.example.com/privacy` | プライバシーポリシー URL |
| `developer.termsOfUseUrl` | `https://www.example.com/termofuse` | 利用規約 URL |
| `name.short` | `python_bot${{APP_NAME_SUFFIX}}` | Teams に表示される短縮名（30 字以内） |
| `name.full` | `"full name for python_bot"` | 正式名称 |
| `description.short` | `"short description for python_bot"` | 概要（80 字以内） |
| `description.full` | `"full description for python_bot"` | 詳細説明（4000 字以内） |
| `accentColor` | `#FFFFFF` | アプリのテーマカラー（白以外推奨） |
| `bots[].commandLists` | `"How can you help me?"` 等の雛形 | 実装済みコマンドに合わせる |
| `bots[].scopes` | `team / groupChat / personal` 全有効 | 不要なスコープは外す |
| `validDomains` | `[]` | Bot がアクセスする外部ドメインを列挙 |
| `permissions` | `identity / messageTeamMembers` | 必要以上に増やさない |

> `${{TEAMS_APP_ID}}` `${{BOT_ID}}` は Toolkit が provision 時に自動で埋めるため手動変更不要。
> `${{APP_NAME_SUFFIX}}` は `env/.env.<env>` の `APP_NAME_SUFFIX` を反映する。本番 env では空にすれば末尾の `dev` 等が消える。

### 2. アイコン

- `appPackage/color.png` — 192×192px フルカラー
- `appPackage/outline.png` — 32×32px 白単色アウトライン

両方ともテンプレート画像のままなのでオリジナルに差し替え必須。

### 3. ソースコード

- `src/agent.py` の `client = DummyClient()` を Azure OpenAI クライアント（同ファイル内コメントアウト済みブロック）に切り替え
- `system_prompt` を本番想定に書き換え
- `membersAdded` ハンドラのウェルカムメッセージを差し替え

### 4. 環境変数（本番 env）

- `SECRET_AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_DEPLOYMENT_NAME` を本物の値に
- これらは `env/.env.*.user` に置き、gitignore で除外されたままにする

### 5. リリース直前チェックリスト

- [ ] manifest.json のテンプレート文字列（`example.com` / `My App, Inc.` / `python_bot` 等）が残っていない
- [ ] アイコン 2 枚を差し替え済み
- [ ] DummyClient ではなく実 LLM クライアントに切り替え済み
- [ ] `env/.env.dev.user` 等に本物のシークレットが入っており、git にはコミットされていない
- [ ] `Zip Teams App Package` で本番 env のパッケージをビルドし、Toolkit のバリデーションが通る
- [ ] プライバシーポリシー URL / 利用規約 URL が実在ページを返す

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
