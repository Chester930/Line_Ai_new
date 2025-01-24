from typing import Dict, List, Optional
from pydantic import BaseModel, validator
from .settings import Settings

class ConfigValidator(BaseModel):
    """配置驗證器"""
    
    settings: Settings
    
    @validator("settings")
    def validate_api_keys(cls, v: Settings) -> Settings:
        """驗證 API 密鑰"""
        if not v.GOOGLE_API_KEY:
            raise ValueError("必須提供 Google API Key")
            
        if v.DEFAULT_MODEL == "gpt" and not v.OPENAI_API_KEY:
            raise ValueError("使用 GPT 模型時必須提供 OpenAI API Key")
            
        if v.DEFAULT_MODEL == "claude" and not v.ANTHROPIC_API_KEY:
            raise ValueError("使用 Claude 模型時必須提供 Anthropic API Key")
        
        return v
    
    @validator("settings")
    def validate_line_config(cls, v: Settings) -> Settings:
        """驗證 LINE 配置"""
        if not v.LINE_CHANNEL_SECRET or not v.LINE_CHANNEL_ACCESS_TOKEN:
            raise ValueError("必須提供 LINE Channel 配置")
        return v
    
    @validator("settings")
    def validate_limits(cls, v: Settings) -> Settings:
        """驗證限制設置"""
        if v.CONTEXT_LIMIT < 100:
            raise ValueError("上下文限制不能小於 100")
        
        if v.MEMORY_LIMIT < 50:
            raise ValueError("記憶限制不能小於 50")
        
        if v.SESSION_TIMEOUT < 300:
            raise ValueError("會話超時不能小於 300 秒")
        
        return v
    
    def validate_all(self) -> Dict[str, List[str]]:
        """執行所有驗證"""
        try:
            self.validate_api_keys(self.settings)
            self.validate_line_config(self.settings)
            self.validate_limits(self.settings)
            return {"success": True}
        except ValueError as e:
            return {"errors": [str(e)]} 