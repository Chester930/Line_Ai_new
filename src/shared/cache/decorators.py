import hashlib
import inspect
from functools import wraps
from typing import Any, Optional, Union, Callable
from datetime import timedelta
from .base import BaseCache
from ..utils.logger import logger

def cache(
    expire: Optional[Union[int, timedelta]] = None,
    key_prefix: str = "",
    cache_null: bool = False
):
    """快取裝飾器"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(
            self,
            *args,
            cache_instance: Optional[BaseCache] = None,
            **kwargs
        ) -> Any:
            if not cache_instance:
                return await func(self, *args, **kwargs)
            
            # 生成快取鍵
            cache_key = _generate_cache_key(
                func,
                key_prefix,
                args,
                kwargs
            )
            
            # 嘗試獲取快取
            cached_value = await cache_instance.get(cache_key)
            if cached_value is not None:
                logger.debug(f"快取命中: {cache_key}")
                return cached_value
            
            # 執行原函數
            result = await func(self, *args, **kwargs)
            
            # 如果結果為 None 且不快取空值，則直接返回
            if result is None and not cache_null:
                return result
            
            # 設置快取
            await cache_instance.set(cache_key, result, expire)
            logger.debug(f"設置快取: {cache_key}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(
            self,
            *args,
            cache_instance: Optional[BaseCache] = None,
            **kwargs
        ) -> Any:
            if not cache_instance:
                return func(self, *args, **kwargs)
            
            # 生成快取鍵
            cache_key = _generate_cache_key(
                func,
                key_prefix,
                args,
                kwargs
            )
            
            # 嘗試獲取快取 (同步方式)
            import asyncio
            cached_value = asyncio.run(cache_instance.get(cache_key))
            if cached_value is not None:
                logger.debug(f"快取命中: {cache_key}")
                return cached_value
            
            # 執行原函數
            result = func(self, *args, **kwargs)
            
            # 如果結果為 None 且不快取空值，則直接返回
            if result is None and not cache_null:
                return result
            
            # 設置快取 (同步方式)
            asyncio.run(cache_instance.set(cache_key, result, expire))
            logger.debug(f"設置快取: {cache_key}")
            
            return result
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def _generate_cache_key(
    func: Callable,
    prefix: str,
    args: tuple,
    kwargs: dict
) -> str:
    """生成快取鍵"""
    # 基礎鍵
    key_parts = [func.__module__, func.__name__]
    
    # 添加前綴
    if prefix:
        key_parts.insert(0, prefix)
    
    # 添加參數
    if args:
        key_parts.extend([str(arg) for arg in args])
    
    # 添加關鍵字參數
    if kwargs:
        for k, v in sorted(kwargs.items()):
            key_parts.extend([k, str(v)])
    
    # 生成最終鍵
    key = ":".join(key_parts)
    return hashlib.md5(key.encode()).hexdigest() 