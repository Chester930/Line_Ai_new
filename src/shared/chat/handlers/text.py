from typing import Optional
from ...utils.logger import logger
from ..session import session_manager

async def handle_text_message(user_id: str, message: str) -> str:
    """處理文字消息"""
    try:
        # 獲取用戶會話
        session = session_manager.get_session(user_id)
        
        # 檢查是否是命令
        if message.startswith('/'):
            return await handle_command(session, message)
        
        # 生成回應
        response = await session.send_message(message)
        return response
        
    except Exception as e:
        logger.error(f"處理文字消息時發生錯誤: {str(e)}")
        return "抱歉，處理您的消息時發生錯誤。"

async def handle_command(session, command: str) -> str:
    """處理命令"""
    cmd_parts = command[1:].split()
    cmd = cmd_parts[0].lower()
    
    if cmd == 'clear':
        session.clear_context()
        return "已清空對話記錄。"
        
    elif cmd == 'switch':
        if len(cmd_parts) < 2:
            return "請指定要切換的模型類型。"
        
        model_type = cmd_parts[1].lower()
        if session.switch_model(model_type):
            return f"已切換至 {model_type} 模型。"
        else:
            return "切換模型失敗，請確認模型類型是否正確。"
    
    return f"未知的命令: {cmd}" 