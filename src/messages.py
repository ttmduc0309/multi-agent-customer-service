from typing import List
from autogen_core.components.models import (
    LLMMessage,
)
from pydantic import BaseModel

class UserLogin(BaseModel):
    pass


class UserTask(BaseModel):
    context: List[LLMMessage]


class AgentResponse(BaseModel):
    reply_to_topic_type: str
    context: List[LLMMessage]

class GroupChatMessage(BaseModel):
    context: List[LLMMessage]

class GroupChatResponse(BaseModel):
    reply_to_topic_type: str
    reply_to_group_chat:str
    context: List[LLMMessage]

class GroupChatAgentResponse(BaseModel):
    reply_to_topic_type: str
    context: List[LLMMessage]

class RequestAgent(BaseModel):
    agent_type: str

class TransferMessage(BaseModel):
    reply_to_topic_type: str
    context: List[LLMMessage]