from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class MockResponse:
    text: str
    usage: Dict[str, int]

class MockModelManager:
    def __init__(self, raise_error: bool = False):
        self.raise_error = raise_error
    
    async def get_model(self):
        if self.raise_error:
            raise Exception("Mock error")
        return MockModel()

class MockModel:
    def __init__(self):
        self.name = "mock_model"
    
    async def generate(self, prompt: str, context: Any = None, **kwargs) -> MockResponse:
        return MockResponse(
            text="This is a mock response",
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        ) 