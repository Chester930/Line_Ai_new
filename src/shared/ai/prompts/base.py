from typing import Dict, List, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class PromptContext:
    """提示詞上下文"""
    role: str
    content: str
    metadata: Dict = field(default_factory=dict)

@dataclass
class PromptTemplate:
    """提示詞模板"""
    name: str
    template: str
    variables: List[str] = field(default_factory=list)
    description: str = ""
    
    def format(self, **kwargs) -> str:
        """格式化提示詞"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"缺少必要的變量: {e}")

class BasePrompt(ABC):
    """基礎提示詞類"""
    
    def __init__(self, template: PromptTemplate):
        self.template = template
        self.contexts: List[PromptContext] = []
    
    def add_context(self, context: PromptContext):
        """添加上下文"""
        self.contexts.append(context)
    
    def clear_context(self):
        """清除上下文"""
        self.contexts.clear()
    
    @abstractmethod
    def build(self, **kwargs) -> str:
        """構建完整提示詞"""
        pass
    
    def get_recent_context(self, limit: int = 5) -> List[PromptContext]:
        """獲取最近的上下文"""
        return self.contexts[-limit:] if self.contexts else [] 