from autogen_core.components.tools import FunctionTool
from ..constants import *

def transfer_back_to_router_agent() -> str:
    return router_topic_type

def transfer_to_complex_agent_account() -> str:
    return COMPLEX_ACCOUNT_TOPIC_TYPE

def transfer_to_simple_agent_account() -> str:
    return SIMPLE_ACCOUNT_TOPIC_TYPE

def transfer_to_password_agent_account() -> str:
    return PASSWORD_ACCOUNT_TOPIC_TYPE

def transfer_to_triage_agent_account() -> str:
    return ERR_ACCOUNT_TOPIC_TYPE

def transfer_to_account_oos_agent() -> str:
    return OOS_ACCOUNT_TOPIC_TYPE


transfer_back_to_router_tool = FunctionTool(
    transfer_back_to_router_agent, description="Change the topic to the router agent."
)

transfer_to_account_complex_agent = FunctionTool(
    transfer_to_complex_agent_account, description="Change the topic to the complex account."
)

transfer_to_account_simple_agent = FunctionTool(
    transfer_to_simple_agent_account, description="Change the topic to the simple account."
)

transfer_to_account_password_agent = FunctionTool(
    transfer_to_password_agent_account, description="Change the topic to the password account."
)

transfer_to_account_triage_agent = FunctionTool(
    transfer_to_triage_agent_account, description="Change the topic to the complex account."
)

transfer_to_account_oos = FunctionTool(
    transfer_to_account_oos_agent, description="Change the topic to the oos account."
)