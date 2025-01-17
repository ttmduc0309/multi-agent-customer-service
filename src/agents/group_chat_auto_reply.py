from autogen_core.base import MessageContext, TopicId
from autogen_core.components import RoutedAgent,message_handler
from autogen_core.components.models import (
    AssistantMessage,
)
import chainlit as cl

from ..messages import *


class GroupChatAutoReplyAgent(RoutedAgent):
    def __init__(
        self,
        description: str,
        agent_topic_type: str,
        user_topic_type: str,
        uc_triage_type: str,
        group_chat_topic_type: str,
    ) -> None:
        super().__init__(description)
        self._agent_topic_type = agent_topic_type
        self._user_topic_type = user_topic_type
        self._uc_triage_type = uc_triage_type
        self._group_chat_topic_type = group_chat_topic_type

    @message_handler
    async def handle_agent_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
            reply_template = "Mình xin lỗi, mình chưa hiểu rõ nội dung câu hỏi của bạn, hiện giờ mình đang hỗ trợ bạn về tài khoản đăng nhập, bạn có thể hỏi rõ ràng hơn được không ?."
            print(f"{'-'*80}\n{self.id.type}:\n{reply_template}", flush=True)
            message.context.append(AssistantMessage(content=reply_template, source=self.id.type))
            async with cl.Step(name=f"Auto Reply Agent"):
                await self.publish_message(
                    GroupChatAgentResponse(context=message.context, reply_to_topic_type=self._uc_triage_type),
                    topic_id=TopicId(self._group_chat_topic_type, source=self.id.key),
                )