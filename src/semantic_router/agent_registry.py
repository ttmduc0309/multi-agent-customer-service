from .components import AgentRegistryBase
from ..constants import *

class MockAgentRegistry(AgentRegistryBase):
    def __init__(self):
        self.agents = {
            "ERR_ACCOUNT": ERR_ACCOUNT_TOPIC_TYPE, 
            "OTHER": OTHER_TOPIC_TYPE
            }

    async def get_agent(self, intent: str) -> str:
        return self.agents[intent]
    
    async def get_all_agents(self) -> list:
        return list(self.agents.keys())
    

class AnotherAgentRegistry(AgentRegistryBase):
    def __init__(self):
        self.agents = {
            "ERR_ACCOUNT": ACCOUNT_TOPIC_TYPE, 
            "OTHER": OTHER_TOPIC_TYPE
            }

    async def get_agent(self, intent: str) -> str:
        return self.agents[intent]
    
    async def get_all_agents(self) -> list:
        return list(self.agents.keys())