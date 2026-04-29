"""
Microsoft Teams Bot Agent - 仕様書

機能概要:
このBotはMicrosoft Teamsで動作するAIエージェントです。

主な機能:
1. 通常メッセージ応答:
   - ユーザーのメッセージに対してAI応答を返します
   - 現在はダミークライアントを使用（テスト用）

2. メンション時のチャット情報取得:
   - Botがメンション（@bot, @agentなど）された場合
   - 現在のチャットの詳細情報をまとめて返します
   - 取得する情報:
     * 会話情報（ID、タイプ）
     * 送信者情報（名前、ID）
     * チャンネル情報（チーム名、チャンネル名）
     * 会話参加者一覧
     * メッセージ情報（内容、タイムスタンプ）

3. エラーハンドリング:
   - 設定読み込みエラー
   - メッセージ処理エラー
   - アプリケーション初期化エラー

使用方法:
- 通常のチャット: AIとの会話が可能
- メンション: @bot または @agent と入力するとチャット情報が表示される

設定:
- 環境変数: .envファイルまたはシステム環境変数
- ポート: 3978 (デフォルト)
- Azure OpenAI設定: 必要に応じて環境変数で設定

注意事項:
- 現在はダミークライアントを使用中
- 本番環境ではAzure OpenAIの設定が必要
- Teamsアプリとしてデプロイして使用
"""

import os
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
# from openai import AzureOpenAI

from config import Config

load_dotenv()

# Load configuration
try:
    config = Config(os.environ)
    agents_sdk_config = load_configuration_from_env(os.environ)
except Exception as e:
    print(f"Error loading configuration: {e}", file=sys.stderr)
    traceback.print_exc()
    # Use default empty config for dummy client testing
    config = Config(os.environ)
    agents_sdk_config = {}

# Dummy client for testing
class DummyMessage:
    def __init__(self, content):
        self.content = content

class DummyChoice:
    def __init__(self, content):
        self.message = DummyMessage(content)

class DummyResult:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]

class DummyCompletions:
    def create(self, **kwargs):
        return DummyResult("This is a dummy response from the agent.")

class DummyChat:
    def __init__(self):
        self.completions = DummyCompletions()

class DummyClient:
    def __init__(self):
        self.chat = DummyChat()

client = DummyClient()

# In-memory conversation history for summary
conversation_history = {}  # conversation_id -> list[dict]


# Uncomment below to use Azure OpenAI instead of dummy client
# client = AzureOpenAI(
#     api_version="2024-12-01-preview",
#     api_key=config.azure_openai_api_key,
#     azure_endpoint=config.azure_openai_endpoint,
#     azure_deployment=config.azure_openai_deployment_name,
# )

system_prompt = "You are an AI agent that can chat with users."

# Define storage and application
storage = MemoryStorage()
connection_manager = MsalConnectionManager(**agents_sdk_config)
adapter = CloudAdapter(connection_manager=connection_manager)

try:
    agent_app = AgentApplication[TurnState](
        storage=storage, 
        adapter=adapter, 
        **agents_sdk_config
    )
except Exception as e:
    print(f"Error creating AgentApplication: {e}", file=sys.stderr)
    traceback.print_exc()
    raise

@agent_app.conversation_update("membersAdded")
async def on_members_added(context: TurnContext, _state: TurnState):
    await context.send_activity("Hi there! I'm an agent to chat with you.")

