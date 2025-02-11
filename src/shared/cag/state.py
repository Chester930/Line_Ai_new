from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy

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
    metadata: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化後處理"""
        # 確保元數據是不可變的
        self.metadata = deepcopy(self.metadata)

class StateTracker:
    """狀態追蹤器"""
    def __init__(self):
        self._current_state: Optional[StateData] = None
        self._state_history: List[StateData] = []
    
    async def set_state(
        self,
        state: DialogueState,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """設置當前狀態"""
        # 創建新的狀態數據
        state_data = StateData(
            state=state,
            metadata=metadata or {},
            updated_at=datetime.now()
        )
        
        # 保存當前狀態到歷史
        if self._current_state:
            self._state_history.append(self._current_state)
        
        # 更新當前狀態
        self._current_state = state_data
    
    async def get_current_state(self) -> Optional[StateData]:
        """獲取當前狀態"""
        return deepcopy(self._current_state) if self._current_state else None
    
    async def get_state_history(self) -> List[StateData]:
        """獲取狀態歷史"""
        return deepcopy(self._state_history) 