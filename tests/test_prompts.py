import pytest
from src.shared.ai.prompts.base import BasePrompt
from src.shared.ai.prompts.roles import AssistantPrompt, ExpertPrompt
from src.shared.ai.prompts.templates import PromptTemplate
from src.shared.config.base import ConfigManager

class TestPromptSystem:
    @pytest.fixture
    def config(self):
        """配置測試夾具"""
        config = ConfigManager()
        config.set("PROMPT_TEMPLATES", {
            "assistant": "You are a helpful assistant. {context}",
            "expert": "You are an expert in {domain}. {context}"
        })
        return config
        
    def test_base_prompt(self, config):
        """測試基礎提示詞"""
        class TestPrompt(BasePrompt):
            def build(self, context: str) -> str:
                return f"Test prompt: {context}"
                
        prompt = TestPrompt(config)
        result = prompt.build("Hello")
        assert result == "Test prompt: Hello"
        
    def test_assistant_prompt(self, config):
        """測試助手提示詞"""
        prompt = AssistantPrompt(config)
        result = prompt.build("How can I help you?")
        assert "helpful assistant" in result.lower()
        assert "How can I help you?" in result
        
    def test_expert_prompt(self, config):
        """測試專家提示詞"""
        prompt = ExpertPrompt(config)
        result = prompt.build(
            context="What is Python?",
            domain="programming"
        )
        assert "expert" in result.lower()
        assert "programming" in result
        assert "What is Python?" in result
        
    def test_prompt_template(self, config):
        """測試提示詞模板"""
        template = PromptTemplate(
            template="{role}: {message}",
            config=config
        )
        
        result = template.format(
            role="Assistant",
            message="Hello"
        )
        assert result == "Assistant: Hello"
        
    def test_template_validation(self, config):
        """測試模板驗證"""
        with pytest.raises(ValueError):
            PromptTemplate(template="", config=config)
            
        with pytest.raises(KeyError):
            template = PromptTemplate(
                template="{invalid}",
                config=config
            )
            template.format()
            
    def test_dynamic_prompt_generation(self, config):
        """測試動態提示詞生成"""
        class DynamicPrompt(BasePrompt):
            def build(self, **kwargs) -> str:
                role = kwargs.get("role", "assistant")
                style = kwargs.get("style", "friendly")
                return f"A {style} {role}"
                
        prompt = DynamicPrompt(config)
        
        result1 = prompt.build(role="teacher", style="professional")
        assert result1 == "A professional teacher"
        
        result2 = prompt.build(role="friend", style="casual")
        assert result2 == "A casual friend"
        
    def test_prompt_chaining(self, config):
        """測試提示詞鏈接"""
        system_prompt = "System: {message}"
        user_prompt = "User: {message}"
        assistant_prompt = "Assistant: {message}"
        
        chain = [
            PromptTemplate(system_prompt, config),
            PromptTemplate(user_prompt, config),
            PromptTemplate(assistant_prompt, config)
        ]
        
        messages = [
            {"message": "Initialize"},
            {"message": "Hello"},
            {"message": "Hi there"}
        ]
        
        result = "\n".join(
            template.format(**msg)
            for template, msg in zip(chain, messages)
        )
        
        assert "System: Initialize" in result
        assert "User: Hello" in result
        assert "Assistant: Hi there" in result
        
    def test_prompt_context_management(self, config):
        """測試提示詞上下文管理"""
        class ContextPrompt(BasePrompt):
            def __init__(self, config):
                super().__init__(config)
                self.context = []
                
            def add_context(self, message: str):
                self.context.append(message)
                
            def build(self, message: str) -> str:
                context = "\n".join(self.context)
                return f"Context:\n{context}\nCurrent: {message}"
                
        prompt = ContextPrompt(config)
        prompt.add_context("Previous message 1")
        prompt.add_context("Previous message 2")
        
        result = prompt.build("Current message")
        
        assert "Previous message 1" in result
        assert "Previous message 2" in result
        assert "Current message" in result 