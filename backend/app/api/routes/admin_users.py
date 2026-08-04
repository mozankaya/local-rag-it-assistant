from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.routes.users import require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.admin_users import (
    AdminUserResponse,
    PaginatedAdminUsersResponse,
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
)


router = APIRouter(
    prefix="/admin/users",
    tags=["Admin Users"],
)


def to_admin_user_response(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def count_active_admins(db: Session) -> int:
    """Sistemde giriş yapabilecek aktif admin sayısını döndürür."""

    return (
        db.query(User)
        .filter(
            User.role == "admin",
            User.is_active.is_(True),
        )
        .count()
    )


@router.get("", response_model=PaginatedAdminUsersResponse)
def list_users(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    query = db.query(User)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.email.ilike(search_pattern),
                User.full_name.ilike(search_pattern),
            )
        )

    total = query.count()

    users = (
        query.order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [to_admin_user_response(user) for user in users]

    return PaginatedAdminUsersResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


@router.patch("/{user_id}/role", response_model=AdminUserResponse)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdateRequest,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı.",
        )

    removes_active_admin_role = (
        user.role == "admin" and user.is_active and payload.role != "admin"
    )

    if removes_active_admin_role:
        active_admin_count = count_active_admins(db)

        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Sistemde en az bir aktif admin " "kullanıcı bulunmalıdır."),
            )

    user.role = payload.role
    db.commit()
    db.refresh(user)

    return to_admin_user_response(user)


@router.patch("/{user_id}/status", response_model=AdminUserResponse)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı.",
        )

    if user.id == current_admin.id and payload.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin kendi hesabını pasif hale getiremez.",
        )

    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)

    return to_admin_user_response(user)
