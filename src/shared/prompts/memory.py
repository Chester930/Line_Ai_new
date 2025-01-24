from typing import Dict, List, Optional
from .base import BasePromptManager, Prompt
from ..utils.logger import logger

class MemoryPromptManager(BasePromptManager):
    """記憶體提示詞管理器"""
    
    def __init__(self):
        self._prompts: Dict[str, Prompt] = {}
    
    async def get_prompt(self, name: str) -> Optional[Prompt]:
        """獲取提示詞"""
        return self._prompts.get(name)
    
    async def save_prompt(self, prompt: Prompt) -> bool:
        """保存提示詞"""
        try:
            self._prompts[prompt.name] = prompt
            logger.info(f"已保存提示詞: {prompt.name}")
            return True
        except Exception as e:
            logger.error(f"保存提示詞失敗: {str(e)}")
            return False
    
    async def delete_prompt(self, name: str) -> bool:
        """刪除提示詞"""
        try:
            if name in self._prompts:
                del self._prompts[name]
                logger.info(f"已刪除提示詞: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"刪除提示詞失敗: {str(e)}")
            return False
    
    async def list_prompts(
        self,
        tags: Optional[List[str]] = None
    ) -> List[Prompt]:
        """列出提示詞"""
        if not tags:
            return list(self._prompts.values())
        
        return [
            prompt for prompt in self._prompts.values()
            if any(tag in prompt.tags for tag in tags)
        ] 