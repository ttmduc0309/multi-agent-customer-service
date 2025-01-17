from autogen_core.base.intervention import DefaultInterventionHandler
from autogen_core.base import AgentId
from typing import Any

from ..constants import *
from ..messages import *

class HandoffHandler(DefaultInterventionHandler):
    def __init__(self) -> None:
        super().__init__()
    async def on_publish(self, message: Any, *, sender: AgentId | None) -> Any:
        if isinstance(message, AgentResponse):
            if ("EXIT_CONVERSATION_FLOW" in message.context[-1].content) and (message.context[-1].source==COMPLEX_ACCOUNT_TOPIC_TYPE):
                message.reply_to_topic_type = ERR_ACCOUNT_TOPIC_TYPE
                message.context[-1].content=message.context[-1].content.replace("EXIT_CONVERSATION_FLOW", "")
                message.context[-1].content=message.context[-1].content.replace("------------------------", "")
                return message
        return message

