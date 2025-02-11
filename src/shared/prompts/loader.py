import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .base import Prompt
from ..utils.logger import logger

class PromptLoader:
    """提示詞加載器"""
    
    @staticmethod
    async def load_from_file(file_path: Path) -> List[Prompt]:
        """從文件加載提示詞"""
        try:
            if not file_path.exists():
                logger.error(f"提示詞文件不存在: {file_path}")
                return []
            
            # 讀取 YAML 文件
            data = yaml.safe_load(file_path.read_text())
            if not isinstance(data, dict):
                raise ValueError("無效的提示詞文件格式")
            
            prompts = []
            for name, config in data.items():
                try:
                    prompt = Prompt(
                        name=name,
                        content=config["content"],
                        description=config.get("description"),
                        tags=config.get("tags", []),
                        variables=config.get("variables", {})
                    )
                    prompts.append(prompt)
                except Exception as e:
                    logger.error(f"加載提示詞失敗 {name}: {str(e)}")
            
            logger.info(f"已加載 {len(prompts)} 個提示詞")
            return prompts
            
        except Exception as e:
            logger.error(f"加載提示詞文件失敗: {str(e)}")
            return []
    
    @staticmethod
    async def load_from_directory(
        directory: Path,
        pattern: str = "*.yml"
    ) -> List[Prompt]:
        """從目錄加載提示詞"""
        prompts = []
        try:
            # 遍歷目錄中的所有 YAML 文件
            for file_path in directory.glob(pattern):
                prompts.extend(
                    await PromptLoader.load_from_file(file_path)
                )
            return prompts
            
        except Exception as e:
            logger.error(f"加載提示詞目錄失敗: {str(e)}")
            return prompts 