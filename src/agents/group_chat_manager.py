import string
from typing import List

from autogen_core.base import MessageContext,TopicId
from autogen_core.components import (
    DefaultTopicId,
    RoutedAgent,
    message_handler,
)
from autogen_core.components.models import (
    ChatCompletionClient,
    LLMMessage,
)

from ..messages import *
import json

import chainlit as cl

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True


class GroupChatManager(RoutedAgent):
    def __init__(
        self,
        participant_topic_types: List[str],
        uc_triage_type: str,
        group_chat_topic_type: str,
        user_topic_type: str,
    ) -> None:
        super().__init__("Group chat manager")
        self._participant_topic_types = participant_topic_types
        self._uc_history: List[LLMMessage] = []
        self._conversation_history: List[LLMMessage] = []
        self._uc_triage_type = uc_triage_type
        self._previous_participant_topic_type: str | None = None
        self._agent_topic_type = group_chat_topic_type
        self._user_topic_type = user_topic_type

    @message_handler
    async def handle_user_message(self, message: UserTask, ctx: MessageContext) -> None:
        self._conversation_history= message.context
        self._uc_history.append(message.context[-1])
        await self.publish_message(
                GroupChatMessage(context=self._uc_history),
                topic_id=TopicId(self._uc_triage_type, source=self.id.key),
            )

    @message_handler
    async def handle_agent_response(self, message: GroupChatAgentResponse , ctx: MessageContext) -> None:
        self._conversation_history.append(message.context[-1])
        self._uc_history = message.context
        if is_json(message.context[-1].content):
            response = json.loads(message.context[-1].content)
            if response.get("is_exit",False):
                print(f"{'-'*80}\n{self.id.type}:\nExiting Conversation Flow", flush=True)
            
            if response.get("new_conversation",False):
                async with cl.Step(name=f"Detect New Conversation, Clearing memory"):
                    print(f"{'-'*80}\n{self.id.type}:\nDetect New Conversation, Clearing memory", flush=True)
                    self._conversation_history.pop()
                    self._uc_history.clear()
                    self._uc_history.append(self._conversation_history[-1])
                    await self.publish_message(
                        GroupChatMessage(context=self._uc_history),
                        topic_id=TopicId(message.reply_to_topic_type, source=self.id.key),
                    )
            else:
                await self.publish_message(
                        GroupChatResponse(
                            context=self._conversation_history,
                            reply_to_topic_type=message.reply_to_topic_type if not response.get("is_exit", False) else self._uc_triage_type,
                            reply_to_group_chat=self._agent_topic_type
                            ),
                        topic_id=TopicId(self._user_topic_type, source=self.id.key),
                    )
        
        else:
            response = message.context[-1].content
            await self.publish_message(
                        GroupChatResponse(
                            context=self._conversation_history,
                            reply_to_topic_type=message.reply_to_topic_type,
                            reply_to_group_chat=self._agent_topic_type
                            ),
                        topic_id=TopicId(self._user_topic_type, source=self.id.key),
                    )

    @message_handler
    async def handle_agent_message(self, message: RequestAgent, ctx: MessageContext) -> None:
        if message.agent_type in self._participant_topic_types:
            async with cl.Step(name=f"Handoff to {message.agent_type}"):
                await self.publish_message(
                        GroupChatMessage(context=self._uc_history),
                        topic_id=TopicId(type= message.agent_type, source=self.id.key),
                    )
        else:
            self._uc_history.pop()
            async with cl.Step(name=f"Handoff to {message.agent_type}"):
                await self.publish_message(
                        UserTask(context=self._conversation_history),
                        topic_id=TopicId(type= message.agent_type, source=self.id.key),
                    )
        
    
    @message_handler
    async def handle_transfer_message(self, message: TransferMessage, ctx: MessageContext) -> None:
        self._conversation_history = message.context
        self._uc_history.append(message.context[-1])
        await self.publish_message(
                GroupChatMessage(context=self._uc_history),
                topic_id=TopicId(message.reply_to_topic_type, source=self.id.key),
            )