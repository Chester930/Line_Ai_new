from typing import Optional, Dict, Any, List
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
from ..rag.system import RAGSystem
from ..events.system import EventSystem

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
        # 保存配置路徑
        self.config_path = config_path
        self.plugins_config_path = plugins_config_path
        self.plugins_dir = plugins_dir
        
        # 初始化 logger
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    async def create(
        cls,
        config_path: Optional[str] = None,
        plugins_config_path: str = "config/plugins_config.json",
        plugins_dir: str = "plugins"
    ) -> "CAGCoordinator":
        """創建協調器實例"""
        coordinator = cls(config_path, plugins_config_path, plugins_dir)
        await coordinator.initialize()
        return coordinator
        
    async def initialize(self):
        """初始化協調器"""
        # 初始化配置管理器
        self.config_manager = ConfigManager(self.config_path)
        self.system_config = self.config_manager.load_config()
        
        # 初始化核心組件
        self.context_manager = ContextManager(
            max_context_length=self.system_config.max_context_length
        )
        self.memory_pool = MemoryPool()
        self.state_tracker = StateTracker()
        self.rag_system = RAGSystem()
        self.event_system = EventSystem()
        
        # 初始化 AI 模型
        model_config = GeminiConfig(**self.system_config.models["gemini"].__dict__)
        self.model = GeminiModel(model_config)
        self.generator = ResponseGenerator(self.model)
        
        # 初始化插件系統
        self.plugin_manager = PluginManager()
        await self._load_plugins(self.plugins_config_path)
        
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
                    try:
                        plugin_config = PluginConfig(
                            name=name,
                            version=config["version"],
                            settings=config.get("settings")
                        )
                        await self.plugin_manager.initialize_plugin(name, plugin_config)
                    except PluginError as e:
                        # 忽略未找到的插件
                        self.logger.warning(f"跳過插件 {name}: {str(e)}")
                        continue
                    
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
        # 移除 session_manager 相關代碼
        await self.plugin_manager.start_watching(self.plugins_dir)
        self.logger.info("CAG Coordinator started")
    
    async def stop(self):
        """停止協調器"""
        # 移除 session_manager 相關代碼
        await self.plugin_manager.stop_watching()
        await self.plugin_manager.cleanup_plugins()
        self.logger.info("CAG Coordinator stopped")
    
    async def process_message(self, message: str, context: Dict[str, Any]) -> str:
        """處理用戶消息"""
        try:
            # 1. 更新狀態
            await self.state_tracker.set_state(
                DialogueState.PROCESSING,
                {"message": message}
            )
            
            # 2. RAG 知識檢索
            relevant_docs = await self.rag_system.retrieve(message)
            
            # 3. 插件處理
            plugin_results = await self.plugin_manager.process(message)
            
            # 4. 生成回應
            response = await self.generate_response(
                message,
                context,
                relevant_docs,
                plugin_results
            )
            
            # 5. 事件追蹤
            await self.event_system.track(
                "response_generated",
                {"message": message, "response": response}
            )
            
            # 6. 更新狀態
            await self.state_tracker.set_state(
                DialogueState.ACTIVE,
                {"response": response}
            )
            
            return response
            
        except Exception as e:
            await self.state_tracker.set_state(
                DialogueState.ERROR,
                {"error": str(e)}
            )
            raise CAGError(f"處理消息失敗: {str(e)}")
    
    async def generate_response(
        self,
        message: str,
        context: Dict[str, Any],
        relevant_docs: List[str],
        plugin_results: Dict[str, Any]
    ) -> str:
        """生成回應"""
        try:
            # 構建生成上下文
            generation_context = {
                "message": message,
                "context": context,
                "relevant_docs": relevant_docs,
                "plugin_results": plugin_results
            }
            
            # 生成回應
            result = await self.generator.generate(
                prompt=message,
                context=generation_context
            )
            
            # 更新記憶
            if context.get("user_id"):
                await self.memory_pool.add_memory(
                    f"context_{context['user_id']}",
                    self.context_manager.current_context.messages,
                    ttl=self.system_config.memory_ttl
                )
            
            return result.content
            
        except Exception as e:
            self.logger.error(f"生成回應失敗: {str(e)}")
            raise CAGError(f"生成回應失敗: {str(e)}") 