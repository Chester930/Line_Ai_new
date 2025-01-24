from typing import Optional, Type
from .base import BaseSessionManager
from .memory import MemorySessionManager
from ..utils.logger import logger

class SessionManagerFactory:
    """會話管理器工廠"""
    
    _managers = {
        "memory": MemorySessionManager
    }
    
    @classmethod
    def create_manager(
        cls,
        manager_type: str = "memory"
    ) -> BaseSessionManager:
        """創建會話管理器"""
        try:
            manager_class = cls._managers.get(manager_type)
            if not manager_class:
                raise ValueError(
                    f"不支持的會話管理器類型: {manager_type}"
                )
            
            manager = manager_class()
            logger.info(f"已創建會話管理器: {manager_type}")
            return manager
            
        except Exception as e:
            logger.error(f"創建會話管理器失敗: {str(e)}")
            # 默認使用記憶體管理器
            return MemorySessionManager()
    
    @classmethod
    def register_manager(
        cls,
        manager_type: str,
        manager_class: Type[BaseSessionManager]
    ):
        """註冊新的管理器類型"""
        cls._managers[manager_type] = manager_class
        logger.info(f"已註冊新的會話管理器類型: {manager_type}") 