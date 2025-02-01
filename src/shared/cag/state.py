from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class DialogueState(Enum):
    """對話狀態枚舉"""
    INIT = "init"           # 初始狀態
    ACTIVE = "active"       # 活躍對話
    WAITING = "waiting"     # 等待用戶
    PROCESSING = "processing"  # 處理中
    ENDED = "ended"         # 對話結束
    ERROR = "error"         # 錯誤狀態

@dataclass
class StateData:
    """狀態數據類"""
    state: DialogueState
    metadata: Dict[str, Any]
    updated_at: datetime

class StateTracker:
    """狀態追蹤器"""
    def __init__(self):
        self.current_state: Optional[StateData] = None
        self.state_history: List[StateData] = []
    
    async def set_state(
        self, 
        state: DialogueState, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """設置當前狀態"""
        state_data = StateData(
            state=state,
            metadata=metadata or {},
            updated_at=datetime.now()
        )
        
        if self.current_state:
            self.state_history.append(self.current_state)
        
        self.current_state = state_data
    
    async def get_current_state(self) -> Optional[StateData]:
        """獲取當前狀態"""
        return self.current_state
    
    async def get_state_history(self) -> List[StateData]:
        """獲取狀態歷史"""
        return self.state_history 