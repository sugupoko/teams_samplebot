"""
Teams Bot のメインファイル（ハンドラ見本帳）。

このファイルでは、よく使う色々なハンドラを書き並べている。
コピペして自分の Bot に組み込めるよう、それぞれにコメント付き。

ハンドラの全体像:
  1. on_members_added       … ユーザーが追加された / Bot がインストールされた
  2. on_message_command     … 特定コマンド（"help" など）にマッチしたメッセージ
  3. on_message_keyword     … キーワードを含むメッセージ
  4. on_mention             … Bot がメンション（@bot）されたとき
  5. on_message             … 上記に該当しない普通のメッセージ（フォールバック）
  6. on_message_reaction    … 👍 などのリアクションが付いた
  7. on_members_removed     … メンバーが退出した
  8. on_typing              … ユーザーがタイピング中
  9. on_error               … 例外が起きたとき
"""

import os
import sys
import traceback
from datetime import datetime
from dotenv import load_dotenv  # .env ファイルを環境変数として読み込む

# Microsoft 365 Agents SDK 本体
from microsoft_agents.hosting.core import (
    AgentApplication,   # Bot 本体のクラス
    TurnState,          # 1 ターンの状態
    TurnContext,        # 1 ターンの文脈（送信者・メッセージ等）
    MemoryStorage,      # メモリ上の状態保存
)
from microsoft_agents.activity import (
    load_configuration_from_env,
    ActivityTypes,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager

from config import Config

load_dotenv()

config = Config(os.environ)
agents_sdk_config = load_configuration_from_env(os.environ)

storage = MemoryStorage()
connection_manager = MsalConnectionManager(**agents_sdk_config)
adapter = CloudAdapter(connection_manager=connection_manager)

agent_app = AgentApplication[TurnState](
    storage=storage,
    adapter=adapter,
    **agents_sdk_config
)


# ────────────────────────────────────────────────
# 1. メンバー追加時（インストール直後・新規参加）
# ────────────────────────────────────────────────
@agent_app.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    """
    Bot がインストールされた直後や、新しい人がチャットに加わったときに呼ばれる。
    新規ユーザー全員に対して 1 回ずつ呼び出される。
    """
    for member in context.activity.members_added or []:
        # 自分自身（Bot）が追加されたイベントは無視
        if member.id == context.activity.recipient.id:
            continue
        name = member.name or "あなた"
        await context.send_activity(f"おはよう、{name}！")


# ────────────────────────────────────────────────
# 2. 特定コマンドへの応答（"help" / "ヘルプ"）
# ────────────────────────────────────────────────
@agent_app.message("help")
@agent_app.message("ヘルプ")
async def on_help(context: TurnContext, _state: TurnState):
    """
    メッセージが完全一致 / 部分一致したときに呼ばれる。
    用途: コマンド型 Bot のディスパッチ。
    """
    help_text = (
        "**使えるコマンド:**\n"
        "- `help` / `ヘルプ` … この一覧\n"
        "- `time` / `時間` … 現在時刻\n"
        "- `echo <文字>` … 入力をそのまま返す\n"
        "- それ以外 … おはよう"
    )
    await context.send_activity(help_text)


@agent_app.message("time")
@agent_app.message("時間")
async def on_time(context: TurnContext, _state: TurnState):
    """現在時刻を返すコマンド。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await context.send_activity(f"いまは {now} だよ")


# ────────────────────────────────────────────────
# 3. キーワード検知（部分一致）
# ────────────────────────────────────────────────
async def on_message(context: TurnContext, _state: TurnState):
    """
    上のコマンドに該当しなかったメッセージを処理するフォールバック。
    キーワードに応じて応答を変える例。
    """
    text = (context.activity.text or "").strip()
    text_lower = text.lower()

    # echo コマンド: "echo こんにちは" → "こんにちは"
    if text_lower.startswith("echo "):
        await context.send_activity(text[5:])
        return

    # キーワードで分岐
    if "天気" in text:
        await context.send_activity("今日は晴れ（仮）")
        return
    if "ありがとう" in text or "thanks" in text_lower:
        await context.send_activity("どういたしまして！")
        return

    # それ以外
    await context.send_activity("おはよう")


# ────────────────────────────────────────────────
# 4. メンション検知（@bot されたか）
# ────────────────────────────────────────────────
async def on_mention_check(context: TurnContext, _state: TurnState) -> bool:
    """Bot 自身がメンションされたか判定する小ヘルパー。"""
    bot_id = context.activity.recipient.id if context.activity.recipient else None
    for entity in context.activity.entities or []:
        if entity.type == "mention" and entity.mentioned and entity.mentioned.id == bot_id:
            return True
    return False


# ────────────────────────────────────────────────
# 5. メッセージ全般のフォールバック
# ────────────────────────────────────────────────
@agent_app.activity(ActivityTypes.message)
async def on_any_message(context: TurnContext, _state: TurnState):
    """
    メッセージ系イベントの最終受け皿。
    @agent_app.message(...) のハンドラがマッチしなかった場合にここへ来る。
    （※ メッセージハンドラの中で最後に登録すること）
    """
    # メンションされていたら専用応答
    if await on_mention_check(context, _state):
        sender = context.activity.from_property.name if context.activity.from_property else "誰か"
        await context.send_activity(f"{sender} さん、呼びましたか？")
        return

    # それ以外は on_message に委譲
    await on_message(context, _state)


# ────────────────────────────────────────────────
# 6. リアクション（👍 などの絵文字反応）
# ────────────────────────────────────────────────
@agent_app.activity(ActivityTypes.message_reaction)
async def on_message_reaction(context: TurnContext, _state: TurnState):
    """
    ユーザーがメッセージにリアクション絵文字をつけた / 外したときに呼ばれる。
    """
    added = context.activity.reactions_added or []
    removed = context.activity.reactions_removed or []
    if added:
        types = ", ".join(r.type for r in added)
        await context.send_activity(f"リアクションありがとう（{types}）")
    if removed:
        types = ", ".join(r.type for r in removed)
        await context.send_activity(f"リアクション外したね（{types}）")


# ────────────────────────────────────────────────
# 7. メンバー退出
# ────────────────────────────────────────────────
@agent_app.conversation_update("membersRemoved")
async def on_members_removed(context: TurnContext, _state: TurnState):
    """誰かがチャット / チームから退出したときに呼ばれる。"""
    for member in context.activity.members_removed or []:
        if member.id == context.activity.recipient.id:
            continue  # 自分自身が外されたケースは別扱いしてもよい
        name = member.name or "誰か"
        await context.send_activity(f"{name} がいなくなった…またね")


# ────────────────────────────────────────────────
# 8. タイピング通知
# ────────────────────────────────────────────────
@agent_app.activity(ActivityTypes.typing)
async def on_typing(context: TurnContext, _state: TurnState):
    """
    ユーザーがメッセージを入力中であることを通知してきたときに呼ばれる。
    返事はしない（うざいので）。ログだけ出す例。
    """
    sender = context.activity.from_property.name if context.activity.from_property else "?"
    print(f"[typing] {sender} が入力中")


# ────────────────────────────────────────────────
# 9. エラー時
# ────────────────────────────────────────────────
@agent_app.error
async def on_error(context: TurnContext, error: Exception):
    """
    どこかのハンドラで例外が起きたときの最終受け皿。
    本番では Application Insights などにログを送るのが良い。
    """
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("ごめん、エラーが出ちゃった")
