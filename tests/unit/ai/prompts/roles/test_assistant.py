import pytest
from src.shared.ai.prompts.roles.assistant import AssistantPrompt
from src.shared.ai.prompts.base import PromptContext

@pytest.fixture
def assistant_prompt():
    return AssistantPrompt()

def test_default_template(assistant_prompt):
    """測試默認模板"""
    assert assistant_prompt.template is not None
    assert "traits" in assistant_prompt.template.variables
    assert "skills" in assistant_prompt.template.variables

def test_trait_management(assistant_prompt):
    """測試特點管理"""
    assistant_prompt.add_trait("友善")
    assistant_prompt.add_trait("耐心")
    
    prompt = assistant_prompt.build(user_input="你好")
    assert "友善" in prompt
    assert "耐心" in prompt

def test_skill_management(assistant_prompt):
    """測試技能管理"""
    assistant_prompt.add_skill("問題解答")
    assistant_prompt.add_skill("資訊檢索")
    
    prompt = assistant_prompt.build(user_input="你好")
    assert "問題解答" in prompt
    assert "資訊檢索" in prompt

def test_context_integration(assistant_prompt):
    """測試上下文整合"""
    # 添加對話上下文
    assistant_prompt.add_context(
        PromptContext(role="user", content="你好")
    )
    assistant_prompt.add_context(
        PromptContext(role="assistant", content="很高興見到你")
    )
    
    prompt = assistant_prompt.build(user_input="請問你是誰?")
    assert "你好" in prompt
    assert "很高興見到你" in prompt
    assert "請問你是誰?" in prompt

def test_empty_prompt_building(assistant_prompt):
    """測試空提示詞構建"""
    prompt = assistant_prompt.build(user_input="你好")
    assert "專業且有幫助" in prompt  # 默認特點
    assert "一般對話" in prompt      # 默認技能 