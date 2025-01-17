import uuid
import asyncio
import chainlit as cl
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict

from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.base import TopicId
from autogen_core.components import TypeSubscription
from autogen_core.components.models import SystemMessage

from src.agents.base_agent import AIAgent
from src.agents.user_agent import UserAgent
from src.constants import *
from src.tools.transfer_tools import *
from src.tools.tools import *
from src.messages import *
from src.prompts import *
from src.agents.semantic_router_agent import SemanticRouterAgent
from src.semantic_router.agent_registry import AnotherAgentRegistry
from src.semantic_router.intent_cls import MockIntentClassifier
from src.intervention_handler.handoff_intervention import HandoffHandler

from dotenv import load_dotenv, find_dotenv
from autogen_ext.models import OpenAIChatCompletionClient
from decouple import config

from src.agents.group_chat_manager import GroupChatManager
from src.agents.group_chat_base_agent import GroupChatAIAgent
from src.agents.group_chat_auto_reply import GroupChatAutoReplyAgent

class MessageHandler:
    def __init__(self):
        self.response: Dict[str, str] = {}
    
    async def handle_agent_response(self, message: AgentResponse):
        try:
            # Ensure that the response content is not empty before sending it
            if hasattr(message, 'content') and message.content.strip():
                await cl.Message(content=str(message.content)).send()
            else:
                logger.warning("Agent response is empty.")
        except Exception as e:
            logger.error(f"Error handling agent response: {e}", exc_info=True)

message_handler = MessageHandler()

# Configure logging
def setup_logging():
    # Create a logger
    logger = logging.getLogger('agent_runtime')
    logger.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create file handler
    file_handler = RotatingFileHandler(
        'agent_runtime.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)

    # Create formatters
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

    # Add formatters to handlers
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Global logger
logger = setup_logging()

# Load environment variables
load_dotenv(find_dotenv())

# Initialize runtime and handlers
handoff_handler = HandoffHandler()
runtime = SingleThreadedAgentRuntime(intervention_handlers=[handoff_handler])

# Initialize model client
model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=config("OPENAI_KEY"),
    base_url=config('API_BASE'),
)

