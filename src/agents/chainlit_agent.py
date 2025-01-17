from typing import Dict, Optional, Union, Any

import chainlit as cl
from autogen_core.components import RoutedAgent

from src.messages import *


async def ask_helper(func, **kwargs):
    res = await func(**kwargs).send()
    while not res:
        res = await func(**kwargs).send()
    return res


class ChainlitAIAgent(RoutedAgent):
    """
    Wrapper for AutoGens AIAgent
    """

    def send(
            self,
            message: Union[Dict, str],
            recipient: RoutedAgent,
            request_reply: Optional[bool] = None,
            silent: Optional[bool] = False,
    ) -> bool:
        
        cl.run_sync(
            cl.Message(
                content=f'*Sending message to "{recipient.name}":*\n\n{message}',
                author=self.name,
            ).send()
        )
        super(ChainlitAIAgent, self).send(
            message=message,
            recipient=recipient,
            request_reply=request_reply,
            silent=silent,
        )


class ChainlitHumanAgent(RoutedAgent):
    """
    Wrapper for Autogen UserAgent and HumanAgent. Simplifies the UI by adding CL Actions
    """
    def get_human_input(self, prompt: Any) -> Any:
        reply = cl.run_sync(ask_helper(cl.AskUserMessage, content=prompt, timeout=1800))
        # timeout: the number of seconds to wait for an answer before raising a TimeoutError
        return reply["output"].strip()
    