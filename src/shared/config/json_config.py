import json
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, Union
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from .base import BaseConfig
from ..utils.logger import logger

T = TypeVar('T', bound='JSONConfig')

class PathEncoder(json.JSONEncoder):
    """處理 Path 對象的 JSON 編碼器"""
    
    def default(self, obj: Any) -> Any:
        """自定義編碼方法"""
        if isinstance(obj, Path):
            return {"__path__": str(obj).replace('\\', '/')}
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
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
    
    # 定義私有屬性
    _config_file_path: Optional[Path] = PrivateAttr(default=None)
    _config: Dict[str, Any] = PrivateAttr(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        populate_by_name=True,
        extra='allow'
    )
    
    def __init__(self, **data):
        """初始化配置"""
        # 從 data 中提取 config_path
        config_path = data.pop('config_path', None)
        
        # 調用父類初始化
        super().__init__(**data)
        
        # 設置配置文件路徑
        if config_path:
            self._config_file_path = Path(config_path)
            self._ensure_config_file()
            if self._config_file_path.exists():
                self._load_config()
        
        # 初始化配置字典
        self._config = self.model_dump()
    
    def _sync_config(self) -> None:
        """同步實例屬性到配置字典"""
        # 獲取所有公共屬性
        data = self.model_dump(exclude={'_config_file_path', '_config'})
        # 更新配置字典
        self._config.update(data)
    
    def _ensure_config_file(self) -> None:
        """確保配置文件存在"""
        if not self._config_file_path:
            return
        
        try:
            # 確保父目錄存在
            self._config_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果文件不存在，創建空配置文件
            if not self._config_file_path.exists():
                self._config_file_path.write_text("{}")
                logger.info(f"已創建空配置文件: {self._config_file_path}")
            
        except Exception as e:
            logger.error(f"創建配置文件失敗: {str(e)}")
            raise
    
    def _load_config(self) -> bool:
        """載入配置文件"""
        if not self._config_file_path or not self._config_file_path.exists():
            return False
        
        try:
            # 讀取並解析配置文件
            config_text = self._config_file_path.read_text()
            if not config_text.strip():
                config_text = "{}"
            
            try:
                # 解析 JSON，如果失敗直接拋出異常
                config_data = json.loads(config_text)
            except json.JSONDecodeError as e:
                logger.error(f"無效的 JSON 格式: {str(e)}")
                raise ValueError(f"無效的 JSON 格式: {str(e)}")
            
            # 處理路徑值
            config_data = self._convert_paths(config_data)
            
            # 驗證並更新配置
            validated = self.model_validate(config_data)
            validated_data = validated.model_dump(exclude={'_config_file_path', '_config'})
            
            # 更新配置字典和實例屬性
            self._config.clear()
            self._config.update(validated_data)
            
            # 更新實例屬性
            for key, value in validated_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            logger.info(f"已載入配置: {self._config_file_path}")
            return True
            
        except ValueError:
            # 直接拋出 ValueError
            raise
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            raise ValueError(f"載入配置失敗: {str(e)}")
    
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
        return self._config_file_path
    
    @config_path.setter
    def config_path(self, value: Optional[Union[str, Path]]) -> None:
        """設置配置文件路徑"""
        if value is not None:
            self._config_file_path = Path(value)
        else:
            self._config_file_path = None
    
    @config_path.deleter
    def config_path(self) -> None:
        """刪除配置文件路徑"""
        self._config_file_path = None
    
    def save(self, path: Optional[Union[str, Path]] = None) -> bool:
        """保存配置到文件"""
        try:
            save_path = Path(path) if path else self._config_file_path
            if not save_path:
                return False
            
            # 確保目標目錄存在
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 同步最新的實例屬性到配置字典
            self._sync_config()
            
            # 保存到文件
            save_path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False, cls=PathEncoder)
            )
            
            # 更新配置路徑
            if path:
                self._config_file_path = save_path
            
            return True
                
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False
    
    def update(self, data: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            # 驗證輸入數據
            if not data or not isinstance(data, dict):
                logger.error("無效的更新數據")
                return False
            
            # 檢查鍵的有效性
            for key in data.keys():
                if not key or not isinstance(key, str) or '.' in key:
                    logger.error(f"無效的配置鍵: {key}")
                    return False
            
            # 處理路徑值
            processed_data = self._convert_paths(data)
            
            # 保存當前值
            current_values = self.model_dump(exclude={'_config_file_path', '_config'})
            
            try:
                # 合併並驗證新數據
                merged_data = {**current_values, **processed_data}
                validated = self.model_validate(merged_data)
                validated_data = validated.model_dump(exclude={'_config_file_path', '_config'})
                
                # 更新配置字典和實例屬性
                self._config.update(validated_data)
                
                # 更新實例屬性
                for key, value in validated_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                # 自動保存
                if self._config_file_path:
                    return self.save()
                return True
                
            except ValueError as e:
                logger.error(f"驗證更新數據失敗: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"更新配置失敗: {str(e)}")
            return False
    
    def reload(self) -> bool:
        """重新載入配置文件"""
        if not self._config_file_path:
            return False
        
        # 檢查文件是否存在
        if not self._config_file_path.exists():
            logger.info(f"配置文件不存在: {self._config_file_path}")
            return False
        
        try:
            # 讀取並解析配置文件
            config_text = self._config_file_path.read_text()
            if not config_text.strip():
                logger.info(f"配置文件為空: {self._config_file_path}")
                # 重置為默認值
                self._config.clear()
                return True
            
            try:
                config_data = json.loads(config_text)
            except json.JSONDecodeError as e:
                logger.error(f"無效的 JSON 格式: {str(e)}")
                raise ValueError(f"無效的 JSON 格式: {str(e)}")
            
            # 處理路徑值
            config_data = self._convert_paths(config_data)
            
            # 驗證並更新配置
            validated = self.model_validate(config_data)
            validated_data = validated.model_dump(exclude={'_config_file_path', '_config'})
            
            # 更新配置字典和實例屬性
            self._config.clear()
            self._config.update(validated_data)
            
            # 更新實例屬性
            for key, value in validated_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            logger.info(f"已重新載入配置: {self._config_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"重新載入配置失敗: {str(e)}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        try:
            keys = key.split('.')
            current = self._config
            
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
                self._config[key] = value
                
                # 自動保存
                if self._config_file_path:
                    return self.save()
                return True
            
            # 處理嵌套鍵
            current = self._config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                elif not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            # 設置最後一層的值
            current[keys[-1]] = self._convert_paths(value)
            
            # 自動保存
            if self._config_file_path:
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
            merged_config = deep_merge(self._config, processed_data)
            
            # 驗證合併後的數據
            if not self._validate_data(merged_config):
                raise ValueError("合併後的配置無效")
            
            # 更新配置字典
            self._config = merged_config
            
            # 更新實例屬性
            for key, value in processed_data.items():
                if hasattr(self, key):
                    if key == "settings":
                        # 特殊處理 settings
                        current_settings = self.settings.model_dump()
                        merged_settings = deep_merge(current_settings, value)
                        self.settings = Settings(**merged_settings)
                        self._config['settings'] = merged_settings
                    else:
                        setattr(self, key, value)
            
            # 自動保存
            if self._config_file_path:
                return self.save()
            return True
            
        except Exception as e:
            logger.error(f"合併配置失敗: {str(e)}")
            return False

    def load(self, path: Union[str, Path]) -> bool:
        """從文件加載配置"""
        try:
            self._config_file_path = Path(path)
            if not self._config_file_path.exists():
                logger.warning(f"配置文件不存在: {path}")
                raise ValueError(f"配置文件不存在: {path}")
            
            if not self._load_config():
                logger.error(f"加載配置失敗: {path}")
                raise ValueError(f"加載配置失敗: {path}")
            
            return True
        except json.JSONDecodeError as e:
            logger.error(f"無效的 JSON 格式: {str(e)}")
            raise ValueError(f"無效的 JSON 格式: {str(e)}")
        except Exception as e:
            logger.error(f"加載配置失敗: {str(e)}")
            raise ValueError(str(e))

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

    def _apply_env_override(self) -> None:
        """應用環境變量覆蓋"""
        import os
        
        # 獲取所有環境變量
        for key, value in os.environ.items():
            if key.startswith('TEST_'):
                # 移除前綴並轉換為小寫
                config_key = key[5:].lower()
                
                # 處理嵌套設置
                if config_key.startswith('settings__'):
                    parts = config_key.split('__')[1:]
                    settings = self.settings.model_dump()
                    current = settings
                    
                    # 遍歷路徑
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    
                    # 設置最後一個值
                    current[parts[-1]] = value
                    
                    # 更新設置
                    self.settings = Settings(**settings)
                    self._config['settings'] = settings
                    continue
                
                # 處理一般屬性
                if hasattr(self, config_key):
                    # 獲取當前值作為備份
                    current_value = getattr(self, config_key)
                    
                    # 轉換值類型
                    attr_type = type(current_value)
                    try:
                        if attr_type == bool:
                            if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                                continue  # 保持原值
                            value = value.lower() in ('true', '1', 'yes')
                        elif attr_type == int:
                            value = int(value)
                        elif attr_type == Path:
                            value = Path(value.replace('\\', '/'))  # 統一使用正斜線
                        elif attr_type == str:
                            value = str(value)
                        setattr(self, config_key, value)
                        self._config[config_key] = value
                    except (ValueError, TypeError):
                        # 轉換失敗時保持原值
                        setattr(self, config_key, current_value)
                        self._config[config_key] = current_value

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
            config = config_class(config_path=self.config_path, **config_data)
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