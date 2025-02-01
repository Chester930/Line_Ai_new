from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging
from .exceptions import GenerationError

# 在文件頂部添加
logger = logging.getLogger(__name__)

@dataclass
class GenerationConfig:
    """生成配置"""
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

@dataclass
class GenerationResult:
    """生成結果"""
    content: str
    metadata: Dict
    created_at: datetime

class ResponseGenerator:
    """回應生成器"""
    def __init__(self, model_manager, config: Optional[GenerationConfig] = None):
        self.model_manager = model_manager
        self.config = config or GenerationConfig()
    
    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict]] = None,
        **kwargs
    ) -> GenerationResult:
        """生成回應"""
        try:
            # 準備生成參數
            params = self._prepare_params(kwargs)
            
            # 獲取模型實例
            model = await self.model_manager.get_model()
            
            # 生成回應
            response = await model.generate(
                prompt=prompt,
                context=context,
                **params
            )
            
            # 封裝結果
            result = GenerationResult(
                content=response.text,
                metadata={
                    "model": model.name,
                    "params": params,
                    "usage": response.usage
                },
                created_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            # 記錄錯誤
            logger.error(f"Generation failed: {str(e)}")
            raise GenerationError(f"Failed to generate response: {str(e)}")
    
    def _prepare_params(self, override_params: Dict) -> Dict:
        """準備生成參數"""
        params = {
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "presence_penalty": self.config.presence_penalty,
            "frequency_penalty": self.config.frequency_penalty
        }
        
        # 使用傳入的參數覆蓋默認配置
        params.update(override_params)
        
        return params 