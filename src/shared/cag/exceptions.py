from ..exceptions import CAGError, GenerationError

# 只定義 CAG 特定的錯誤
class ContextError(CAGError):
    """上下文處理異常"""
    pass

class MemoryError(CAGError):
    """記憶系統異常"""
    pass

class StateError(CAGError):
    """狀態處理異常"""
    pass 