# Listen for ANY message to be received. MUST BE AFTER ANY OTHER MESSAGE HANDLERS
@agent_app.activity(ActivityTypes.message)
async def on_message(context: TurnContext, _state: TurnState):
    try:
        # Record incoming user message for summary
        record_conversation_message(context, "user", context.activity.text or "")

        # Check if the bot is mentioned
        is_mentioned = False
        bot_id = context.activity.recipient.id if context.activity.recipient else None
        
        # Check entities for mentions
        if context.activity.entities:
            for entity in context.activity.entities:
                if entity.type == "mention" and entity.mentioned and entity.mentioned.id == bot_id:
                    is_mentioned = True
                    break
        
        # Check text for @ mentions (fallback)
        text_lower = context.activity.text.lower() if context.activity.text else ""
        if not is_mentioned and text_lower:
            if "@" in text_lower and ("bot" in text_lower or "agent" in text_lower):
                is_mentioned = True

        if is_mentioned and ("help" in text_lower or "ヘルプ" in text_lower):
            help_text = (
                "以下の機能が利用できます:\n"
                "- @bot help / @bot ヘルプ: このヘルプメッセージを表示\n"
                "- @bot summary / @bot サマリー: 過去の会話履歴を表示\n"
                "- @bot: チャット情報を取得してまとめて返す\n"
                "- 通常メッセージ: AI応答を返す"
            )
            await context.send_activity(help_text)
            record_conversation_message(context, "bot", help_text)
        elif is_mentioned and ("summary" in text_lower or "サマリー" in text_lower):
            history_text = await get_conversation_history(context)
            await context.send_activity(history_text)
            record_conversation_message(context, "bot", history_text)
        elif is_mentioned:
            # Get chat information
            chat_info = await get_chat_summary(context)
            await context.send_activity(chat_info)
            record_conversation_message(context, "bot", chat_info)
        else:
            # Normal AI response
            result = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": context.activity.text,
                    },
                ],
                model="",
            )
            
            answer = ""
            for choice in result.choices:
                answer += choice.message.content or ""
            
            await context.send_activity(answer)
        record_conversation_message(context, "bot", answer)
    except Exception as e:
        print(f"Error in on_message: {e}", file=sys.stderr)
        traceback.print_exc()
        await context.send_activity(f"Error processing message: {str(e)}")

async def get_conversation_history(context: TurnContext) -> str:
    conversation_id = context.activity.conversation.id if context.activity.conversation else None
    if not conversation_id:
        return "会話IDが取得できませんでした。"

    history = conversation_history.get(conversation_id, [])
    if not history:
        return "これまでの会話履歴はまだありません。"

    lines = ["**過去の会話履歴:**"]
    for item in history[-20:]:
        lines.append(f"- {item['timestamp']} {item['from']}: {item['text']}")
    return "\n".join(lines)


def record_conversation_message(context: TurnContext, sender: str, text: str) -> None:
    conversation_id = context.activity.conversation.id if context.activity.conversation else None
    if not conversation_id or not text:
        return

    timestamp = str(context.activity.timestamp or "")
    conversation_history.setdefault(conversation_id, []).append({
        "from": sender,
        "text": text,
        "timestamp": timestamp,
    })

async def get_chat_summary(context: TurnContext) -> str:
    """Get and summarize chat information"""
    try:
        summary_parts = []
        
        # Basic conversation info
        conversation = context.activity.conversation
        if conversation:
            summary_parts.append(f"**会話情報:**")
            summary_parts.append(f"- 会話ID: {conversation.id}")
            summary_parts.append(f"- 会話タイプ: {conversation.conversation_type or '不明'}")
        
        # Sender info
        sender = context.activity.from_property
        if sender:
            summary_parts.append(f"\n**送信者情報:**")
            summary_parts.append(f"- 名前: {sender.name or '不明'}")
            summary_parts.append(f"- ID: {sender.id}")
        
        # Channel data (Teams specific)
        channel_data = context.activity.channel_data
        if channel_data:
            summary_parts.append(f"\n**チャンネル情報:**")
            if hasattr(channel_data, 'team') and channel_data.team:
                summary_parts.append(f"- チーム: {channel_data.team.name or '不明'}")
            if hasattr(channel_data, 'channel') and channel_data.channel:
                summary_parts.append(f"- チャンネル: {channel_data.channel.name or '不明'}")
        
        # Try to get conversation members
        try:
            members = await context.adapter.get_conversation_members(context.activity)
            if members:
                summary_parts.append(f"\n**会話参加者 ({len(members)}人):**")
                for member in members[:10]:  # Limit to first 10 members
                    summary_parts.append(f"- {member.name or '不明'} ({member.id})")
                if len(members) > 10:
                    summary_parts.append(f"- ... 他 {len(members) - 10}人")
        except Exception as e:
            summary_parts.append(f"\n**参加者情報取得エラー:** {str(e)}")
        
        # Message info
        summary_parts.append(f"\n**メッセージ情報:**")
        summary_parts.append(f"- メッセージ: {context.activity.text or 'なし'}")
        summary_parts.append(f"- タイムスタンプ: {context.activity.timestamp}")
        
        return "\n".join(summary_parts)
        
    except Exception as e:
        return f"チャット情報取得中にエラーが発生しました: {str(e)}"

@agent_app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The agent encountered an error or bug.")
