# hello

Teams Bot の最小サンプル。ハンドラの **見本帳** として使う。

## できること

ユーザーが何を送ってきても基本「おはよう」と返す。`agent.py` には実際に呼ばれるハンドラを 9 種類並べてあり、Bot Framework でどんなイベントが取れるかを一望できる。

## ハンドラ一覧（agent.py）

| # | ハンドラ | 呼ばれるタイミング |
|---|---|---|
| 1 | `on_members_added` | Bot がインストールされた / 新規メンバーがチャットに参加した |
| 2 | `on_help` (`@message("help"/"ヘルプ")`) | ユーザーが `help` または `ヘルプ` と発言した |
| 3 | `on_time` (`@message("time"/"時間")`) | `time` または `時間` と発言した |
| 4 | `on_message` | キーワード（`echo` / `天気` / `ありがとう`）を含むメッセージ |
| 5 | `on_any_message` | 上記に該当しないメッセージのフォールバック |
| 6 | `on_message_reaction` | 👍 などのリアクション絵文字が付いた / 外れた |
| 7 | `on_members_removed` | メンバーがチャットから退出した |
| 8 | `on_typing` | ユーザーがタイピング中 |
| 9 | `on_error` | どこかのハンドラで例外が起きた |

## 使い方

1. VS Code で `/hello` フォルダを開く
2. `Python: Create Environment` で venv 作成（`src/requirements.txt` を選択）
3. F5 → `Debug in Test Tool`（Playground）で起動
4. ブラウザで何か発言してみる

API キーは不要。`env/*.user` の値はダミーのままでOK。

## 主なファイル

- `src/agent.py` … ハンドラ見本帳
- `src/app.py` … aiohttp 起動
- `src/config.py` … 環境変数読み込み

## 次のステップ

`@bot <コマンド名> <引数>` 形式に発展させたいなら → [`../command_bot/`](../command_bot/) へ
