from typing import List, Dict
from ..base import BasePrompt, PromptTemplate, PromptContext

class AssistantPrompt(BasePrompt):
    """助手角色提示詞"""
    
    def __init__(self, template: PromptTemplate = None):
        super().__init__(template or self._default_template())
        self.personality_traits: List[str] = []
        self.skills: List[str] = []
    
    def _default_template(self) -> PromptTemplate:
        """默認模板"""
        return PromptTemplate(
            name="assistant",
            template=(
                "你是一個專業的助手，具有以下特點：\n"
                "{traits}\n\n"
                "你擅長：\n"
                "{skills}\n\n"
                "當前對話：\n"
                "{context}\n\n"
                "用戶: {user_input}\n"
                "助手:"
            ),
            variables=["traits", "skills", "context", "user_input"]
        )
    
    def add_trait(self, trait: str):
        """添加性格特點"""
        self.personality_traits.append(trait)
    
    def add_skill(self, skill: str):
        """添加技能"""
        self.skills.append(skill)
    
    def build(self, **kwargs) -> str:
        """構建提示詞"""
        # 格式化性格特點
        traits = "\n".join(f"- {trait}" for trait in self.personality_traits)
        
        # 格式化技能
        skills = "\n".join(f"- {skill}" for skill in self.skills)
        
        # 格式化上下文
        context = "\n".join(
            f"{ctx.role}: {ctx.content}"
            for ctx in self.get_recent_context()
        )
        
        return self.template.format(
            traits=traits or "- 專業且有幫助",
            skills=skills or "- 一般對話",
            context=context,
            user_input=kwargs.get("user_input", "")
        ) 