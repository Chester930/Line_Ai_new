from typing import Dict, List, Optional
from .base import BasePrompt, PromptContext

class BasicPrompt(BasePrompt):
    """基本提示詞"""
    
    def format(self, context: PromptContext) -> str:
        """格式化提示詞"""
        # 替換基本變數
        prompt = self.template
        base_vars = {
            "user_id": context.user_id,
            "session_id": context.session_id,
            "language": context.language,
            "role": context.role
        }
        prompt = self._replace_variables(prompt, base_vars)
        
        # 替換自定義變數
        if context.variables:
            prompt = self._replace_variables(prompt, context.variables)
            
        return prompt
    
    def validate(self) -> bool:
        """驗證提示詞"""
        return bool(self.template and isinstance(self.template, str))

class SystemPrompt(BasicPrompt):
    """系統提示詞"""
    
    def format(self, context: PromptContext) -> str:
        """格式化系統提示詞"""
        context.role = "system"
        return super().format(context)

class UserPrompt(BasicPrompt):
    """用戶提示詞"""
    
    def format(self, context: PromptContext) -> str:
        """格式化用戶提示詞"""
        context.role = "user"
        return super().format(context) 