import pytest
from src.shared.ai.prompts.templates import PromptTemplateManager
from src.shared.ai.prompts.base import PromptTemplate

@pytest.fixture
def template_manager():
    return PromptTemplateManager()

def test_default_templates(template_manager):
    """測試默認模板"""
    assert template_manager.get_template("chat") is not None
    assert template_manager.get_template("image_analysis") is not None

def test_template_registration(template_manager):
    """測試模板註冊"""
    new_template = PromptTemplate(
        name="custom",
        template="Custom template: {var}",
        variables=["var"],
        description="Custom template"
    )
    
    template_manager.register_template(new_template)
    assert template_manager.get_template("custom") == new_template

def test_template_removal(template_manager):
    """測試模板移除"""
    template_manager.remove_template("chat")
    assert template_manager.get_template("chat") is None

def test_template_retrieval(template_manager):
    """測試模板獲取"""
    chat_template = template_manager.get_template("chat")
    assert chat_template.name == "chat"
    assert "user_input" in chat_template.variables 