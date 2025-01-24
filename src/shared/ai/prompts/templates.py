from typing import Dict, Optional
from .base import PromptTemplate

class PromptTemplateManager:
    """提示詞模板管理器"""
    
    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """註冊默認模板"""
        self.register_template(
            PromptTemplate(
                name="chat",
                template="你是一個有幫助的助手。\n\n用戶: {user_input}\n助手:",
                variables=["user_input"],
                description="基礎對話模板"
            )
        )
        
        self.register_template(
            PromptTemplate(
                name="image_analysis",
                template="請描述這張圖片的內容，包括：\n1. 主要物體\n2. 場景描述\n3. 關鍵細節",
                variables=[],
                description="圖片分析模板"
            )
        )
    
    def register_template(self, template: PromptTemplate):
        """註冊模板"""
        self._templates[template.name] = template
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """獲取模板"""
        return self._templates.get(name)
    
    def remove_template(self, name: str):
        """移除模板"""
        if name in self._templates:
            del self._templates[name] 