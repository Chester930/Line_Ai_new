class CAGError(Exception):
    """CAG 系統基礎異常類"""
    pass

class GenerationError(CAGError):
    """生成回應時的異常"""
    pass

class ContextError(CAGError):
    """上下文處理異常"""
    pass

class MemoryError(CAGError):
    """記憶系統異常"""
    pass

class StateError(CAGError):
    """狀態處理異常"""
    pass 