from .components import IntentClassifierBase
from autogen_core.components.models import (
    ChatCompletionClient,
    SystemMessage,
    UserMessage,
)

class MockIntentClassifier(IntentClassifierBase):
    def __init__(
        self,
        system_message: SystemMessage,
        model_client: ChatCompletionClient,
    ) -> None:
        super().__init__()
        self._system_message = system_message
        self._model_client = model_client

    async def classify_intent(self, message: UserMessage) -> str:
        print(message)
        llm_result = await self._model_client.create(
            messages=[self._system_message] + [message],
        )
        return llm_result.content