@cl.on_chat_start
async def on_chat_start():
    logger.info("Chat started: Initializing agents and runtime")
    try:
        # runtime.register_message_handler(message_handler.handle_agent_response)
        # Register the user agent.
        user_agent_type = await UserAgent.register(
            runtime,
            type=user_topic_type,
            factory=lambda: UserAgent(
                description="A user agent.",
                user_topic_type=user_topic_type,
                agent_topic_type=router_topic_type,  # Start with the triage agent.
            ),
        )
        logger.info(f"Registered User Agent: {user_agent_type}")

        # Add subscriptions for the user agent
        await runtime.add_subscription(TypeSubscription(topic_type=user_topic_type, agent_type=user_agent_type.type))
        logger.info("Added subscription for User Agent")

        # Initialize agent registry and intent classifier
        agent_registry = AnotherAgentRegistry()
        intent_classifier = MockIntentClassifier(
            system_message=SystemMessage(content=INTENT_CLS_PROMPT), 
            model_client=model_client
        )
        logger.info("Initialized Agent Registry and Intent Classifier")

        # Register Semantic Router Agent
        # await SemanticRouterAgent.register(
        #     runtime,
        #     type=router_topic_type,
        #     factory=lambda: SemanticRouterAgent(
        #         name="router",
        #         agent_registry=agent_registry, 
        #         intent_classifier=intent_classifier
        #     ),
        # )
        semantic_router = await SemanticRouterAgent.register(
            runtime,
            type=router_topic_type,
            factory=lambda: SemanticRouterAgent(
                name="router",
                agent_registry=agent_registry, 
                intent_classifier=intent_classifier
            ),
        )
        await runtime.add_subscription(
            TypeSubscription(topic_type=router_topic_type, agent_type=semantic_router.type)
        )
        
        logger.info("Registered Semantic Router Agent")

    # Register the GroupChat agent.
        group_chat_type = await GroupChatManager.register(
            runtime,
            type=ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
            factory=lambda: GroupChatManager(
                participant_topic_types=[ERR_ACCOUNT_TOPIC_TYPE,SIMPLE_ACCOUNT_TOPIC_TYPE,COMPLEX_ACCOUNT_TOPIC_TYPE,OOS_ACCOUNT_TOPIC_TYPE,PASSWORD_ACCOUNT_TOPIC_TYPE],
                uc_triage_type=ERR_ACCOUNT_TOPIC_TYPE,
                group_chat_topic_type=ACCOUNT_TOPIC_TYPE,
                user_topic_type=user_topic_type,
            ),
        )
        # Add subscriptions for the issues and repairs agent: it will receive messages published to its own topic only.
        await runtime.add_subscription(
            TypeSubscription(topic_type=ACCOUNT_TOPIC_TYPE, agent_type=group_chat_type.type)
        )

        # Register the Account agent.
        account_triage_agent_type = await GroupChatAIAgent.register(
            runtime,
            type=ERR_ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
            factory=lambda: GroupChatAIAgent(
                description="An agent for dealing with accounts.",
                system_message=SystemMessage(content=ACCOUNT_TRIAGE_PROMPT),
                model_client=model_client,
                tools=[],
                delegate_tools=[
                    transfer_back_to_router_tool,
                    transfer_to_account_complex_agent,
                    transfer_to_account_simple_agent,
                    transfer_to_account_password_agent,
                ],
                agent_topic_type=ERR_ACCOUNT_TOPIC_TYPE,
                user_topic_type=user_topic_type,
                group_chat_topic_type=ACCOUNT_TOPIC_TYPE,
            ),
        )

        # Add subscriptions for the account agent: it will receive messages published to its own topic only.
        await runtime.add_subscription(
            TypeSubscription(topic_type=ERR_ACCOUNT_TOPIC_TYPE, agent_type=account_triage_agent_type.type)
        )

        # Register the Complex Account agent.
        complex_account_agent_type = await GroupChatAIAgent.register(
            runtime,
            type=COMPLEX_ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
            factory=lambda: GroupChatAIAgent(
                description="An agent for dealing with complex task in the account UC.",
                system_message=SystemMessage(content=COMPLEX_ACCOUNT_PROMPT),
                model_client=model_client,
                tools=[
                    save_login_fail_tool,
                    update_login_fail_tool,
                    save_forget_acc_tool,
                    update_forget_acc_tool,
                ],
                delegate_tools=[
                    # transfer_to_account_triage_agent,
                    transfer_to_account_oos
                    ],
                agent_topic_type=COMPLEX_ACCOUNT_TOPIC_TYPE,
                user_topic_type=user_topic_type,
                group_chat_topic_type=ACCOUNT_TOPIC_TYPE,
            ),
        )

        # Add subscriptions for the Complex account agent: it will receive messages published to its own topic only.
        await runtime.add_subscription(
            TypeSubscription(topic_type=COMPLEX_ACCOUNT_TOPIC_TYPE, agent_type=complex_account_agent_type.type)
        )

        # Register the Simple Account agent.
        simple_account_agent_type = await GroupChatAIAgent.register(
            runtime,
            type=SIMPLE_ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
            factory=lambda: AIAgent(
                description="An agent for dealing with simple task in the account UC.",
                system_message=SystemMessage(content=SIMPLE_ACCOUNT_PROMPT),
                model_client=model_client,
                tools=[],
                delegate_tools=[
                    transfer_to_account_triage_agent,
                    transfer_to_account_oos
                    ],
                agent_topic_type=SIMPLE_ACCOUNT_TOPIC_TYPE,
                user_topic_type=user_topic_type,
                group_chat_topic_type=ACCOUNT_TOPIC_TYPE,
            ),
        )

        # Add subscriptions for the Complex account agent: it will receive messages published to its own topic only.
        await runtime.add_subscription(
            TypeSubscription(topic_type=SIMPLE_ACCOUNT_TOPIC_TYPE, agent_type=simple_account_agent_type.type)
        )
        # Register the simple account agent.
        password_account_agent_type = await GroupChatAIAgent.register(
            runtime,
            type=PASSWORD_ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
            factory=lambda: GroupChatAIAgent(
                description="An agent for dealing with password account problems.",
                system_message=SystemMessage(content=PASSWORD_PROMPT),
                model_client=model_client,
                tools=[],
                delegate_tools=[
                    transfer_to_account_triage_agent,
                    transfer_to_account_oos
                    ],
                agent_topic_type=PASSWORD_ACCOUNT_TOPIC_TYPE,
                user_topic_type=user_topic_type,
                group_chat_topic_type=ACCOUNT_TOPIC_TYPE,
            ),
        )
        # Add subscriptions for the issues and repairs agent: it will receive messages published to its own topic only.
        await runtime.add_subscription(
            TypeSubscription(topic_type=PASSWORD_ACCOUNT_TOPIC_TYPE, agent_type=password_account_agent_type.type)
        )
        # Register the other agent.
        other_agent_type = await AIAgent.register(
            runtime,
            type=OTHER_TOPIC_TYPE,  # Using the topic type as the agent type.
            factory=lambda: AIAgent(
                description="An agent for dealing with other problems.",
                system_message=SystemMessage(content=OTHER_AGENT_PROMPT),
                model_client=model_client,
                tools=[],
                delegate_tools=[transfer_back_to_router_tool],
                agent_topic_type=OTHER_TOPIC_TYPE,
                user_topic_type=user_topic_type,
            ),
        )
        # Add subscriptions for the issues and repairs agent: it will receive messages published to its own topic only.
        await runtime.add_subscription(
            TypeSubscription(topic_type=OTHER_TOPIC_TYPE, agent_type=other_agent_type.type)
        )
        
        # Register the oos agent.
        oos_account_agent_type = await GroupChatAutoReplyAgent.register(
            runtime,
            type=OOS_ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
            factory=lambda: GroupChatAutoReplyAgent(
                description="An agent for dealing oos problem of account.",
                agent_topic_type=OOS_ACCOUNT_TOPIC_TYPE,
                uc_triage_type=ERR_ACCOUNT_TOPIC_TYPE,
                user_topic_type=user_topic_type,
                group_chat_topic_type=ACCOUNT_TOPIC_TYPE,
            ),
        )
        # Add subscriptions for the issues and repairs agent: it will receive messages published to its own topic only.
        await runtime.add_subscription(
            TypeSubscription(topic_type=OOS_ACCOUNT_TOPIC_TYPE, agent_type=oos_account_agent_type.type)
        )

        # Start the runtime
        runtime.start()
        logger.info("Runtime started successfully")

        # Create a new session for the user
        session_id = str(uuid.uuid4())
        await runtime.publish_message(UserLogin(), topic_id=TopicId(user_topic_type, source=session_id))
        logger.info(f"Created new user session: {session_id}")

        # Store session_id in Chainlit's user session
        cl.user_session.set("session_id", session_id)
        cl.user_session.set(user_agent_type, user_agent_type)
        cl.user_session.set(semantic_router, semantic_router)
        cl.user_session.set(account_triage_agent_type, account_triage_agent_type)
        cl.user_session.set(complex_account_agent_type, complex_account_agent_type)
        cl.user_session.set(other_agent_type, other_agent_type)
        cl.user_session.set(oos_account_agent_type, oos_account_agent_type)
        cl.user_session.set(simple_account_agent_type, simple_account_agent_type)
        cl.user_session.set(group_chat_type, group_chat_type)

    except Exception as e:
        logger.error(f"Error during chat start: {e}", exc_info=True)
        await cl.Message(content=f"An error occurred: {str(e)}").send()

if __name__ == "__main__":
    logger.info("Starting Chainlit application")
    cl.run()

