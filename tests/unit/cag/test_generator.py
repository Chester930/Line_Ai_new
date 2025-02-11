import pytest
from datetime import datetime
from src.shared.cag.generator import ResponseGenerator, GenerationConfig, GenerationResult
from tests.mocks.model_manager import MockModelManager

@pytest.mark.asyncio
class TestResponseGenerator:
    async def test_generate_response(self):
        # 創建模擬的模型管理器
        model_manager = MockModelManager()
        generator = ResponseGenerator(model_manager)
        
        result = await generator.generate("Hello")
        
        assert isinstance(result, GenerationResult)
        assert isinstance(result.content, str)
        assert isinstance(result.created_at, datetime)
        assert "model" in result.metadata
    
    async def test_generation_with_context(self):
        model_manager = MockModelManager()
        generator = ResponseGenerator(model_manager)
        
        context = [
            {"role": "user", "content": "Previous message"}
        ]
        
        result = await generator.generate("Hello", context=context)
        assert result.content != ""
    
    async def test_custom_config(self):
        model_manager = MockModelManager()
        config = GenerationConfig(
            max_tokens=500,
            temperature=0.5
        )
        generator = ResponseGenerator(model_manager, config)
        
        result = await generator.generate("Test")
        assert result.metadata["params"]["max_tokens"] == 500
        assert result.metadata["params"]["temperature"] == 0.5 