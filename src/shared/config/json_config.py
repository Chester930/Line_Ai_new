import json
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from .base import BaseConfig
from ..utils.logger import logger
import aiofiles
import os

T = TypeVar('T', bound='JSONConfig')

class EnhancedPathEncoder(json.JSONEncoder):
    """增强型路径处理器"""
    def default(self, obj):
        if isinstance(obj, Path):
            return obj.as_posix()  # 统一使用POSIX路径格式
        return super().default(obj)

class Settings(BaseModel):
    """配置設置"""
    database: Dict[str, Any] = Field(default_factory=lambda: {"host": "localhost", "port": "5432"})
    api: Dict[str, Any] = Field(default_factory=lambda: {"version": "v1"})

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='allow'
    )

class JSONConfig(BaseConfig):
    """JSON 配置基類"""
    app_name: str = Field(default="test_app")
    settings: Settings = Field(default_factory=Settings)
    debug: bool = Field(default=False)
    port: int = Field(default=8000)
    data_path: Optional[Path] = Field(default=None)
    version: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    
    # 定義私有屬性
    config_file_path: Optional[Path] = Field(default=None, exclude=True)
    config_data: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    is_loaded: bool = Field(default=False, exclude=True)
    env_prefix: Optional[str] = Field(default=None, exclude=True)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        extra='allow',
    )
    
    def __init__(self, path: Optional[Union[str, Path]] = None, *, env_prefix: Optional[str] = None, data: Optional[Dict[str, Any]] = None, **kwargs):
        """初始化配置"""
        super().__init__(**kwargs)
        self.config_file_path = Path(path) if path else None
        self.config_data = {}
        self.is_loaded = False
        self.env_prefix = env_prefix
        
        # 初始化數據
        if data:
            for key, value in data.items():
                setattr(self, key, value)
                self.config_data[key] = value
            self.is_loaded = True
        
        # 設置配置文件路徑
        if path:
            self._ensure_config_file()
            if self.config_file_path.exists():
                self._load_config()
    
    def _sync_config(self) -> None:
        """同步實例屬性到配置字典"""
        try:
            # 使用model_dump获取所有字段值
            model_data = self.model_dump(
                exclude={'config_file_path', 'is_loaded', 'env_prefix'},
                by_alias=True,
                exclude_unset=False
            )
            
            # 合并额外属性
            combined_data = {
                **model_data,
                **{k: v for k, v in self.__dict__.items() 
                   if k not in model_data and not k.startswith('_')}
            }
            
            # 特殊处理Path对象
            self.config_data = {
                k: str(v) if isinstance(v, Path) else v
                for k, v in combined_data.items()
            }
            
        except Exception as e:
            logger.error(f"配置同步失败: {str(e)}")
            raise
    
    def _ensure_config_file(self) -> None:
        """確保配置文件存在"""
        if not self.config_file_path:
            return
        
        try:
            # 確保父目錄存在
            self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果文件不存在，創建空配置文件
            if not self.config_file_path.exists():
                self.config_file_path.write_text("{}")
                logger.info(f"已創建空配置文件: {self.config_file_path}")
            
        except Exception as e:
            logger.error(f"創建配置文件失敗: {str(e)}")
            raise
    
    def _load_config(self) -> bool:
        """載入配置文件"""
        if not self.config_file_path or not self.config_file_path.exists():
            return False
        
        try:
            # 新增类型转换处理
            def convert_types(data):
                if isinstance(data, dict):
                    return {k: convert_types(v) for k, v in data.items()}
                if isinstance(data, list):
                    return [convert_types(v) for v in data]
                if isinstance(data, str) and 'path' in data.lower():
                    return Path(data)
                return data

            config_text = self.config_file_path.read_text()
            config_data = json.loads(config_text)
            processed_data = convert_types(config_data)
            
            # 使用update方法确保所有字段更新
            self.config_data.update(processed_data)
            for key in self.model_fields:
                if key in processed_data:
                    setattr(self, key, processed_data[key])
            
            logger.info(f"已載入配置: {self.config_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            raise
    
    def _convert_paths(self, data: Any) -> Any:
        """轉換路徑值"""
        if isinstance(data, dict):
            if "__path__" in data:
                # 統一使用正斜線
                path_str = str(data["__path__"]).replace('\\', '/')
                return Path(path_str)  # 返回 Path 對象
            return {k: self._convert_paths(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_paths(v) for v in data]
        elif isinstance(data, (str, Path)):
            path_str = str(data)
            if '://' in path_str:  # URL 格式
                return path_str
            if '/' in path_str or '\\' in path_str:
                # 統一使用正斜線
                normalized = path_str.replace('\\', '/')
                if ':' in normalized[:2]:  # Windows 絕對路徑
                    return normalized
                return Path(normalized)  # 返回 Path 對象
        return data
    
    @property
    def config_path(self) -> Optional[Path]:
        """獲取配置文件路徑"""
        return self.config_file_path
    
    @config_path.setter
    def config_path(self, value: Optional[Union[str, Path]]) -> None:
        """設置配置文件路徑"""
        if value is not None:
            self.config_file_path = Path(value)
        else:
            self.config_file_path = None
    
    @config_path.deleter
    def config_path(self) -> None:
        """刪除配置文件路徑"""
        self.config_file_path = None
    
    async def load(self) -> bool:
        """載入配置"""
        try:
            if not self.config_file_path:
                return False
            
            path = Path(self.config_file_path)
            if not path.exists():
                self._ensure_config_file()
                return True
            
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if not content:
                return True
            
            data = json.loads(content)
            # 更新配置字典和實例屬性
            self.config_data.update(data)
            for key, value in data.items():
                if key in self.model_fields:
                    setattr(self, key, value)
            self.is_loaded = True  # 確保加載狀態更新
            return True
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            return False

    async def save(self) -> bool:
        """保存配置"""
        try:
            self._sync_config()
            async with aiofiles.open(self.config_file_path, 'w', encoding='utf-8') as f:
                content = json.dumps(
                    self.config_data,
                    indent=2,
                    cls=EnhancedPathEncoder,  # 使用自定義編碼器
                    ensure_ascii=False
                )
                await f.write(content)
            self.is_loaded = True
            return True
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False

    async def update(self, data: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            # 更新配置
            for key, value in data.items():
                setattr(self, key, value)
                self.config_data[key] = value  # 同時更新配置字典
            
            # 保存更新
            return await self.save()
        except Exception as e:
            logger.error(f"更新配置失敗: {str(e)}")
            return False
    
    async def reload(self) -> bool:
        """重新載入配置"""
        try:
            self.is_loaded = False  # 重置加載狀態
            if await self.load():
                # 應用環境變量覆蓋
                self._apply_env_override()
                # 保存更改
                await self.save()
                return True
            return False
        except Exception as e:
            logger.error(f"重新載入失敗: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        try:
            keys = key.split('.')
            current = self.config_data
            
            for k in keys:
                if not isinstance(current, dict) or k not in current:
                    return default
                current = current[k]
            
            # 特殊處理路徑值
            if isinstance(current, dict) and "__path__" in current:
                return Path(current["__path__"])  # 直接返回 Path 對象
            
            # 處理字符串路徑
            if isinstance(current, str):
                if '://' in current:  # URL 格式
                    return current
                if '/' in current or '\\' in current:
                    return Path(current.replace('\\', '/'))  # 轉換為 Path 對象
            
            return current
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """設置配置值"""
        try:
            if not key or not isinstance(key, str):
                raise ValueError("無效的配置鍵")
            
            # 處理嵌套鍵
            keys = key.split('.')
            if not all(keys):  # 檢查空鍵
                raise ValueError("無效的配置鍵")
            
            # 如果是單層鍵，直接設置
            if len(keys) == 1:
                # 轉換值類型
                if key == "debug":
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes')
                    elif not isinstance(value, bool):
                        raise ValueError("debug 必須是布爾值")
                elif key == "port":
                    if isinstance(value, str):
                        value = int(value)
                    elif not isinstance(value, int):
                        raise ValueError("port 必須是整數")
                
                # 處理路徑值
                if isinstance(value, (str, Path)):
                    value = self._convert_paths(value)
                
                setattr(self, key, value)
                self.config_data[key] = value
                
                # 自動保存
                if self.config_file_path:
                    return self.save()
                return True
            
            # 處理嵌套鍵
            current = self.config_data
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                elif not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            # 設置最後一層的值
            current[keys[-1]] = self._convert_paths(value)
            
            # 自動保存
            if self.config_file_path:
                return self.save()
            return True
            
        except Exception as e:
            logger.error(f"設置配置失敗: {str(e)}")
            raise ValueError(str(e))
    
    def merge(self, data: Dict[str, Any]) -> bool:
        """合併配置"""
        try:
            # 驗證輸入數據
            if not data or not isinstance(data, dict):
                raise ValueError("無效的合併數據")
            
            # 檢查鍵的有效性
            for key in data.keys():
                if not key or not isinstance(key, str) or '.' in key:
                    raise ValueError(f"無效的配置鍵: {key}")
            
            # 處理路徑值
            processed_data = self._convert_paths(data)
            
            # 遞歸合併字典
            def deep_merge(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
                result = d1.copy()
                for key, value in d2.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result
            
            # 合併到配置字典
            merged_config = deep_merge(self.config_data, processed_data)
            
            # 驗證合併後的數據
            if not self._validate_data(merged_config):
                raise ValueError("合併後的配置無效")
            
            # 更新配置字典
            self.config_data = merged_config
            
            # 更新實例屬性
            for key, value in processed_data.items():
                if hasattr(self, key):
                    if key == "settings":
                        # 特殊處理 settings
                        current_settings = self.settings.model_dump()
                        merged_settings = deep_merge(current_settings, value)
                        self.settings = Settings(**merged_settings)
                        self.config_data['settings'] = merged_settings
                    else:
                        setattr(self, key, value)
            
            # 自動保存
            if self.config_file_path:
                return self.save()
            return True
            
        except Exception as e:
            logger.error(f"合併配置失敗: {str(e)}")
            return False

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """驗證配置數據"""
        try:
            # 如果是空配置，允許通過
            if not data:
                return True
            
            # 檢查字段類型（如果存在）
            if "debug" in data and not isinstance(data.get("debug"), bool):
                raise ValueError("debug 必須是布爾值")
            if "port" in data and not isinstance(data.get("port"), int):
                raise ValueError("port 必須是整數")
            
            # 檢查嵌套結構
            if "settings" in data:
                settings = data.get("settings", {})
                if not isinstance(settings, dict):
                    raise ValueError("settings 必須是字典")
                # 檢查 database 字段
                if "database" in settings and not isinstance(settings["database"], dict):
                    raise ValueError("settings.database 必須是字典")
            
            return True
        except Exception as e:
            logger.error(f"驗證配置失敗: {str(e)}")
            return False

    def _apply_env_override(self):
        """增強環境變量覆蓋邏輯"""
        try:
            # 直接處理環境變量
            if not self.env_prefix:
                return
            
            # 處理嵌套設置的環境變量
            for key in os.environ:
                if key.startswith(self.env_prefix):
                    # 移除前綴並轉換為小寫
                    config_key = key[len(self.env_prefix):].lower()
                    value = os.environ[key]
                    
                    if config_key.startswith('settings__'):
                        # 處理嵌套設置
                        parts = config_key.split('__')[1:]
                        current = self.settings
                        for part in parts[:-1]:
                            current = getattr(current, part, None) or {}
                        setattr(current, parts[-1], value)
                    else:
                        # 一般屬性
                        if hasattr(self, config_key):
                            # 轉換值類型
                            current_value = getattr(self, config_key)
                            if isinstance(current_value, bool):
                                value = value.lower() in ('true', '1', 'yes')
                            elif isinstance(current_value, int):
                                value = int(value)
                            elif isinstance(current_value, Path):
                                value = Path(value)
                            setattr(self, config_key, value)
                            self.config_data[config_key] = value
            
            # 保存更改
            self._sync_config()
            # 標記為已修改
            self.is_loaded = True
        except Exception as e:
            logger.error(f"環境變量覆蓋失敗: {str(e)}")

class JSONConfigLoader:
    """JSON 配置加載器"""
    
    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
    
    def load(self, config_class: Type[T]) -> T:
        """加載配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            # 讀取文件內容
            config_data = json.loads(self.config_path.read_text())
            
            # 創建配置實例
            config = config_class(path=self.config_path, **config_data)
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"無效的 JSON 格式: {str(e)}")
        except Exception as e:
            raise ValueError(f"加載配置失敗: {str(e)}")
    
    def save(self, config: T) -> bool:
        """保存配置"""
        try:
            # 設置配置文件路徑
            config.config_path = self.config_path
            return config.save()
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False

class JsonConfigError(Exception):
    """JSON 配置錯誤"""
    pass 