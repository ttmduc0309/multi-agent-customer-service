import logging

from ..semantic_router.components import AgentRegistryBase, IntentClassifierBase, TerminationMessage, UserProxyMessage
from autogen_core.application.logging import TRACE_LOGGER_NAME
from autogen_core.base import MessageContext
from autogen_core.components import DefaultTopicId, RoutedAgent, default_subscription, message_handler
from ..messages import *
from autogen_core.components.models import (
    UserMessage,
)
import chainlit as cl

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(f"{TRACE_LOGGER_NAME}.semantic_router")
logger.setLevel(logging.DEBUG)


@default_subscription
class SemanticRouterAgent(RoutedAgent):
    def __init__(self, name: str, agent_registry: AgentRegistryBase, intent_classifier: IntentClassifierBase) -> None:
        super().__init__("Semantic Router Agent")
        self._name = name
        self._registry = agent_registry
        self._classifier = intent_classifier

    # The User has sent a message that needs to be routed
    @message_handler
    async def route_to_agent(self, message: UserTask, ctx: MessageContext) -> None:
        assert ctx.topic_id is not None
        logger.debug(f"Received message from {message.context[-1].source}: {message.context[-1].content}")
        session_id = ctx.topic_id.source
        async with cl.Step(name=f"Classifying Intent") as step:
            step.input= message.context[-1]
            intent = await self._identify_intent(message.context[-1])
            step.output = intent
            # if self.validate_intent(intent):
            #     break
        agent = await self._find_agent(intent)
        async with cl.Step(name=f"Contacting {agent}"):
            await self.contact_agent(agent, message, session_id)

    ## Identify the intent of the user message
    async def _identify_intent(self, message: UserMessage) -> str:
        return await self._classifier.classify_intent(message)
            

    ## Use a lookup, search, or LLM to identify the most relevant agent for the intent
    async def _find_agent(self, intent: str) -> str:
        logger.debug(f"Identified intent: {intent}")
        try:
            agent = await self._registry.get_agent(intent)
            return agent
        except KeyError:
            logger.debug("No relevant agent found for intent: " + intent)
            return "termination"

    ## Forward user message to the appropriate agent, or end the thread.
    async def contact_agent(self, agent: str, message: UserTask, session_id: str) -> None:
        if agent == "termination":
            logger.debug("No relevant agent found")
            await self.publish_message(
                TerminationMessage(reason="No relevant agent found", content=message.content, source=self.type),
                DefaultTopicId(type="user_proxy", source=session_id),
            )
        else:
            logger.debug("Routing to agent: " + agent)
            await self.publish_message(
                message,
                DefaultTopicId(type=agent, source=session_id),
            )

    def validate_intent(self, intent: str) -> bool:
        if intent in self._registry.get_all_agents():
            return True
        else: return False
