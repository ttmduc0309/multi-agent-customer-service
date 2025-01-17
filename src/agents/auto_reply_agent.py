from autogen_core.base import MessageContext, TopicId
from autogen_core.components import RoutedAgent,message_handler
from autogen_core.components.models import (
    AssistantMessage,
)
from autogen_core.components.tools import Tool

from ..messages import *


class AutoReplyAgent(RoutedAgent):
    def __init__(
        self,
        description: str,
        agent_topic_type: str,
        user_topic_type: str,
        uc_triage_type: str,
    ) -> None:
        super().__init__(description)
        self._agent_topic_type = agent_topic_type
        self._user_topic_type = user_topic_type
        self._uc_triage_type = uc_triage_type

    @message_handler
    async def handle_task(self, message: UserTask, ctx: MessageContext) -> None:
        # Send the task to the LLM.
        if message.context[-1].source=="User":
            await self.publish_message(
                message= message, 
                topic_id=TopicId(type = self._uc_triage_type, source=self.id.key)
                )
        else:
            message.context.pop()
            reply_template = "Mình xin lỗi, mình chưa hiểu rõ nội dung câu hỏi của bạn, hiện giờ mình đang hỗ trợ bạn về tài khoản đăng nhập, bạn có thể hỏi rõ ràng hơn được không ?."
            print(f"{'-'*80}\n{self.id.type}:\n{reply_template}", flush=True)
            message.context.append(AssistantMessage(content=reply_template, source=self.id.type))
            await self.publish_message(
                AgentResponse(context=message.context, reply_to_topic_type=self._agent_topic_type),
                topic_id=TopicId(self._user_topic_type, source=self.id.key),
            )