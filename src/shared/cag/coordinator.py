from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
from .context import ContextManager
from .memory import MemoryPool
from .state import StateTracker, DialogueState
from .generator import ResponseGenerator, GenerationResult
from .exceptions import CAGError
from ..config.cag_config import ConfigManager, CAGSystemConfig
from ..logger.log_manager import LogManager
import json
from ..ai.models.gemini import GeminiModel, GeminiConfig
from ..session.manager import SessionManager
from ..session.base import Message
from ..plugins.manager import PluginManager
from ..plugins.base import PluginConfig

logger = logging.getLogger(__name__)

@dataclass
class CAGConfig:
    """CAG 系統配置"""
    max_context_length: int = 2000
    memory_ttl: int = 3600  # 短期記憶存活時間(秒)
    enable_state_tracking: bool = True
    
class CAGCoordinator:
    """CAG 系統協調器"""
    def __init__(
        self,
        config_path: Optional[str] = None,
        plugins_config_path: str = "config/plugins_config.json",
        plugins_dir: str = "plugins"
    ):
        # 初始化配置管理器
        self.config_manager = ConfigManager(config_path)
        self.system_config = self.config_manager.load_config()
        
        # 初始化日誌管理器
        self.logger = LogManager(
            log_level=self.system_config.log_level
        ).logger
        
        # 初始化 Gemini 模型
        model_config = GeminiConfig(**self.system_config.models["gemini"].__dict__)
        self.model = GeminiModel(model_config)
        
        # 初始化其他組件
        self.context_manager = ContextManager(
            max_context_length=self.system_config.max_context_length
        )
        self.memory_pool = MemoryPool()
        self.state_tracker = StateTracker()
        self.generator = ResponseGenerator(self.model)
        
        # 初始化會話管理器
        self.session_manager = SessionManager()
        
        # 初始化插件管理器
        self.plugin_manager = PluginManager()
        self._load_plugins(plugins_config_path)
        
        # 啟動插件監視
        self.plugins_dir = plugins_dir
        
    async def _load_plugins(self, config_path: str) -> None:
        """載入插件配置並初始化插件"""
        try:
            # 載入插件配置
            with open(config_path, 'r', encoding='utf-8') as f:
                plugin_configs = json.load(f)
            
            # 載入所有插件類
            await self.plugin_manager.load_plugins()
            
            # 初始化已啟用的插件
            for name, config in plugin_configs["plugins"].items():
                if config.get("enabled", True):
                    plugin_config = PluginConfig(
                        name=name,
                        version=config["version"],
                        settings=config.get("settings")
                    )
                    await self.plugin_manager.initialize_plugin(name, plugin_config)
                    
            self.logger.info("插件系統初始化完成")
            
        except Exception as e:
            self.logger.error(f"載入插件失敗: {str(e)}")
            raise
    
    async def execute_plugin(
        self,
        plugin_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """執行插件"""
        try:
            return await self.plugin_manager.execute_plugin(plugin_name, context)
        except Exception as e:
            self.logger.error(f"執行插件 {plugin_name} 失敗: {str(e)}")
            raise
    
    async def start(self):
        """啟動協調器"""
        await self.session_manager.start()
        await self.plugin_manager.start_watching(self.plugins_dir)
    
    async def stop(self):
        """停止協調器"""
        await self.session_manager.stop()
        await self.plugin_manager.stop_watching()
        await self.plugin_manager.cleanup_plugins()
    
    async def process_message(
        self,
        message: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """處理用戶消息"""
        try:
            # 獲取或創建會話
            session = None
            if session_id:
                session = await self.session_manager.get_session(session_id)
            if not session:
                session = await self.session_manager.create_session(user_id)
                session_id = session.id
            
            # 創建消息對象
            message_obj = Message.create(
                user_id=user_id,
                content=message,
                role="user",
                metadata=metadata
            )
            
            # 添加消息到會話
            session.add_message(message_obj)
            
            # 記錄請求信息
            self.logger.info(f"Processing message from user {user_id}")
            self.logger.debug(f"Message content: {message}")
            if metadata:
                self.logger.debug(f"Message metadata: {json.dumps(metadata)}")
            
            # 1. 更新狀態
            await self.state_tracker.set_state(
                DialogueState.PROCESSING,
                metadata={"user_id": user_id}
            )
            
            # 2. 獲取相關記憶
            context_memory = await self.memory_pool.get_memory(
                f"context_{user_id}"
            )
            
            # 檢查是否需要調用插件
            if metadata and "plugin" in metadata:
                plugin_result = await self.execute_plugin(
                    metadata["plugin"],
                    {
                        "message": message,
                        "user_id": user_id,
                        **metadata.get("plugin_context", {})
                    }
                )
                
                # 將插件結果添加到上下文
                context_memory["plugin_result"] = plugin_result
            
            # 3. 生成回應
            result = await self.generator.generate(
                prompt=message,
                context=context_memory
            )
            
            # 4. 更新記憶
            await self.memory_pool.add_memory(
                f"context_{user_id}",
                self.context_manager.current_context.messages,
                ttl=self.system_config.memory_ttl
            )
            
            # 5. 更新狀態
            await self.state_tracker.set_state(
                DialogueState.ACTIVE,
                metadata={
                    "user_id": user_id,
                    "last_response": result.content
                }
            )
            
            # 更新會話
            await self.session_manager.update_session(session)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise 