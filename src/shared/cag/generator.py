from typing import Dict, Optional
from dataclasses import dataclass
import logging
from .exceptions import GenerationError
from ..ai.base import BaseAIModel
from ..ai.models.gemini import GeminiModel  # 移除 GeminiConfig

# 在文件頂部添加
logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    """生成配置"""
    # Gemini 模型不需要任何生成參數
    pass

class ResponseGenerator:
    """回應生成器"""
    def __init__(self, model: BaseAIModel):
        self.model = model
        self.config = GenerationConfig()  # 添加默認配置
    
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        **kwargs
    ) -> str:  # 改為直接返回字符串
        """生成回應"""
        try:
            # 準備生成參數
            params = self._prepare_params(kwargs)
            
            # 生成回應
            response = await self.model.generate(
                prompt=prompt,
                context=context,
                **params
            )
            
            return response.content  # 直接返回內容
            
        except Exception as e:
            logger.error(f"生成回應失敗: {str(e)}")
            raise GenerationError(f"生成回應失敗: {str(e)}")
    
    def _prepare_params(self, override_params: Dict) -> Dict:
        """準備生成參數"""
        # Gemini 模型不需要任何生成參數
        return {} 