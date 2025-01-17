import uuid
from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.base import TopicId
from autogen_core.components import TypeSubscription
from autogen_core.components.models import (
    SystemMessage,
)

from src.agents.base_agent import AIAgent
from src.agents.user_agent import UserAgent
from src.agents.group_chat_manager import GroupChatManager
from src.agents.group_chat_base_agent import GroupChatAIAgent
from src.agents.group_chat_auto_reply import GroupChatAutoReplyAgent
from src.constants import *
from src.tools.transfer_tools import *
from src.tools.tools import *
from src.messages import *
from src.prompts import *
from src.agents.semantic_router_agent import SemanticRouterAgent
from src.semantic_router.agent_registry import AnotherAgentRegistry
from src.semantic_router.intent_cls import MockIntentClassifier

from dotenv import load_dotenv, find_dotenv
from autogen_ext.models import OpenAIChatCompletionClient
from decouple import config
import asyncio

load_dotenv(find_dotenv())

runtime = SingleThreadedAgentRuntime()


model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    api_key=config("OPENAI_KEY"),
    base_url=config('API_BASE'),
)

# @cl.on_chat_start
# async def on_chat_start():
#   try:
async def main():
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
    # Add subscriptions for the user agent: it will receive messages published to its own topic only.
    await runtime.add_subscription(TypeSubscription(topic_type=user_topic_type, agent_type=user_agent_type.type))

    agent_registry = AnotherAgentRegistry()
    intent_classifier = MockIntentClassifier(system_message=SystemMessage(content=INTENT_CLS_PROMPT), model_client=model_client)
    await SemanticRouterAgent.register(
        runtime,
        type=router_topic_type,
        factory=lambda: SemanticRouterAgent(
            name="router",
            agent_registry=agent_registry, 
            intent_classifier=intent_classifier),
    )

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
    
    # Register the triage account agent.
    triage_account_agent_type = await GroupChatAIAgent.register(
        runtime,
        type=ERR_ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
        factory=lambda: GroupChatAIAgent(
            description="An agent for dealing with other problems.",
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
    # Add subscriptions for the issues and repairs agent: it will receive messages published to its own topic only.
    await runtime.add_subscription(
        TypeSubscription(topic_type=ERR_ACCOUNT_TOPIC_TYPE, agent_type=triage_account_agent_type.type)
    )

    # Register the simple account agent.
    simple_account_agent_type = await GroupChatAIAgent.register(
        runtime,
        type=SIMPLE_ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
        factory=lambda: GroupChatAIAgent(
            description="An agent for dealing with simple account problems.",
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
    # Add subscriptions for the issues and repairs agent: it will receive messages published to its own topic only.
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

    # Register the complex account agent.
    complex_account_agent_type = await GroupChatAIAgent.register(
        runtime,
        type=COMPLEX_ACCOUNT_TOPIC_TYPE,  # Using the topic type as the agent type.
        factory=lambda: GroupChatAIAgent(
            description="An agent for dealing with complex account problems.",
            system_message=SystemMessage(content=COMPLEX_ACCOUNT_PROMPT),
            model_client=model_client,
            tools=[
                save_login_fail_tool,
                update_login_fail_tool,
                save_forget_acc_tool,
                update_forget_acc_tool,
            ],
            delegate_tools=[
                transfer_to_account_triage_agent,
                transfer_to_account_oos
                ],
            agent_topic_type=COMPLEX_ACCOUNT_TOPIC_TYPE,
            user_topic_type=user_topic_type,
            group_chat_topic_type=ACCOUNT_TOPIC_TYPE,
        ),
    )
    # Add subscriptions for the issues and repairs agent: it will receive messages published to its own topic only.
    await runtime.add_subscription(
        TypeSubscription(topic_type=COMPLEX_ACCOUNT_TOPIC_TYPE, agent_type=complex_account_agent_type.type)
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

    # Start the runtime.
    runtime.start()

    # Create a new session for the user.
    session_id = str(uuid.uuid4())
    await runtime.publish_message(UserLogin(), topic_id=TopicId(user_topic_type, source=session_id))

    # Run until completion.
    await runtime.stop_when_idle()

if __name__ == "__main__":
    asyncio.run(main())
