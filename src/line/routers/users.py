from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
from src.line.models.user import User, RoleAssignRequest
from src.line.utils.auth import get_current_admin
from src.shared.utils.pagination import PaginatedResponse, Paginator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.line.models.batch_operation import BatchOperation

router = APIRouter()

@router.post("/{user_id}/role", tags=["users"])
async def assign_user_role(
    user_id: int, 
    role: RoleAssignRequest,
    current_user: User = Depends(get_current_admin)
):
    """
    分配使用者角色
    - 需要管理員權限
    - 可分配多個角色
    """
    # 添加角色分配邏輯... 

@router.get("/users", response_model=PaginatedResponse[User])
async def list_users(
    page: int = 1,
    per_page: int = 20,
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(User)
    if role:
        query = query.where(User.roles.any(role))
    paginator = Paginator(query, page, per_page)
    return await paginator.paginate()

@router.post("/users/batch", tags=["users"])
async def batch_operation(
    operation: BatchOperation,
    current_user: User = Depends(get_current_admin)
):
    """批量操作接口"""
    # 實現批量刪除/更新邏輯 