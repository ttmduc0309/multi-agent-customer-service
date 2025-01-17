from autogen_core.base import MessageContext, TopicId
from autogen_core.components import RoutedAgent, message_handler, DefaultTopicId
from autogen_core.components.models import (
    UserMessage,
)
import chainlit as cl

from .chainlit_agent import ChainlitHumanAgent

from ..messages import *
from ..constants import router_topic_type
import logging
import json

_logger = logging.getLogger(__name__)


def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True


class UserAgent(ChainlitHumanAgent):
    def __init__(self, description: str, user_topic_type: str, agent_topic_type: str) -> None:
        super().__init__(description)
        self._user_topic_type = user_topic_type
        self._agent_topic_type = agent_topic_type

    @message_handler
    async def handle_user_login(self, message: UserLogin, ctx: MessageContext) -> None:
        print(f"Received message from User: {message}")  # Log the received message
        # user_input = message if message else "No input"
        message = message.model_dump_json()
        _logger.info(f"Message from user after model dump json: {message}")
        user_input = self.get_human_input(prompt=f"User login, session ID: {self.id.key}")
        _logger.info(f"User message: {user_input}")
        print(f"User input: {user_input}")
        
        if user_input != "exit":
            await self.publish_message(
                UserTask(context=[UserMessage(content=user_input, source="User")]),
                topic_id=TopicId(router_topic_type, source=self.id.key),
            )
        else:
            print(f"Session ended: {self.id.key}")


    @message_handler
    async def handle_task_result(self, message: AgentResponse, ctx: MessageContext) -> None:
        _logger.info(f"Agent response: {message.context[-1].content}")
        if is_json(message.context[-1].content):
            reply = json.loads(message.context[-1].content)["response"]
        else:
            reply = message.context[-1].content
        message = message.model_dump_json()
        user_input = self.get_human_input(prompt=reply)
        if user_input == "exit":
            print(f"{'-'*80}\nUser session ended, session ID: {self.id.key}.")
            return
        _logger.info(f"User message next: {UserMessage(content=user_input, source='User')}")
        message = json.loads(message)
        _logger.info(f"message after load_json:{message}")
        if isinstance(message['context'], list):
            message['context'].append(UserMessage(content=user_input, source="User"))      
        else:
            print("Error: 'context' is not a list!")
        await self.publish_message(
            UserTask(context=message['context']), topic_id=TopicId(message['reply_to_topic_type'], source=self.id.key)
        )


    @message_handler
    async def handle_groupchat_message(self, message: GroupChatResponse, ctx: MessageContext) -> None:
        _logger.info(f"Group Chat Agent response: {message.context[-1].content}")
        if is_json(message.context[-1].content):
            reply = json.loads(message.context[-1].content)["response"]
        else:
            reply = message.context[-1].content
        message = message.model_dump_json()
        # Get the user's input after receiving a response from an agent.
        user_input = self.get_human_input(prompt=reply)
        if user_input == "exit":
            print(f"{'-'*80}\nUser session ended, session ID: {self.id.key}.")
            return
        _logger.info(f"User message next: {UserMessage(content=user_input, source='User')}")
        message = json.loads(message)
        if isinstance(message['context'], list):
            message['context'].append(UserMessage(content=user_input, source="User"))      
        else:
            print("Error: 'context' is not a list!")
        await self.publish_message(
            TransferMessage(context=message['context'], reply_to_topic_type=message['reply_to_topic_type']),
            topic_id=TopicId(message['reply_to_group_chat'], source=self.id.key),
        ) 
