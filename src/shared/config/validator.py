from typing import Any, Callable, List, Optional, Pattern, Union, Dict
import re
from .base import BaseConfig
from ..utils.logger import logger

class ValidationError(Exception):
    """配置驗證錯誤"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        self.message = f"{field}: {message}" if field else message
        super().__init__(self.message)

class ValidationRule:
    """配置驗證規則"""
    
    def __init__(self, field: str, message: str = None):
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
        self._nested_rules = None
        self._list_item_rule = None
    
    def required(self, message: str = None) -> 'ValidationRule':
        """設置必填規則"""
        self._required = True
        if message:
            self.message = message
        return self
    
    def type(self, type_: type, message: str = None) -> 'ValidationRule':
        """設置類型規則"""
        self._type = type_
        if message:
            self.message = message
        return self
    
    def min_value(self, value: Union[int, float], message: str = None) -> 'ValidationRule':
        """設置最小值規則"""
        self._min_value = value
        if message:
            self.message = message
        return self
    
    def max_value(self, value: Union[int, float], message: str = None) -> 'ValidationRule':
        """設置最大值規則"""
        self._max_value = value
        if message:
            self.message = message
        return self
    
    def min_length(self, length: int, message: str = None) -> 'ValidationRule':
        """設置最小長度規則"""
        self._min_length = length
        if message:
            self.message = message
        return self
    
    def max_length(self, length: int, message: str = None) -> 'ValidationRule':
        """設置最大長度規則"""
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
        """設置自定義驗證規則
        
        Args:
            validator: 接收單個參數的驗證函數
            message: 錯誤消息
        """
        # 包裝驗證器以統一參數
        def wrapped_validator(value: Any, _: Any = None) -> bool:
            return validator(value)
        self._custom_validator = wrapped_validator
        if message:
            self.message = message
        return self
    
    def nested(self, rules: Dict[str, 'ValidationRule'], message: str = None) -> 'ValidationRule':
        """設置嵌套驗證規則"""
        self._nested_rules = rules
        if message:
            self.message = message
        return self
    
    def list_items(self, rule: 'ValidationRule', message: str = None) -> 'ValidationRule':
        """設置列表項目驗證規則"""
        self._list_item_rule = rule
        if message:
            self.message = message
        return self
    
    def validate(self, value: Any, config: Any = None) -> bool:
        """驗證值是否符合規則
        
        Args:
            value: 要驗證的值
            config: 配置對象(用於自定義驗證)
            
        Returns:
            是否通過驗證
            
        Raises:
            ValidationError: 驗證失敗時拋出
        """
        try:
            # 檢查必填
            if self._required and value is None:
                raise ValidationError(
                    self.message or f"{self.field} 不能為空",
                    self.field
                )
            
            # 如果值為 None 且非必填,則跳過其他驗證
            if value is None and not self._required:
                return True
            
            # 檢查類型
            if self._type and not isinstance(value, self._type):
                raise ValidationError(
                    self.message or f"{self.field} 必須是 {self._type.__name__} 類型",
                    self.field
                )
            
            # 檢查最小值
            if self._min_value is not None:
                if isinstance(value, (int, float)) and value < self._min_value:
                    raise ValidationError(
                        self.message or f"{self.field} 不能小於 {self._min_value}",
                        self.field
                    )
            
            # 檢查最大值
            if self._max_value is not None:
                if isinstance(value, (int, float)) and value > self._max_value:
                    raise ValidationError(
                        self.message or f"{self.field} 不能大於 {self._max_value}",
                        self.field
                    )
            
            # 檢查最小長度
            if self._min_length is not None:
                if hasattr(value, '__len__') and len(value) < self._min_length:
                    raise ValidationError(
                        self.message or f"{self.field} 長度不能小於 {self._min_length}",
                        self.field
                    )
            
            # 檢查最大長度
            if self._max_length is not None:
                if hasattr(value, '__len__') and len(value) > self._max_length:
                    raise ValidationError(
                        self.message or f"{self.field} 長度不能大於 {self._max_length}",
                        self.field
                    )
            
            # 檢查正則表達式
            if self._pattern and isinstance(value, str):
                if not self._pattern.match(value):
                    raise ValidationError(
                        self.message or f"{self.field} 格式不正確",
                        self.field
                    )
            
            # 檢查自定義驗證
            if self._custom_validator:
                if not self._custom_validator(value, config):
                    raise ValidationError(
                        self.message or f"{self.field} 驗證失敗",
                        self.field
                    )
            
            # 檢查嵌套規則
            if self._nested_rules and isinstance(value, dict):
                for key, rule in self._nested_rules.items():
                    if key in value:
                        if not rule.validate(value[key], config):
                            raise ValidationError(
                                self.message or f"{self.field}.{key} 驗證失敗",
                                f"{self.field}.{key}"
                            )
            
            # 檢查列表項目
            if self._list_item_rule and isinstance(value, list):
                for i, item in enumerate(value):
                    try:
                        if not self._list_item_rule.validate(item, config):
                            raise ValidationError(
                                self.message or f"{self.field}[{i}] 驗證失敗",
                                f"{self.field}[{i}]"
                            )
                    except ValidationError as e:
                        raise ValidationError(
                            f"{self.field}[{i}]: {str(e)}",
                            f"{self.field}[{i}]"
                        )
            
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(str(e), self.field)

class ConfigValidator:
    """配置驗證器"""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule) -> None:
        """添加驗證規則"""
        self.rules.append(rule)
    
    def validate(self, config: Any, data: Dict = None) -> bool:
        """驗證配置
        
        Args:
            config: 配置對象
            data: 額外的驗證數據
            
        Returns:
            是否通過驗證
            
        Raises:
            ValidationError: 驗證失敗時拋出
        """
        errors = []
        
        for rule in self.rules:
            try:
                # 獲取要驗證的值
                value = None
                if data and rule.field in data:
                    value = data[rule.field]
                elif hasattr(config, rule.field):
                    value = getattr(config, rule.field)
                
                # 執行驗證
                if not rule.validate(value, config):
                    errors.append(f"{rule.field} 驗證失敗")
                    
            except ValidationError as e:
                errors.append(str(e))
        
        if errors:
            error_message = "\n".join(errors)
            logger.error(f"驗證失敗:\n{error_message}")
            raise ValueError(error_message)
        
        return True