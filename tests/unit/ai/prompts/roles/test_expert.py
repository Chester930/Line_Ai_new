import pytest
from src.shared.ai.prompts.roles.expert import ExpertPrompt
from src.shared.ai.prompts.base import PromptContext

@pytest.fixture
def expert_prompt():
    return ExpertPrompt(domain="人工智能")

def test_expert_initialization(expert_prompt):
    """測試專家初始化"""
    assert expert_prompt.domain == "人工智能"
    assert isinstance(expert_prompt.expertise, list)
    assert isinstance(expert_prompt.credentials, list)

def test_expertise_management(expert_prompt):
    """測試專業知識管理"""
    expert_prompt.add_expertise("機器學習算法")
    expert_prompt.add_expertise("深度學習模型")
    
    prompt = expert_prompt.build(user_input="解釋神經網絡")
    assert "機器學習算法" in prompt
    assert "深度學習模型" in prompt

def test_credential_management(expert_prompt):
    """測試資歷管理"""
    expert_prompt.add_credential("10年研究經驗")
    expert_prompt.add_credential("發表50篇論文")
    
    prompt = expert_prompt.build(user_input="你的背景是什麼?")
    assert "10年研究經驗" in prompt
    assert "發表50篇論文" in prompt

def test_context_integration(expert_prompt):
    """測試上下文整合"""
    expert_prompt.add_context(
        PromptContext(role="user", content="什麼是機器學習?")
    )
    expert_prompt.add_context(
        PromptContext(role="expert", content="機器學習是...")
    )
    
    prompt = expert_prompt.build(user_input="深度學習呢?")
    assert "什麼是機器學習?" in prompt
    assert "機器學習是..." in prompt
    assert "深度學習呢?" in prompt

def test_empty_expert_prompt(expert_prompt):
    """測試空專家提示詞"""
    prompt = expert_prompt.build(user_input="你好")
    assert "該領域的一般知識" in prompt
    assert "多年實踐經驗" in prompt 