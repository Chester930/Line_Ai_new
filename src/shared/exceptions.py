"""自定義異常類"""

class CAGError(Exception):
    """CAG 系統基礎異常"""
    pass

class ModelError(CAGError):
    """AI 模型相關異常"""
    pass

class GenerationError(ModelError):
    """生成錯誤"""
    pass

class ConfigError(CAGError):
    """配置相關異常"""
    pass

class PluginError(CAGError):
    """插件相關異常"""
    pass

class DatabaseError(CAGError):
    """數據庫相關異常"""
    pass

class SessionError(CAGError):
    """會話相關異常"""
    pass

class ValidationError(CAGError):
    """驗證相關異常"""
    pass

class AuthenticationError(CAGError):
    """認證相關異常"""
    pass

class PermissionError(CAGError):
    """權限相關異常"""
    pass

class ResourceNotFoundError(CAGError):
    """資源未找到異常"""
    pass

class ResourceExistsError(CAGError):
    """資源已存在異常"""
    pass

class TimeoutError(CAGError):
    """超時異常"""
    pass

class NetworkError(CAGError):
    """網絡相關異常"""
    pass

class APIError(CAGError):
    """API 相關異常"""
    pass

class EventError(Exception):
    """事件處理錯誤"""
    pass 