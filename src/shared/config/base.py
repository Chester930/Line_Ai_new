from typing import Any, Dict, Optional, Type, List, ClassVar, Union
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
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

class BaseConfig(BaseModel):
    """基礎配置類"""
    config_path: Optional[Path] = Field(default=None, description="配置文件路徑")
    
    model_config = ConfigDict(
        validate_assignment=True,
        frozen=False,
        extra="allow",
        arbitrary_types_allowed=True
    )
    
    _config: Dict[str, Any] = PrivateAttr(default_factory=dict)
    
    def __init__(self, **data):
        """初始化配置
        
        Args:
            **data: 配置數據
        """
        try:
            # 保存原始數據
            initial_data = data.copy()
            
            # 確保 debug 默認為 False
            if 'debug' not in initial_data:
                initial_data['debug'] = False
            elif isinstance(initial_data['debug'], str):
                initial_data['debug'] = initial_data['debug'].lower() in ('true', '1', 'yes', 'on')
            else:
                initial_data['debug'] = bool(initial_data['debug'])
            
            # 先初始化基類
            super().__init__(**initial_data)
            
            # 初始化內部配置字典
            self._config = {}
            for field_name, field in self.model_fields.items():
                if field_name != 'config_path':
                    value = getattr(self, field_name, None)
                    if value is not None:
                        self._config[field_name] = value
            
            # 載入配置文件
            if self.config_path:
                self._load_config()
            
            # 載入環境變量
            env_data = self._load_env_vars()
            if env_data:
                self.merge(env_data)
            
        except Exception as e:
            logger.error(f"初始化配置失敗: {str(e)}")
            raise ConfigError(f"初始化配置失敗: {str(e)}")
    
    def _try_parse_json(self, value: str) -> Any:
        """嘗試解析 JSON 字符串"""
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    def _convert_value(self, value: str, field_info: Any) -> Any:
        """轉換值為指定類型"""
        try:
            # 首先嘗試 JSON 解析
            try:
                parsed_value = json.loads(value)
                # 如果解析成功且類型匹配，直接返回
                if isinstance(parsed_value, (list, dict)):
                    return parsed_value
            except json.JSONDecodeError:
                parsed_value = value
            
            # 根據字段類型轉換值
            if field_info.annotation == bool:
                return str(parsed_value).lower() in ("true", "1", "yes", "on")
            elif field_info.annotation == int:
                return int(parsed_value)
            elif field_info.annotation == float:
                return float(parsed_value)
            elif field_info.annotation == Path:
                return Path(parsed_value)
            elif field_info.annotation == List:
                if isinstance(parsed_value, str):
                    # 移除可能的方括號並分割
                    cleaned = parsed_value.strip('[]').replace('"', '').replace("'", "")
                    return [v.strip() for v in cleaned.split(',') if v.strip()]
                return list(parsed_value)
            elif field_info.annotation == Dict:
                if isinstance(parsed_value, str):
                    return json.loads(parsed_value)
                return dict(parsed_value)
            else:
                return parsed_value
                
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"值轉換失敗: {str(e)}")
            return None
    
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

    def _load_env_vars(self) -> Dict[str, Any]:
        """載入環境變量
        
        Returns:
            環境變量數據
        """
        try:
            env_data = {}
            env_prefix = self.model_config.get("env_prefix", "")
            delimiter = self.model_config.get("env_nested_delimiter", "__")
            
            # 獲取所有相關的環境變量
            env_vars = {
                k: v for k, v in os.environ.items()
                if k.startswith(env_prefix.upper())
            }
            
            # 處理環境變量
            for env_key, env_value in env_vars.items():
                try:
                    # 移除前綴並轉換為小寫
                    key = env_key[len(env_prefix):].lower() if env_prefix else env_key.lower()
                    
                    # 處理嵌套鍵
                    if delimiter in key:
                        keys = key.split(delimiter)
                        current = env_data
                        for k in keys[:-1]:
                            if k not in current:
                                current[k] = {}
                            current = current[k]
                        current[keys[-1]] = self._try_parse_json(env_value)
                    else:
                        env_data[key] = self._try_parse_json(env_value)
                    
                except Exception as e:
                    logger.warning(f"處理環境變量 {env_key} 失敗: {str(e)}")
                    continue
            
            return env_data
            
        except Exception as e:
            logger.error(f"載入環境變量失敗: {str(e)}")
            return {}
    
    def _load_config(self) -> None:
        """載入配置"""
        try:
            if not self.config_path:
                return
            
            if not self.config_path.exists():
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self.config_path.write_text("{}")
                return
            
            config_data = json.loads(self.config_path.read_text())
            
            # 保持初始的 debug 值
            debug_value = self._config.get('debug', False)
            
            # 更新配置
            self._config.update(config_data)
            
            # 恢復 debug 值
            self._config['debug'] = debug_value
            
            # 更新實例屬性
            for key, value in self._config.items():
                if hasattr(self, key) and key != 'debug':
                    setattr(self, key, value)
            
            logger.info(f"已載入配置: {self.config_path}")
            
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
    
    def load_file(self, path: Union[str, Path]) -> bool:
        """從文件載入配置
        
        Args:
            path: 配置文件路徑
            
        Returns:
            是否載入成功
        """
        try:
            self.config_path = Path(path)
            self._load_config()
            return True
        except Exception as e:
            logger.error(f"從文件載入配置失敗: {str(e)}")
            return False
    
    def load_dict(self, data: Dict[str, Any]) -> bool:
        """從字典載入配置
        
        Args:
            data: 配置數據
            
        Returns:
            是否載入成功
        """
        try:
            return self.update(data)
            
        except Exception as e:
            logger.error(f"從字典載入配置失敗: {str(e)}")
            return False
    
    def save(self) -> bool:
        """保存配置"""
        try:
            if not self.config_path:
                logger.warning("未指定配置文件路徑")
                return False
            
            # 確保目標目錄存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 獲取當前配置數據
            data = self.to_dict()
            
            # 根據文件擴展名選擇保存方式
            ext = self.config_path.suffix.lower()
            if ext == '.json':
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif ext in ('.yml', '.yaml'):
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(data, f, allow_unicode=True)
            else:
                raise ConfigError(f"不支持的配置文件格式: {ext}")
            
            logger.info(f"已保存配置: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False
    
    def update(self, data: Dict[str, Any]) -> bool:
        """更新配置
        
        Args:
            data: 新的配置數據
            
        Returns:
            是否更新成功
        """
        try:
            # 更新配置字典
            self._config = self._deep_merge(self._config, data)
            
            # 更新模型屬性
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"更新配置失敗: {str(e)}")
            return False
    
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
        """獲取配置值
        
        Args:
            key: 配置鍵
            default: 默認值
            
        Returns:
            配置值
        """
        try:
            if '.' in key:
                parts = key.split('.')
                current = self._config
                for part in parts:
                    if not isinstance(current, dict) or part not in current:
                        return default
                    current = current[part]
                return current
            return self._config.get(key, default)
            
        except Exception as e:
            logger.error(f"獲取配置值失敗: {str(e)}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """設置配置值
        
        Args:
            key: 配置鍵
            value: 配置值
            
        Returns:
            是否設置成功
            
        Raises:
            ConfigError: 當配置鍵無效時
        """
        try:
            # 驗證鍵值
            if not key or not isinstance(key, str):
                raise ConfigError("配置鍵不能為空且必須是字符串")
            
            # 如果是實例屬性，直接設置
            if hasattr(self, key):
                setattr(self, key, value)
                return True
            
            # 否則設置到配置字典
            keys = key.split('.')
            current = self._config
            
            # 遍歷到最後一層
            for k in keys[:-1]:
                if not k:  # 檢查空鍵
                    raise ConfigError("配置鍵的層級不能為空")
                current = current.setdefault(k, {})
                
                # 確保中間節點是字典
                if not isinstance(current, dict):
                    raise ConfigError(f"配置路徑 '{key}' 無效：中間節點必須是字典")
            
            # 設置值
            if not keys[-1]:  # 檢查最後一個鍵
                raise ConfigError("配置鍵的最後一層不能為空")
            
            current[keys[-1]] = value
            return True
            
        except ConfigError:
            raise
        except Exception as e:
            logger.error(f"設置配置失敗: {str(e)}")
            return False
    
    def merge(self, data: Dict[str, Any]) -> bool:
        """合併配置
        
        Args:
            data: 要合併的配置數據
            
        Returns:
            是否合併成功
        """
        try:
            # 處理點號分隔的鍵
            processed_data = {}
            for key, value in data.items():
                if '.' in key:
                    parts = key.split('.')
                    current = processed_data
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    processed_data[key] = value
            
            # 深度合併配置
            self._config = self._deep_merge(self._config, processed_data)
            
            # 更新實例屬性
            for key, value in processed_data.items():
                if hasattr(self, key):
                    if isinstance(value, dict):
                        current_value = getattr(self, key, {})
                        if isinstance(current_value, dict):
                            current_value.update(value)
                            setattr(self, key, current_value)
                    else:
                        setattr(self, key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"合併配置失敗: {str(e)}")
            return False
    
    def load_env(self, prefix: str = "") -> bool:
        """載入環境變量
        
        Args:
            prefix: 環境變量前綴
            
        Returns:
            是否載入成功
        """
        try:
            # 暫時修改配置中的前綴
            original_prefix = self.model_config.get("env_prefix", "")
            self.model_config["env_prefix"] = prefix
            
            # 載入環境變量
            env_data = self._load_env_vars()
            
            # 恢復原始前綴
            self.model_config["env_prefix"] = original_prefix
            
            if env_data:
                return self.merge(env_data)
            return True
            
        except Exception as e:
            logger.error(f"載入環境變量失敗: {str(e)}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典
        
        Returns:
            配置字典
        """
        try:
            # 返回完整的配置數據
            return copy.deepcopy(self._config)
        except Exception as e:
            logger.error(f"轉換配置為字典失敗: {str(e)}")
            return {}
    
    def get_fields(self) -> Dict[str, ConfigField]:
        """獲取配置字段
        
        Returns:
            字段信息字典
        """
        fields = {}
        for name, field in self.model_fields.items():
            if name != "config_path":
                fields[name] = ConfigField(
                    name=name,
                    type_=field.annotation,
                    default=field.default,
                    description=field.description or ""
                )
        return fields 