import json
from pathlib import Path
from typing import Dict, Optional
from .base import BasePrompt, PromptContext
from .basic import BasicPrompt, SystemPrompt, UserPrompt
from ..utils.logger import logger

class PromptManager:
    """提示詞管理器"""
    
    def __init__(self, prompt_dir: Path):
        self.prompt_dir = prompt_dir
        self.prompts: Dict[str, BasePrompt] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """載入提示詞"""
        try:
            # 確保目錄存在
            self.prompt_dir.mkdir(parents=True, exist_ok=True)
            
            # 載入所有 JSON 文件
            for file_path in self.prompt_dir.glob("*.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    prompt_type = data.get("type", "basic")
                    template = data.get("template")
                    
                    if not template:
                        continue
                        
                    # 創建提示詞實例
                    prompt = self._create_prompt(prompt_type, template)
                    if prompt and prompt.validate():
                        self.prompts[file_path.stem] = prompt
                        
            logger.info(f"已載入 {len(self.prompts)} 個提示詞模板")
            
        except Exception as e:
            logger.error(f"載入提示詞失敗: {str(e)}")
    
    def _create_prompt(
        self,
        prompt_type: str,
        template: str
    ) -> Optional[BasePrompt]:
        """創建提示詞實例"""
        try:
            if prompt_type == "system":
                return SystemPrompt(template)
            elif prompt_type == "user":
                return UserPrompt(template)
            else:
                return BasicPrompt(template)
                
        except Exception as e:
            logger.error(f"創建提示詞失敗: {str(e)}")
            return None
    
    def get_prompt(
        self,
        prompt_id: str,
        context: PromptContext
    ) -> Optional[str]:
        """獲取格式化的提示詞"""
        try:
            prompt = self.prompts.get(prompt_id)
            if not prompt:
                return None
                
            return prompt.format(context)
            
        except Exception as e:
            logger.error(f"格式化提示詞失敗: {str(e)}")
            return None
    
    def add_prompt(
        self,
        prompt_id: str,
        template: str,
        prompt_type: str = "basic"
    ) -> bool:
        """添加提示詞"""
        try:
            # 創建提示詞實例
            prompt = self._create_prompt(prompt_type, template)
            if not prompt or not prompt.validate():
                return False
                
            # 保存到文件
            file_path = self.prompt_dir / f"{prompt_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "type": prompt_type,
                    "template": template
                }, f, ensure_ascii=False, indent=2)
                
            # 添加到內存
            self.prompts[prompt_id] = prompt
            return True
            
        except Exception as e:
            logger.error(f"添加提示詞失敗: {str(e)}")
            return False 