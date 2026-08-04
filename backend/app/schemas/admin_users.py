from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class AdminUserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    deactivated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class PaginatedAdminUsersResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class UserRoleUpdateRequest(BaseModel):
    role: Literal["admin", "user"]


class UserStatusUpdateRequest(BaseModel):
    is_active: bool
