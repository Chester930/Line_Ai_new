import google.generativeai as genai
import logging
from typing import Optional, Dict, Any, List
from ...exceptions import ModelError, GenerationError, ValidationError
from ...utils.logger import logger
from ..base import BaseAIModel, ModelResponse
import asyncio

class GeminiModel(BaseAIModel):
    """Gemini 模型實現"""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-pro",
        **kwargs
    ):
        """初始化 Gemini 模型
        
        Args:
            api_key: API 金鑰
            model_name: 模型名稱
            **kwargs: 其他配置參數
        """
        super().__init__(api_key=api_key)  # 正確傳遞 api_key 給父類
        self.model_name = model_name
        self.config = kwargs.get('config', {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.95,
            "top_k": 40
        })  # 從 kwargs 獲取配置
        self.enable_cache = False
        self.rate_limit = None
        self._cache = {}
        
        try:
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                **self.config  # 使用配置參數
            )
        except Exception as e:
            logger.error(f"初始化 Gemini 模型失敗: {str(e)}")
            raise ModelError(f"初始化失敗: {str(e)}")
    
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """生成回應"""
        try:
            # 添加快取處理
            cache_key = f"generate:{prompt}"
            if hasattr(self, "_get_cache"):
                cached = self._get_cache(cache_key)
                if cached:
                    return cached
                
            response = await self._model.generate_content(prompt)
            
            # 保存到快取
            if hasattr(self, "_set_cache"):
                self._set_cache(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Gemini 生成失敗: {str(e)}")
            raise GenerationError(f"Gemini 生成失敗: {str(e)}")
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """流式生成回應"""
        try:
            response = await self._model.generate_content(
                prompt,
                stream=True
            )
            return response
            
        except Exception as e:
            logger.error(f"Gemini 流式生成失敗: {str(e)}")
            raise GenerationError(f"Gemini 流式生成失敗: {str(e)}")
    
    async def close(self):
        """關閉模型並清理資源"""
        try:
            # 執行清理操作
            if hasattr(self, '_model'):
                await self._model.close()
        except Exception as e:
            # 記錄錯誤但不拋出
            logger.error(f"清理資源時發生錯誤: {str(e)}")
            pass  # 靜默處理錯誤
            
    async def analyze_image(
        self,
        image: bytes,
        prompt: str = None
    ) -> Any:
        """分析圖片"""
        try:
            model = genai.GenerativeModel('gemini-pro-vision')
            response = await model.generate_content_async([image, prompt or "描述這張圖片"])
            return response
            
        except Exception as e:
            logger.error(f"Gemini 圖片分析失敗: {str(e)}")
            raise GenerationError(f"Gemini 圖片分析失敗: {str(e)}")
            
    async def count_tokens(self, text: str) -> int:
        """計算 tokens"""
        try:
            result = self._model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.error(f"計算 tokens 失敗: {str(e)}")
            return 0
            
    async def validate(self) -> bool:
        """驗證模型"""
        try:
            response = await self.generate("Test message")
            return True if response else False
        except Exception:
            return False
    
    async def update_config(self, new_config: dict) -> None:
        """更新模型配置"""
        self.config = {
            **self.config,  # 保留原有配置
            **new_config   # 更新新配置
        }

    def reset_config(self) -> None:
        """重置配置為默認值"""
        self.config = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.95,
            "top_k": 40
        }
        
    async def is_safe_content(self, content: str) -> bool:
        """檢查內容安全性"""
        return True
        
    async def initialize(self) -> None:
        """初始化資源"""
        pass
            
    async def cleanup(self) -> None:
        """清理資源"""
        pass

    def _get_cache(self, key: str) -> Any:
        """獲取快取"""
        return self._cache.get(key)

    def _set_cache(self, key: str, value: Any) -> None:
        """設置快取"""
        self._cache[key] = value

    def _format_messages(self, messages: List[Dict]) -> List[Dict]:
        """格式化消息列表"""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg["role"],
                "parts": [msg["content"]]
            })
        return formatted
    
    def _build_prompt(self, messages: List[Dict]) -> str:
        """構建提示詞"""
        prompt = []
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"]
            prompt.append(f"{role}: {content}")
        return "\n".join(prompt)
    
    async def _validate_response(self, response: Dict) -> bool:
        """驗證響應"""
        return bool(response and "text" in response)
    
    async def _handle_error(self, error: Exception) -> ModelResponse:
        """處理錯誤"""
        return ModelResponse(
            text=f"錯誤：{str(error)}",
            error=True,
            raw_response={"error": str(error)}
        )
    
    async def _handle_generation_error(self, error: GenerationError) -> ModelResponse:
        """處理生成錯誤"""
        return ModelResponse(
            text=f"生成錯誤：{str(error)}",
            error=True,
            raw_response={"error": str(error)}
        )
    
    async def _handle_validation_error(self, error: ValidationError) -> ModelResponse:
        """處理驗證錯誤"""
        return ModelResponse(
            text=f"驗證錯誤：{str(error)}",
            error=True,
            raw_response={"error": str(error)}
        )
    
    def _get_model_info(self) -> Dict:
        """獲取模型信息"""
        return {
            "model_name": self.model_name,
            "provider": "google"
        }
    
    def _get_usage_info(self, tokens: int) -> Dict:
        """獲取使用信息"""
        return {
            "total_tokens": tokens,
            "prompt_tokens": tokens // 2,
            "completion_tokens": tokens // 2
        }
    
    def _create_response(self, text: str, tokens: int) -> ModelResponse:
        """創建響應對象"""
        return ModelResponse(
            text=text,
            tokens=tokens,
            model_info=self._get_model_info(),
            usage=self._get_usage_info(tokens)
        )
    
    async def _is_valid_response(self, response: Dict) -> bool:
        """檢查響應是否有效"""
        return bool(response and "text" in response)
    
    async def _get_response_text(self, response: Dict) -> str:
        """獲取響應文本"""
        return response.get("text", "")