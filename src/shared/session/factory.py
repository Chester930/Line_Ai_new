from typing import Dict, Type, Optional
from .base import Session
from .memory import MemorySessionManager
from ..utils.logger import logger

# 添加 SessionManager 導入
from .manager import SessionManager  # 需要先創建這個文件

class SessionFactory:
    """會話工廠類"""
    _managers: Dict[str, Type[Session]] = {
        "memory": MemorySessionManager
    }
    
    @classmethod
    def register_manager(cls, name: str, manager_class: Type[Session]):
        """註冊新的會話管理器類型"""
        cls._managers[name] = manager_class

    @classmethod
    async def create_session(
        cls,
        session_type: str,
        user_id: str,
        metadata: Optional[dict] = None
    ) -> Session:
        """創建指定類型的會話"""
        if session_type not in cls._managers:
            raise ValueError(f"Unknown session type: {session_type}")
        
        manager = cls._managers[session_type]()
        return await manager.create_session(user_id, metadata)

    @classmethod
    def create_manager(
        cls,
        manager_type: str = "memory"
    ) -> Session:
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

class SessionManagerFactory:
    """會話管理器工廠"""
    @staticmethod
    def create(config: dict) -> SessionManager:
        """創建會話管理器實例"""
        return SessionManager(config)