import pytest
from pathlib import Path
from src.shared.utils.helpers import (
    generate_session_id,
    safe_json_loads,
    truncate_text,
    calculate_text_tokens,
    sanitize_filename,
    is_valid_image_type
)

def test_session_id_generation():
    """測試會話 ID 生成"""
    session_id = generate_session_id("user123")
    assert session_id.startswith("sess_")
    assert len(session_id) == 17  # "sess_" + 12 chars

def test_safe_json_loads():
    """測試安全 JSON 解析"""
    # 有效 JSON
    assert safe_json_loads('{"key": "value"}') == {"key": "value"}
    # 無效 JSON
    assert safe_json_loads('invalid json') == {}

def test_truncate_text():
    """測試文本截斷"""
    text = "a" * 200
    truncated = truncate_text(text, 50)
    assert len(truncated) == 50
    assert truncated.endswith("...")

def test_calculate_text_tokens():
    """測試文本 token 計算"""
    text = "Hello, World!"
    tokens = calculate_text_tokens(text)
    assert tokens > 0

def test_sanitize_filename():
    """測試文件名清理"""
    filename = 'test/file:name*.txt'
    sanitized = sanitize_filename(filename)
    assert '/' not in sanitized
    assert ':' not in sanitized
    assert '*' not in sanitized

def test_valid_image_types():
    """測試圖片類型驗證"""
    assert is_valid_image_type('.jpg')
    assert is_valid_image_type('.png')
    assert not is_valid_image_type('.txt')
    assert not is_valid_image_type('.exe') 