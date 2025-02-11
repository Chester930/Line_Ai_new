import json
import hashlib
import base64
from typing import Any, Dict, Optional
from datetime import datetime, timezone, date
from pathlib import Path
from uuid import UUID
import uuid

def generate_session_id() -> str:
    """生成唯一的會話 ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"session_{timestamp}_{unique_id}"

def safe_json_loads(data: str) -> Dict:
    """安全的 JSON 解析"""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {}

def safe_file_write(path: Path, content: str, mode: str = "w") -> bool:
    """安全的文件寫入"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False

def truncate_text(text: str, max_length: int = 100) -> str:
    """截斷文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_timestamp(timestamp: Optional[float] = None) -> str:
    """格式化時間戳"""
    dt = datetime.fromtimestamp(timestamp or time.time(), timezone.utc)
    return dt.isoformat()

def calculate_text_tokens(text: str) -> int:
    """計算文本 token 數（簡單估算）"""
    return len(text) // 3

def encode_image_to_base64(image_path: Path) -> Optional[str]:
    """將圖片轉換為 base64"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

def sanitize_filename(filename: str) -> str:
    """清理文件名"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def get_file_extension(filename: str) -> str:
    """獲取文件擴展名"""
    return Path(filename).suffix.lower()

def is_valid_image_type(file_extension: str) -> bool:
    """檢查是否為有效的圖片類型"""
    valid_types = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    return file_extension.lower() in valid_types

class JSONEncoder(json.JSONEncoder):
    """自定義 JSON 編碼器"""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

class Helper:
    """工具類"""
    
    @staticmethod
    def load_json(
        file_path: Path,
        default: Any = None
    ) -> Any:
        """載入 JSON 文件"""
        try:
            if not file_path.exists():
                return default
            return json.loads(file_path.read_text())
        except Exception as e:
            from .logger import logger
            logger.error(f"載入 JSON 失敗: {str(e)}")
            return default
    
    @staticmethod
    def save_json(
        data: Any,
        file_path: Path,
        indent: int = 2
    ) -> bool:
        """保存 JSON 文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(
                json.dumps(
                    data,
                    indent=indent,
                    ensure_ascii=False,
                    cls=JSONEncoder
                )
            )
            return True
        except Exception as e:
            from .logger import logger
            logger.error(f"保存 JSON 失敗: {str(e)}")
            return False
    
    @staticmethod
    def merge_dicts(
        dict1: Dict,
        dict2: Dict,
        deep: bool = True
    ) -> Dict:
        """合併字典"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if (
                deep and
                key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)
            ):
                result[key] = Helper.merge_dicts(
                    result[key],
                    value,
                    deep=True
                )
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def truncate_text(
        text: str,
        max_length: int,
        suffix: str = "..."
    ) -> str:
        """截斷文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix 