from typing import Any, Dict, Optional, Type, List, ClassVar, Union
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator
import json
import logging
import os
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from ..utils.logger import logger
import copy
import aiofiles

class ConfigError(Exception):
    """配置相關錯誤"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ConfigField:
    """配置字段"""
    def __init__(
        self,
        name: str,
        type_: Type,
        default: Any = None,
        description: str = ""
    ):
        self.name = name
        self.type_ = type_
        self.default = default
        self.description = description

class ConfigManager:
    """配置管理器基類"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._config = {}
            self._initialized = True
            
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        if key is None:
            raise TypeError("Key cannot be None")
            
        try:
            parts = key.split('.')
            current = self._config
            
            for part in parts:
                if isinstance(current, dict):
                    current = current[part]
                else:
                    return default
                    
            return current
        except (KeyError, TypeError):
            return default
        
    def set(self, key: str, value: Any) -> None:
        """設置配置值"""
        if key is None:
            raise TypeError("Key cannot be None")
        if not key:
            raise ValueError("Key cannot be empty")
            
        # 類型轉換
        if isinstance(value, str):
            # 嘗試轉換數字
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                # 嘗試轉換布爾值
                if value.lower() in ('true', 'yes', 'on', '1'):
                    value = True
                elif value.lower() in ('false', 'no', 'off', '0'):
                    value = False
                else:
                    # 嘗試解析 JSON
                    try:
                        import json
                        if value.startswith('[') or value.startswith('{'):
                            value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
                        
        self._config[key] = value
        
    def load(self) -> Dict[str, Any]:
        """加載配置
        
        Returns:
            Dict[str, Any]: 當前配置的副本
        """
        return self._config.copy()
        
    def clear(self) -> None:
        """清除所有配置"""
        self._config.clear()
        
    def update(self, data: Dict[str, Any]) -> None:
        """更新多個配置值
        
        Args:
            data: 要更新的配置字典
        """
        if not isinstance(data, dict):
            raise TypeError("Update data must be a dictionary")
        self._config.update(data)
        
    def __len__(self) -> int:
        return len(self._config)
        
    def __contains__(self, key: str) -> bool:
        return key in self._config
        
    def __getitem__(self, key: str) -> Any:
        return self.get(key)
        
    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

