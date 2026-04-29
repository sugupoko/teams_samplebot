"""
Teams Bot：コマンドディスパッチ版。

hello bot の発展形。「@bot <コマンド名> <引数>」形式の入力をパースして、
コマンドごとに別の処理に振り分けるサンプル。

例:
  @bot search 過去のチケットを調査して  → handle_search("過去のチケットを調査して")
  @bot summarize <長文>                  → handle_summarize(<長文>)
  @bot help                              → コマンド一覧を返す

今回は引数を受け取って echo するだけ。実際の検索や要約処理は TODO のまま残してある。
ここに LLM 呼び出しや RAG を差し込んで使う想定。
"""

import os
import re
import sys
import traceback
from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnState,
    TurnContext,
    MemoryStorage,
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
# ヘルパー: メンション部分を取り除いて本文だけ取り出す
# ────────────────────────────────────────────────
def strip_mention(context: TurnContext) -> str:
    """
    "<at>bot</at> search 過去のチケット" → "search 過去のチケット"
    Teams からのメッセージは <at>...</at> という形でメンションが埋め込まれているので
    自分宛てのものだけを除去する。
    """
    text = context.activity.text or ""
    bot_id = context.activity.recipient.id if context.activity.recipient else None

    # entities から自分宛てメンションの text 部分を除去
    for entity in context.activity.entities or []:
        if entity.type == "mention" and entity.mentioned and entity.mentioned.id == bot_id:
            if entity.text:
                text = text.replace(entity.text, "")

    # 念のため、残った <at>...</at> タグも除去
    text = re.sub(r"<at>.*?</at>", "", text)
    return text.strip()


def parse_command(body: str) -> tuple[str, str]:
    """
    "search 過去のチケットを調査して" → ("search", "過去のチケットを調査して")
    "help"                              → ("help", "")
    ""                                   → ("", "")
    """
    parts = body.split(maxsplit=1)
    if not parts:
        return "", ""
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    return command, args


# ────────────────────────────────────────────────
# 各コマンドの処理本体
# ────────────────────────────────────────────────
async def handle_help(context: TurnContext, _args: str):
    """使えるコマンドの一覧を返す。"""
    text = (
        "**使えるコマンド:**\n"
        "- `@bot help` / `@bot ヘルプ` … この一覧\n"
        "- `@bot search <質問>` … 検索して回答（要 LLM/RAG 実装）\n"
        "- `@bot summarize <文章>` … 文章を要約（要 LLM 実装）\n"
        "- `@bot echo <文字>` … 引数をそのまま返す\n"
        "- `@bot ping` … 生存確認"
    )
    await context.send_activity(text)


async def handle_search(context: TurnContext, query: str):
    """
    例: @bot search 過去のチケットを調査して
    本来はベクター検索 + LLM 回答生成。今は受け取った内容を返すだけ。
    """
    if not query:
        await context.send_activity("検索したい内容を教えて。例: `@bot search 認証エラーの解決策`")
        return

    await context.send_activity(f"「{query}」を検索中…（TODO: 実装）")
    # TODO: ここで RAG / LLM を呼び出して結果を整形して送り返す
    # results = await rag_search(query)
    # await context.send_activity(results)


async def handle_summarize(context: TurnContext, text: str):
    """例: @bot summarize <長文>"""
    if not text:
        await context.send_activity("要約したい文章を貼ってね")
        return
    await context.send_activity(f"要約中…（TODO: LLM 実装）\n対象 {len(text)} 文字")
    # TODO: LLM を呼び出して要約を返す


async def handle_echo(context: TurnContext, args: str):
    """例: @bot echo こんにちは → こんにちは"""
    await context.send_activity(args or "（引数が空）")


async def handle_ping(context: TurnContext, _args: str):
    """生存確認用。"""
    await context.send_activity("pong")


# コマンド名 → 関数 のマップ
COMMANDS = {
    "help": handle_help,
    "ヘルプ": handle_help,
    "search": handle_search,
    "summarize": handle_summarize,
    "echo": handle_echo,
    "ping": handle_ping,
}


# ────────────────────────────────────────────────
# メイン: メッセージを受けてコマンドにディスパッチ
# ────────────────────────────────────────────────
@agent_app.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    for member in context.activity.members_added or []:
        if member.id == context.activity.recipient.id:
            continue
        await context.send_activity(
            f"こんにちは、{member.name or 'あなた'}！\n`@bot help` で使い方を確認できるよ。"
        )


@agent_app.activity(ActivityTypes.message)
async def on_message(context: TurnContext, _state: TurnState):
    body = strip_mention(context)

    # メンションだけ / 空文字
    if not body:
        await context.send_activity("呼びましたか？ `@bot help` で使い方を見られるよ")
        return

    command, args = parse_command(body)
    handler = COMMANDS.get(command)

    if handler is None:
        await context.send_activity(
            f"`{command}` というコマンドは知らない。`@bot help` で一覧を確認してね"
        )
        return

    await handler(context, args)


@agent_app.error
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("ごめん、エラーが出ちゃった")
