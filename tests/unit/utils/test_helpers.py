import pytest
from pathlib import Path
from src.shared.utils.helpers import (
    generate_session_id,
    safe_json_loads,
    truncate_text,
    calculate_text_tokens,
    sanitize_filename,
    is_valid_image_type,
    safe_file_write,
    Helper,
    encode_image_to_base64,
    get_file_extension
)

def test_generate_session_id():
    session_id = generate_session_id()
    assert isinstance(session_id, str)
    assert session_id.startswith("session_")
    assert len(session_id) > 20

def test_safe_json_loads():
    valid_json = '{"key": "value"}'
    assert safe_json_loads(valid_json) == {"key": "value"}
    
    invalid_json = 'invalid'
    assert safe_json_loads(invalid_json) == {}

def test_truncate_text():
    text = "a" * 200
    truncated = truncate_text(text, max_length=100)
    assert len(truncated) == 100
    assert truncated.endswith("...")

def test_calculate_text_tokens():
    """測試文本 token 計算"""
    text = "Hello, World!"
    tokens = calculate_text_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)

def test_sanitize_filename():
    filename = 'test<>:"/\\|?*file.txt'
    sanitized = sanitize_filename(filename)
    assert all(c not in sanitized for c in '<>:"/\\|?*')

def test_valid_image_types():
    """測試圖片類型驗證"""
    assert is_valid_image_type('.jpg')
    assert is_valid_image_type('.png')
    assert not is_valid_image_type('.txt')
    assert not is_valid_image_type('.exe')

def test_safe_file_write(tmp_path):
    test_file = tmp_path / "test.txt"
    assert safe_file_write(test_file, "test content")
    assert test_file.read_text() == "test content"

def test_helper_json_operations(tmp_path):
    """測試 JSON 文件操作"""
    test_file = tmp_path / "test.json"
    
    # 測試保存 JSON
    data = {"key": "value", "nested": {"test": True}}
    assert Helper.save_json(data, test_file)
    
    # 測試載入 JSON
    loaded = Helper.load_json(test_file)
    assert loaded == data
    
    # 測試錯誤處理
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("invalid json")
    assert Helper.load_json(invalid_file) is None

def test_helper_merge_dicts():
    """測試字典合併"""
    dict1 = {"a": 1, "b": {"c": 2}}
    dict2 = {"b": {"d": 3}, "e": 4}
    
    # 測試深度合併
    result = Helper.merge_dicts(dict1, dict2, deep=True)
    assert result["a"] == 1
    assert result["b"] == {"c": 2, "d": 3}
    assert result["e"] == 4
    
    # 測試淺合併
    result = Helper.merge_dicts(dict1, dict2, deep=False)
    assert result["b"] == {"d": 3}  # b 被完全覆蓋

def test_encode_image_to_base64(tmp_path):
    """測試圖片轉 base64"""
    # 創建測試圖片
    image_path = tmp_path / "test.png"
    image_path.write_bytes(b"test image content")
    
    # 測試編碼
    result = encode_image_to_base64(image_path)
    assert isinstance(result, str)
    assert len(result) > 0
    
    # 測試不存在的文件
    non_existent = tmp_path / "non_existent.png"
    assert encode_image_to_base64(non_existent) is None

def test_get_file_extension():
    """測試獲取文件擴展名"""
    assert get_file_extension("test.jpg") == ".jpg"
    assert get_file_extension("test.tar.gz") == ".gz"
    assert get_file_extension("test") == ""
    assert get_file_extension(".gitignore") == ".gitignore"

def test_helper_edge_cases():
    """測試 Helper 類的邊界情況"""
    # 測試空字典合併
    result = Helper.merge_dicts({}, {})
    assert result == {}
    
    # 測試 None 值處理
    assert Helper.load_json(None) is None
    
    # 測試無效的 JSON 文件
    with pytest.raises(Exception):
        Helper.save_json({"key": object()}, Path("test.json"))

def test_helper_load_json_error(tmp_path):
    """測試 JSON 載入錯誤處理"""
    # 創建無效的 JSON 文件
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid")
    
    # 測試載入錯誤
    result = Helper.load_json(invalid_file)
    assert result is None
    
    # 測試使用默認值
    result = Helper.load_json(invalid_file, default={"key": "value"})
    assert result == {"key": "value"}

def test_helper_merge_dicts_edge_cases():
    """測試字典合併的邊界情況"""
    # 測試 None 值
    assert Helper.merge_dicts(None, {}) == {}
    assert Helper.merge_dicts({}, None) == {}
    
    # 測試非字典值
    dict1 = {"a": 1, "b": {"c": 2}}
    dict2 = {"b": "not a dict"}
    result = Helper.merge_dicts(dict1, dict2, deep=True)
    assert result["b"] == "not a dict"  # 非字典值應該覆蓋字典 