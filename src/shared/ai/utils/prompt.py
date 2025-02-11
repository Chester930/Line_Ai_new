from typing import Dict, Any
from pathlib import Path
import yaml
from ...utils.logger import logger

class PromptManager:
    """提示詞管理器"""
    
    def __init__(self):
        self.prompts: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """從 YAML 文件加載提示詞"""
        try:
            prompt_file = Path('config/prompts.yaml')
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.prompts = yaml.safe_load(f)
                logger.info("提示詞加載成功")
            else:
                logger.warning("提示詞文件不存在")
        except Exception as e:
            logger.error(f"加載提示詞時發生錯誤: {str(e)}")
    
    def get_prompt(self, key: str, **kwargs) -> str:
        """獲取並格式化提示詞"""
        try:
            prompt_template = self.prompts.get(key)
            if not prompt_template:
                logger.warning(f"未找到提示詞: {key}")
                return ""
            
            return prompt_template.format(**kwargs)
        except Exception as e:
            logger.error(f"格式化提示詞時發生錯誤: {str(e)}")
            return ""
    
    def add_prompt(self, key: str, template: str) -> None:
        """添加新的提示詞"""
        self.prompts[key] = template
        logger.info(f"添加新提示詞: {key}")

# 全局提示詞管理器實例
prompt_manager = PromptManager() 