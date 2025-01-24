import pytest
from pathlib import Path
from datetime import datetime
from src.shared.prompts.base import Prompt, PromptError
from src.shared.prompts.memory import MemoryPromptManager
from src.shared.prompts.loader import PromptLoader
from src.shared.session.base import Message

@pytest.fixture
def prompt():
    """測試提示詞"""
    return Prompt(
        name="test",
        content="Hello, {name}!",
        description="Test prompt",
        tags=["test", "greeting"],
        variables={"name": "world"}
    )

@pytest.fixture
def prompt_manager():
    """提示詞管理器"""
    return MemoryPromptManager()

def test_prompt_formatting(prompt):
    """測試提示詞格式化"""
    # 使用默認變量
    result = prompt.format()
    assert result == "Hello, world!"
    
    # 使用自定義變量
    result = prompt.format(name="Alice")
    assert result == "Hello, Alice!"
    
    # 測試缺少變量
    with pytest.raises(PromptError):
        prompt.format(wrong_var="test")

@pytest.mark.asyncio
async def test_prompt_manager(prompt_manager, prompt):
    """測試提示詞管理器"""
    # 保存提示詞
    assert await prompt_manager.save_prompt(prompt)
    
    # 獲取提示詞
    saved_prompt = await prompt_manager.get_prompt("test")
    assert saved_prompt is not None
    assert saved_prompt.name == prompt.name
    assert saved_prompt.content == prompt.content
    
    # 列出提示詞
    prompts = await prompt_manager.list_prompts()
    assert len(prompts) == 1
    assert prompts[0].name == prompt.name
    
    # 按標籤過濾
    prompts = await prompt_manager.list_prompts(tags=["greeting"])
    assert len(prompts) == 1
    prompts = await prompt_manager.list_prompts(tags=["nonexistent"])
    assert len(prompts) == 0
    
    # 刪除提示詞
    assert await prompt_manager.delete_prompt("test")
    assert await prompt_manager.get_prompt("test") is None

@pytest.mark.asyncio
async def test_message_formatting(prompt_manager):
    """測試消息格式化"""
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi")
    ]
    
    # 不帶系統提示詞
    formatted = await prompt_manager.format_messages(messages)
    assert len(formatted) == 2
    
    # 帶系統提示詞
    formatted = await prompt_manager.format_messages(
        messages,
        system_prompt="Be helpful."
    )
    assert len(formatted) == 3
    assert formatted[0].role == "system"
    assert formatted[0].content == "Be helpful."

@pytest.mark.asyncio
async def test_prompt_loader(tmp_path):
    """測試提示詞加載器"""
    # 創建測試文件
    file_path = tmp_path / "test.yml"
    file_path.write_text("""
test_prompt:
  content: "Hello, {name}!"
  description: "Test prompt"
  tags: ["test", "greeting"]
  variables:
    name: world
""")
    
    # 加載文件
    prompts = await PromptLoader.load_from_file(file_path)
    assert len(prompts) == 1
    assert prompts[0].name == "test_prompt"
    assert prompts[0].content == "Hello, {name}!"
    
    # 加載目錄
    prompts = await PromptLoader.load_from_directory(tmp_path)
    assert len(prompts) == 1 