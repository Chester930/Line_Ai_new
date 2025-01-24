import pytest
from src.shared.ai.prompts.base import PromptTemplate, PromptContext, BasePrompt

class TestPrompt(BasePrompt):
    """測試用提示詞類"""
    def build(self, **kwargs) -> str:
        return self.template.format(**kwargs)

@pytest.fixture
def template():
    return PromptTemplate(
        name="test",
        template="Hello, {name}!",
        variables=["name"],
        description="Test template"
    )

@pytest.fixture
def prompt(template):
    return TestPrompt(template)

def test_prompt_template_format(template):
    """測試模板格式化"""
    result = template.format(name="World")
    assert result == "Hello, World!"
    
    # 測試缺少變量
    with pytest.raises(ValueError):
        template.format()

def test_prompt_context_management(prompt):
    """測試上下文管理"""
    context = PromptContext(role="user", content="test message")
    prompt.add_context(context)
    
    assert len(prompt.contexts) == 1
    assert prompt.contexts[0] == context
    
    prompt.clear_context()
    assert len(prompt.contexts) == 0

def test_recent_context_retrieval(prompt):
    """測試最近上下文獲取"""
    # 添加多個上下文
    for i in range(10):
        prompt.add_context(
            PromptContext(role="user", content=f"message {i}")
        )
    
    recent = prompt.get_recent_context(limit=5)
    assert len(recent) == 5
    assert recent[-1].content == "message 9" 