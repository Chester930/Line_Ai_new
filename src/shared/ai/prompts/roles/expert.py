from typing import List, Dict
from ..base import BasePrompt, PromptTemplate, PromptContext

class ExpertPrompt(BasePrompt):
    """專家角色提示詞"""
    
    def __init__(self, domain: str, template: PromptTemplate = None):
        super().__init__(template or self._default_template())
        self.domain = domain
        self.expertise: List[str] = []
        self.credentials: List[str] = []
    
    def _default_template(self) -> PromptTemplate:
        return PromptTemplate(
            name="expert",
            template=(
                "你是一位{domain}領域的專家，具有以下專業知識：\n"
                "{expertise}\n\n"
                "你的資歷包括：\n"
                "{credentials}\n\n"
                "當前對話：\n"
                "{context}\n\n"
                "用戶: {user_input}\n"
                "專家:"
            ),
            variables=["domain", "expertise", "credentials", "context", "user_input"]
        )
    
    def add_expertise(self, expertise: str):
        """添加專業知識"""
        self.expertise.append(expertise)
    
    def add_credential(self, credential: str):
        """添加資歷"""
        self.credentials.append(credential)
    
    def build(self, **kwargs) -> str:
        """構建提示詞"""
        expertise = "\n".join(f"- {exp}" for exp in self.expertise)
        credentials = "\n".join(f"- {cred}" for cred in self.credentials)
        context = "\n".join(
            f"{ctx.role}: {ctx.content}"
            for ctx in self.get_recent_context()
        )
        
        return self.template.format(
            domain=self.domain,
            expertise=expertise or "- 該領域的一般知識",
            credentials=credentials or "- 多年實踐經驗",
            context=context,
            user_input=kwargs.get("user_input", "")
        ) 