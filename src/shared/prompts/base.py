from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from ..session.base import Message

@dataclass
class Prompt:
    """提示詞"""
    content: str
    name: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    variables: Dict[str, str] = field(default_factory=dict)
    
    def format(self, **kwargs) -> str:
        """格式化提示詞"""
        try:
            # 合併默認變量和傳入的變量
            variables = self.variables.copy()
            variables.update(kwargs)
            return self.content.format(**variables)
        except KeyError as e:
            raise PromptError(f"缺少必要的變量: {str(e)}")
        except Exception as e:
            raise PromptError(f"格式化提示詞失敗: {str(e)}")

class BasePromptManager(ABC):
    """提示詞管理器基類"""
    
    @abstractmethod
    async def get_prompt(self, name: str) -> Optional[Prompt]:
        """獲取提示詞"""
        pass
    
    @abstractmethod
    async def save_prompt(self, prompt: Prompt) -> bool:
        """保存提示詞"""
        pass
    
    @abstractmethod
    async def delete_prompt(self, name: str) -> bool:
        """刪除提示詞"""
        pass
    
    @abstractmethod
    async def list_prompts(
        self,
        tags: Optional[List[str]] = None
    ) -> List[Prompt]:
        """列出提示詞"""
        pass
    
    async def format_messages(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None
    ) -> List[Message]:
        """格式化消息列表"""
        formatted = []
        
        # 添加系統提示詞
        if system_prompt:
            formatted.append(Message(
                role="system",
                content=system_prompt
            ))
        
        # 添加對話消息
        formatted.extend(messages)
        
        return formatted

class PromptError(Exception):
    """提示詞錯誤"""
    pass 