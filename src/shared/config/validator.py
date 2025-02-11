from typing import Any, Callable, List, Optional, Pattern, Union, Dict, Type
import re
from .base import BaseConfig
from ..utils.logger import logger

class ValidationError(Exception):
    """配置驗證錯誤"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        # 直接使用消息，不再添加字段名前綴
        self.message = message
        super().__init__(self.message)

class ValidationRule:
    """驗證規則"""
    def __init__(self, field: str = None, message: Optional[str] = None):
        """初始化驗證規則
        
        Args:
            field: 字段名稱
            message: 錯誤消息
        """
        self.field = field
        self.message = message
        self._required = False
        self._type = None
        self._min_value = None
        self._max_value = None
        self._min_length = None
        self._max_length = None
        self._pattern = None
        self._custom_validator = None
        self._custom_message = None
        self._nested_rules = None
        self._list_item_rule = None
        self.is_optional = False

    def required(self, message: Optional[str] = None) -> 'ValidationRule':
        """設置必填"""
        self._required = True
        self._custom_message = message
        return self

    def type(self, type_: Type, message: Optional[str] = None) -> 'ValidationRule':
        """設置類型"""
        self._type = type_
        self._custom_message = message
        return self

    def min_value(self, value: Union[int, float], message: Optional[str] = None) -> 'ValidationRule':
        """設置最小值"""
        self._min_value = value
        self._custom_message = message
        return self

    def max_value(self, value: Union[int, float], message: Optional[str] = None) -> 'ValidationRule':
        """設置最大值"""
        self._max_value = value
        self._custom_message = message
        return self

    def range(self, min_value: Union[int, float], max_value: Union[int, float], message: Optional[str] = None) -> 'ValidationRule':
        """設置值範圍"""
        self._min_value = min_value
        self._max_value = max_value
        self._custom_message = message
        return self

    def min_length(self, length: int, message: str = None) -> 'ValidationRule':
        """最小長度驗證"""
        self._min_length = length
        if message:
            self.message = message
        return self
    
    def max_length(self, length: int, message: str = None) -> 'ValidationRule':
        """最大長度驗證"""
        self._max_length = length
        if message:
            self.message = message
        return self
    
    def pattern(self, pattern: Union[str, Pattern], message: str = None) -> 'ValidationRule':
        """設置正則表達式規則"""
        if isinstance(pattern, str):
            self._pattern = re.compile(pattern)
        else:
            self._pattern = pattern
        if message:
            self.message = message
        return self
    
    def custom(self, validator: Callable[[Any], bool], message: str = None) -> 'ValidationRule':
        """設置自定義驗證規則"""
        self._custom_validator = validator
        if message:
            self.message = message
        return self
    
    def nested(self, rules: Dict[str, 'ValidationRule']) -> 'ValidationRule':
        """設置嵌套驗證規則"""
        # 確保所有規則都有字段名
        for key, rule in rules.items():
            if not hasattr(rule, 'field'):
                rule.field = key
        self._nested_rules = rules
        return self
    
    def list_items(self, rule: 'ValidationRule') -> 'ValidationRule':
        """設置列表項目驗證規則"""
        self._list_item_rule = rule
        return self
    
    def optional(self) -> "ValidationRule":
        """標記字段為可選"""
        self.is_optional = True
        return self
    
    # 為了向後兼容
    min = min_value
    max = max_value

    async def validate(self, value: Any) -> bool:
        """驗證值"""
        try:
            # 可選字段處理(新增空值檢查)
            if self.is_optional:
                if value is None or value == "":
                    return True
                if isinstance(value, (list, dict)) and not value:
                    return True
            
            # 必填檢查
            if self._required and (value is None or value == ""):
                raise ValidationError(f"{self.field} 不能為空")
            
            if value is not None:
                # 類型檢查(新增字符串轉換邏輯)
                if self._type and not isinstance(value, self._type):
                    if self._type in (int, float):
                        try:
                            converted_value = self._type(value)
                            value = converted_value  # 更新轉換後的值
                        except (TypeError, ValueError):
                            raise ValidationError(f"{self.field} 必須是 {self._type.__name__}")
                    else:
                        raise ValidationError(f"{self.field} 必須是 {self._type.__name__}")
            
            # 自定義驗證
            if self._custom_validator:
                if not self._custom_validator(value):
                    raise ValidationError(self._custom_message or f"{self.field} 驗證失敗")
            
            # 數值範圍檢查
            if self._min_value is not None or self._max_value is not None:
                # 確保數值類型
                try:
                    if isinstance(value, str):
                        num_value = float(value)
                        if self._type is int and not num_value.is_integer():
                            raise ValueError
                        num_value = int(num_value) if self._type is int else num_value
                    else:
                        num_value = float(value)
                except (TypeError, ValueError):
                    raise ValidationError(f"{self.field} 必須是數值類型")

                # 嚴格檢查整數類型
                if self._type is int and not isinstance(num_value, int):
                    raise ValidationError(f"{self.field} 必須是整數")
                
                # 邊界檢查
                if self._min_value is not None and num_value < self._min_value:
                    raise ValidationError(f"{self.field} 不能小於 {self._min_value}")
                if self._max_value is not None and num_value > self._max_value:
                    raise ValidationError(f"{self.field} 不能大於 {self._max_value}")
            
            # 長度檢查
            if self._min_length is not None or self._max_length is not None:
                value_str = str(value)
                if self._min_length is not None and len(value_str) < self._min_length:
                    raise ValidationError(f"{self.field} 長度不能小於 {self._min_length}")
                if self._max_length is not None and len(value_str) > self._max_length:
                    raise ValidationError(f"{self.field} 長度不能大於 {self._max_length}")
            
            # 正則驗證
            if self._pattern:
                if not re.match(self._pattern, str(value)):
                    raise ValidationError(f"{self.field} 格式不正確")
            
            return True
        except ValidationError as e:
            logger.error(f"驗證失敗: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"驗證過程中發生意外錯誤: {str(e)}")
            raise ValidationError(f"系統錯誤: {str(e)}") from e

    def length(self, min: Optional[int] = None, max: Optional[int] = None, message: Optional[str] = None) -> 'ValidationRule':
        """設置長度範圍"""
        self._min_length = min
        self._max_length = max
        self._custom_message = message
        return self

class ConfigValidator:
    """配置驗證器"""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
    
    def _get_value(self, config: Any, field: str) -> Any:
        """獲取配置值"""
        if hasattr(config, 'get'):
            return config.get(field)
        elif hasattr(config, field):
            return getattr(config, field)
        return None
    
    def add_rule(self, rule: ValidationRule) -> None:
        """添加驗證規則"""
        self.rules.append(rule)
    
    async def validate(self, config: Union[Dict, BaseConfig]) -> bool:
        """异步验证配置"""
        try:
            if isinstance(config, BaseConfig):
                config_data = config.model_dump()
            else:
                config_data = config
            
            for rule in self.rules:
                value = self._get_value(config_data, rule.field)
                if not await rule.validate(value):
                    return False
            return True
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"驗證過程中發生意外錯誤: {str(e)}")
            raise ValidationError(f"系統錯誤: {str(e)}") from e

    async def validate(self, config: BaseConfig) -> bool:
        try:
            # 执行所有验证规则...
            return True
        except ValidationError:
            return False