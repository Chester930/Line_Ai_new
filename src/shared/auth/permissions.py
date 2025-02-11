from typing import List
from fastapi import HTTPException, Depends
from src.shared.auth.user import get_current_user

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(self, user: User = Depends(get_current_user)):
        if not any(role in self.allowed_roles for role in user.roles):
            raise HTTPException(
                status_code=403,
                detail="Operation not permitted"
            )

admin_only = RoleChecker(["admin"])
moderator_only = RoleChecker(["moderator", "admin"])