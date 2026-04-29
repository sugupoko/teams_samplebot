# CLAUDE.md

このリポジトリで Claude Code が新しい Teams Bot を作るときのワークフロー。

## このリポジトリの構成

段階的に難しくなる Teams Bot サンプル集。

| ディレクトリ | 役割 |
|---|---|
| `hello/` | 最小サンプル + ハンドラ見本帳（9 種類のイベントハンドラ） |
| `command_bot/` | `@bot <コマンド名> <引数>` のディスパッチパターン |
| `python_bot/` | M365 Agents Toolkit が生成する素のテンプレート + ダミー LLM |

新しい Bot を作るときは、これらをベースとしてコピーして派生させる。

---

## 新しい Bot を作るときのワークフロー

ユーザーから「〇〇するボットが欲しい」という要望が来たら、以下の手順で進める。

### Step 1. 要望ヒアリング

まず以下を **対話形式で** 確認する。一気に全部聞かず、必要なものから順に。決まっていない項目があれば「いったん仮で進めますか？」と聞く。

#### 必須で聞くこと

1. **何をする Bot か（ユースケース）**
   - 例: 「ナレッジ検索」「日次の朝会まとめ」「フォーム入力」「タスク管理」
2. **入力の形**
   - DM だけ？ チャネル / グループチャットでも使う？
   - 必ずメンション必要？ それとも何でも反応？
3. **出力の形**
   - テキストで十分？ Adaptive Card で見た目欲しい？ 添付ファイル？
4. **外部サービス連携の有無**
   - LLM 使う？（Azure OpenAI / OpenAI / その他）
   - DB 検索？ Web API 呼び出し？ 内部システム接続？

#### 状況によって聞くこと

5. **会話履歴の永続化**: メモリで揮発でOK？ 永続化必要？（永続化なら Cosmos DB / Blob 等を後で検討）
6. **コマンド一覧の見せ方**: ヘルプメッセージで十分？ Teams のコマンドメニュー (`commandLists`) も登録？
7. **配布範囲**: ローカルで動けばOK？ 個人配布？ 組織配布まで見据える？
8. **デプロイ先**: ローカル F5 だけ？ Azure App Service にデプロイまで？

### Step 2. 仕様をブレイクダウンする

ヒアリングを **箇条書きの仕様メモ** にまとめてユーザーに見せて確認する。書く項目:

```markdown
## 仕様（〇〇bot）

- ユースケース: ...
- 利用範囲: 個人 DM のみ / チャネル可 / グループチャット可
- トリガー: メンション必須 / コマンド形式（@bot <command> <args>）/ 自由文
- コマンド一覧:
  - `@bot <cmd1> <args>` … 〇〇する
  - `@bot <cmd2>` … 〇〇する
- 応答形式: テキスト / Adaptive Card / 添付
- 外部連携: Azure OpenAI（gpt-4o-mini）/ <データソース>
- 状態管理: インメモリ（再起動でリセット） / 永続化（〇〇）
- 想定外入力時: ヘルプを案内 / 「分からない」を返す
```

ここで合意してから次へ進む。**大事なのは合意してから手を動かすこと**。

### Step 3. ベースを選んでコピー

仕様に応じて以下から選ぶ:

| 仕様の傾向 | ベース | 理由 |
|---|---|---|
| 1 種類の応答だけ / イベント練習 | `hello/` | ハンドラ見本帳がそのまま使える |
| `@bot <command> <args>` 形式 | `command_bot/` | ディスパッチ構造ができている |
| AI 応答中心（LLM がそのまま会話） | `python_bot/` | DummyClient → Azure OpenAI 差し替えが楽 |

コピー手順:

```bash
cp -r <base> <new_bot_name>
rm -rf <new_bot_name>/devTools <new_bot_name>/src/__pycache__
```

その後すぐに以下を書き換える:

- `<new_bot_name>/appPackage/manifest.json` の `name.short` / `name.full` / `description.*`
- `<new_bot_name>/README.md` をその Bot 用に書き直し（できること / 主なファイル / 使い方）

### Step 4. 中身を作る

コピーしたあと、以下の順で `src/agent.py` を組み立てる。

#### 4-1. ハンドラのスケルトン

- `command_bot/` ベースなら `COMMANDS` 辞書に `handle_xxx` を追加
- `hello/` ベースなら必要なハンドラだけ残して他は削除
- `python_bot/` ベースなら `on_message` 内で必要な分岐を追加

#### 4-2. 外部連携を差し込む

- LLM: `python_bot/src/agent.py` のコメントアウトされた `AzureOpenAI(...)` ブロックが参考。`config.py` に環境変数を追加
- DB / API: `httpx` や SDK を `requirements.txt` に追加してハンドラから呼ぶ

#### 4-3. 状態管理

- 揮発でいいなら `MemoryStorage` のまま
- 永続化が要るなら `microsoft_agents.hosting.core` の Storage 実装を差し替え or 自前で Cosmos DB クライアントを使う

#### 4-4. ハードコードを避ける

- API キー・エンドポイントは必ず `env/.env.*.user`（gitignore 済み）から読む
- `config.py` に変数を追加 → `agent.py` は `config.xxx` 参照

### Step 5. 動作確認

1. `python -m venv .venv && source .venv/bin/activate && pip install -r src/requirements.txt`
2. F5 → Playground で動作確認
3. 想定したコマンド・想定外のコマンド・空入力・長文 など最低 4 ケース試す
4. 想定外の挙動があれば修正

### Step 6. リポジトリへの反映

- ルート `README.md` の「📖 このリポジトリの読み方」表に新しい Bot を追記
- 新しい Bot の README.md も書く

---

## やってはいけないこと

- ユーザーの要望を聞かずに **勝手に大きな機能を入れない**（LLM・DB・認証連携などは合意してから）
- `env/.env.*.user` に **本物のキーをコミットしない**（`.gitignore` で除外されているか毎回確認）
- 既存の `hello/` `command_bot/` `python_bot/` を **直接書き換えない**（必ずコピーして派生させる）
- ハンドラ内で例外を握りつぶさない（`@agent_app.error` に任せるか、ユーザーに状態を返す）

## ヒアリングが面倒なときのテンプレ

ユーザーが「とりあえず作って」みたいなときは、これを下敷きにユーザーに最低限聞く:

> 1. どんな Bot ですか？（一行で）
> 2. 主な使い方を 2-3 個教えてください（例: `@bot 検索 〇〇` で〇〇を探す）
> 3. 外部の何かに繋ぎますか？（LLM / API / DB / なし）
> 4. ベース は `hello` `command_bot` `python_bot` のどれが近そうですか？（分からなければこちらで提案）

これに答えてもらえれば、Step 2 の仕様メモまで作れる。