class BaseConfig(BaseModel):
    """配置基類"""
    name: Optional[str] = Field(default=None)
    data_path: Optional[Path] = Field(default=None)
    version: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    settings: Dict[str, Any] = Field(default_factory=dict)
    bool_value: bool = Field(default=False)
    int_value: int = Field(default=0)
    float_value: float = Field(default=0.0)
    list_value: List[Any] = Field(default_factory=list)
    dict_value: Dict[str, Any] = Field(default_factory=dict)
    
    # 添加通用属性
    config_file_path: Optional[Path] = Field(default=None, exclude=True)
    config_data: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    is_loaded: bool = Field(default=False, exclude=True)
    env_prefix: Optional[str] = Field(default=None, exclude=True)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='allow'
    )
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None, **kwargs):
        """初始化配置"""
        super().__init__(**kwargs)
        self._config_file_path = Path(config_path) if config_path else None
        self._config = {}
        self._loaded = False
    
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
    
    async def load(self) -> bool:
        """載入配置"""
        try:
            if not self._config_file_path:
                return False
            
            path = Path(self._config_file_path)
            if not path.exists():
                return True
            
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if not content:
                return True
            
            data = json.loads(content)
            
            # 更新配置字典
            self._config.update(data)
            
            # 更新實例屬性
            for key, value in data.items():
                setattr(self, key, value)
            
            self._loaded = True
            return True
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            return False
    
    async def reload(self) -> bool:
        """重新載入配置"""
        self._loaded = False  # 重置加載狀態
        return await self.load()
    
    async def save(self) -> bool:
        """保存配置"""
        try:
            if not self._config_file_path:
                return False
            
            # 確保目標目錄存在
            Path(self._config_file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 獲取當前配置數據
            data = self.model_dump(exclude={'_config_file_path', '_config'})
            
            async with aiofiles.open(self._config_file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            
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
                self._config[key] = value  # 同時更新配置字典
            
            # 保存更新
            return await self.save()
        except Exception as e:
            logger.error(f"更新配置失敗: {str(e)}")
            return False

    def _process_nested_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理嵌套字典，將點號分隔的鍵轉換為嵌套結構"""
        result = {}
        for key, value in data.items():
            if isinstance(value, dict):
                value = self._process_nested_dict(value)
            
            # 處理點號分隔的鍵
            if isinstance(key, str) and '.' in key:
                parts = key.split('.')
                current = result
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = value
            else:
                result[key] = value
            
        return result

    def _load_env_vars(self) -> None:
        """加載環境變量"""
        try:
            # 獲取所有字段信息
            for key in self.model_fields:
                # 跳過特殊屬性
                if key == "config_path":
                    continue
                    
                # 清理鍵名
                clean_key = key.lower()
                
                # 獲取字段信息
                field_info = self.model_fields[clean_key]
                
                # 檢查環境變量
                env_key = f"TEST_{clean_key}".upper()
                if env_key in os.environ:
                    value = os.environ[env_key]
                    
                    # 根據字段類型轉換值
                    try:
                        if field_info.annotation == bool:
                            value = value.lower() in ('true', '1', 'yes')
                        elif field_info.annotation == int:
                            value = int(value)
                        elif field_info.annotation == Path:
                            value = Path(value)
                        
                        # 設置值
                        setattr(self, clean_key, value)
                    except (ValueError, TypeError):
                        continue
                        
        except Exception as e:
            logger.error(f"加載環境變量失敗: {str(e)}")
            raise ConfigError(f"加載環境變量失敗: {str(e)}")
    
    def _convert_value(self, value: str, field_info: Any) -> Any:
        """轉換值為正確類型"""
        try:
            # 獲取字段類型
            field_type = field_info.annotation
            if hasattr(field_type, "__origin__"):
                if field_type.__origin__ is Union:  # 處理 Optional 類型
                    field_type = field_type.__args__[0]  # 使用第一個非 None 類型
                else:
                    field_type = field_type.__origin__
            
            # 如果已經是正確的類型，直接返回
            if isinstance(value, field_type):
                return value
            
            # 處理基本類型
            if field_type == bool:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif field_type == int:
                return int(value)
            elif field_type == float:
                return float(value)
            elif field_type == str:
                return str(value)  # 確保字符串轉換
            
            # 處理列表類型
            elif field_type == list:  # 改用小寫的 list
                if isinstance(value, str):
                    if value.startswith('['):
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            # JSON 解析失敗時返回默認值
                            return field_info.default_factory() if hasattr(field_info, 'default_factory') else []
                    if ',' in value:  # 只有當字符串包含逗號時才分割
                        return value.split(',')
                    # 其他情況返回默認值
                    return field_info.default_factory() if hasattr(field_info, 'default_factory') else []
                elif isinstance(value, (list, tuple)):
                    return list(value)
                return field_info.default_factory() if hasattr(field_info, 'default_factory') else []
                
            # 處理字典類型
            elif field_type == dict:  # 改用小寫的 dict
                if isinstance(value, str):
                    if value.startswith('{'):
                        try:
                            return json.loads(value)
                        except json.JSONDecodeError:
                            pass
                elif isinstance(value, dict):
                    return value
                return field_info.default_factory() if hasattr(field_info, 'default_factory') else {}
                
            # 其他類型保持原樣
            return value
            
        except (ValueError, TypeError):
            # 轉換失敗時返回預設值
            if hasattr(field_info, 'default'):
                return field_info.default
            elif hasattr(field_info, 'default_factory'):
                return field_info.default_factory()
            return value

    def to_dict(self, include_env: bool = True) -> dict:
        """轉換為字典"""
        if include_env:
            # 包含環境變量設置的值
            return self._data.copy()
        else:
            # 只返回非環境變量設置的值
            result = {}
            for key, value in self._data.items():
                # 檢查該值是否來自環境變量
                env_key = f"{self._env_prefix}{key.upper()}"
                if env_key not in os.environ:
                    result[key] = value
            return result

    def _try_parse_json(self, value: str) -> Any:
        """嘗試解析 JSON 字符串"""
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    def _build_nested_dict(self, keys: List[str], value: str) -> Dict[str, Any]:
        """構建嵌套字典
        
        Args:
            keys: 鍵路徑列表
            value: 值
            
        Returns:
            構建好的字典
        """
        result = {}
        current = result
        
        # 構建除了最後一個鍵以外的路徑
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        
        # 設置最後一個值
        current[keys[-1]] = value
        return result

    def _merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """淺層合併兩個字典
        
        Args:
            dict1: 第一個字典
            dict2: 第二個字典
            
        Returns:
            合併後的字典
        """
        result = dict1.copy()
        result.update(dict2)
        return result

    def _load_config(self) -> None:
        """加載配置文件"""
        try:
            if not self._config_path:
                return
            
            path = Path(self._config_path)
            if not path.exists():
                logger.info(f"創建新配置文件: {path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding='utf-8')
                return
            
            content = path.read_text(encoding='utf-8')
            if not content:
                return
            
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ConfigError(f"無效的 JSON 格式: {str(e)}")
            
            # 更新內部數據
            self._data.update(data)
            # 處理嵌套結構並更新配置
            processed_data = self._process_nested_dict(data)
            self._config.update(processed_data)
            # 更新模型屬性
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            logger.info(f"已載入配置: {path}")
            
        except ConfigError:
            raise
        except Exception as e:
            logger.error(f"加載配置失敗: {str(e)}")
            raise ConfigError(f"加載配置失敗: {str(e)}")

    def load_file(self, path: Union[str, Path]) -> bool:
        """從文件載入配置"""
        try:
            path = Path(path)
            if not path.exists():
                logger.warning(f"配置文件不存在: {path}")
                return False  # 文件不存在時返回 False
            
            content = path.read_text(encoding='utf-8')
            if not content:
                return True
            
            # 根據文件擴展名選擇解析方式
            ext = path.suffix.lower()
            if ext == '.json':
                data = json.loads(content)
            elif ext in ('.yml', '.yaml'):
                data = yaml.safe_load(content)
            else:
                raise ConfigError(f"不支持的文件格式: {ext}")
            
            # 更新內部數據
            self._data.update(data)
            processed_data = self._process_nested_dict(data)
            self._config.update(processed_data)
            
            # 更新模型屬性
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            logger.info(f"已載入配置文件: {path}")
            return True
            
        except ConfigError:
            raise
        except Exception as e:
            logger.error(f"載入配置文件失敗: {str(e)}")
            return False
    
    def load_dict(self, data: Dict[str, Any]) -> bool:
        """從字典載入配置"""
        try:
            # 驗證數據
            for key, value in data.items():
                if isinstance(value, object) and not isinstance(value, (dict, list, str, int, float, bool)):
                    raise ConfigError(f"不支持的配置值類型: {type(value)}")
            
            # 更新內部數據
            self._data.update(data)
            # 處理嵌套結構並更新配置
            processed_data = self._process_nested_dict(data)
            self._config.update(processed_data)
            # 更新模型屬性
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            logger.info("已從字典載入配置")
            return True
            
        except ConfigError:
            raise
        except Exception as e:
            error_msg = f"從字典載入配置失敗: {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg)
    
    def _deep_merge(self, d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合併字典
        
        Args:
            d1: 第一個字典
            d2: 第二個字典
            
        Returns:
            合併後的字典
        """
        result = d1.copy()
        
        for key, value in d2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 如果兩邊都是字典，遞歸合併
                result[key] = self._deep_merge(result[key], value)
            else:
                # 否則直接覆蓋
                result[key] = value
            
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        try:
            parts = key.split('.')
            current = self._config
            
            for part in parts:
                if isinstance(current, dict):
                    if part in current:
                        current = current[part]
                    else:
                        return default
                else:
                    return default
            
            return current
        except Exception:
            return default

    def set(self, key: str, value: Any) -> bool:
        """設置配置值"""
        try:
            if not key:
                return False
                
            parts = key.split('.')
            current = self._config
            
            # 遍歷到最後一個部分
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    return False
                current = current[part]
                
            current[parts[-1]] = value
            return True
        except Exception:
            return False

    def merge(self, data: Dict[str, Any]) -> bool:
        """合併配置"""
        try:
            if data is None:
                raise ConfigError("合併數據不能為 None")
            
            # 驗證數據
            for key, value in data.items():
                if isinstance(value, object) and not isinstance(value, (dict, list, str, int, float, bool, type(None))):
                    raise ConfigError(f"不支持的配置值類型: {type(value)}")
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if isinstance(v, object) and not isinstance(v, (dict, list, str, int, float, bool, type(None))):
                            raise ConfigError(f"不支持的嵌套配置值類型: {type(v)}")
            
            # 處理嵌套結構
            processed_data = self._process_nested_dict(data)
            
            # 更新配置
            self._config = self._deep_merge(self._config, processed_data)
            self._data.update(data)
            
            # 更新模型屬性
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            return True
        except ConfigError:
            raise
        except Exception as e:
            error_msg = f"合併配置失敗: {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg)

    def load_env(self, prefix: str = "") -> bool:
        """載入環境變量
        
        Args:
            prefix: 環境變量前綴
            
        Returns:
            是否載入成功
        """
        try:
            # 暫時修改配置中的前綴
            original_prefix = self._env_prefix
            self._env_prefix = prefix
            
            # 載入環境變量
            env_data = self._load_env_vars()
            
            # 恢復原始前綴
            self._env_prefix = original_prefix
            
            if env_data:
                return self.merge(env_data)
            return True
            
        except Exception as e:
            logger.error(f"載入環境變量失敗: {str(e)}")
            return False
    
    def get_fields(self) -> Dict[str, ConfigField]:
        """獲取配置字段
        
        Returns:
            字段信息字典
        """
        fields = {}
        for name, field in self.model_fields.items():
            if name != "_config_path":
                fields[name] = ConfigField(
                    name=name,
                    type_=field.annotation,
                    default=field.default,
                    description=field.description or ""
                )
        return fields 

    def validate(self) -> None:
        """驗證配置"""
        try:
            # 驗證必填字段
            for field_name, field in self.model_fields.items():
                # 檢查是否為必填字段
                is_required = (
                    field.is_required or 
                    (field.default is None and field.default_factory is None)
                )
                
                if is_required:
                    # 檢查字段是否存在且不為 None
                    if not hasattr(self, field_name) or getattr(self, field_name) is None:
                        raise ConfigError(f"缺少必填配置項: {field_name}")
            
            # 檢查內部字典中的值
            for field_name, field in self.model_fields.items():
                if field_name in self._data or field_name in self._config:
                    value = self._data.get(field_name) or self._config.get(field_name)
                    
                    # 獲取基本類型
                    base_type = getattr(field.annotation, "__origin__", field.annotation)
                    if base_type == Union:  # 處理 Optional[str] 等類型
                        allowed_types = field.annotation.__args__
                        if not any(isinstance(value, t) for t in allowed_types):
                            raise ConfigError(
                                f"配置項 {field_name} 類型錯誤，"
                                f"應為 {field.annotation.__name__}，"
                                f"實際為 {type(value).__name__}"
                            )
                    else:
                        if not isinstance(value, base_type):
                            raise ConfigError(
                                f"配置項 {field_name} 類型錯誤，"
                                f"應為 {base_type.__name__}，"
                                f"實際為 {type(value).__name__}"
                            )
            
            # 驗證整個模型
            try:
                self.model_validate(self.model_dump())
            except Exception as e:
                raise ConfigError(f"配置驗證失敗: {str(e)}")
            
            logger.info("配置驗證通過")
            
        except ConfigError:
            logger.error("配置驗證失敗")
            raise
        except Exception as e:
            error_msg = f"配置驗證失敗: {str(e)}"
            logger.error(error_msg)
            raise ConfigError(error_msg)

    def __getitem__(self, key: str) -> Any:
        """支持字典訪問"""
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """支持字典設置"""
        setattr(self, key, value) 