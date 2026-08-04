from datetime import datetime, timedelta, timezone
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

INACTIVE_USER_RETENTION_DAYS = 30

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin Users"],
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_admin_user_response(user: User) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        deactivated_at=user.deactivated_at,
        created_at=user.created_at,
    )


def count_active_admins(db: Session) -> int:
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

    if user.id == current_admin.id and payload.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin kendi hesabını pasif hale getiremez.",
        )

    deactivates_active_admin = (
        user.role == "admin" and user.is_active and payload.is_active is False
    )

    if deactivates_active_admin:
        active_admin_count = count_active_admins(db)

        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sistemde en az bir aktif admin kullanıcı bulunmalıdır.",
            )

    if payload.is_active:
        user.is_active = True
        user.deactivated_at = None
    else:
        if user.is_active or user.deactivated_at is None:
            user.deactivated_at = utc_now()

        user.is_active = False

    db.commit()
    db.refresh(user)

    return to_admin_user_response(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def permanently_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> None:
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı.",
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin kendi hesabını kalıcı olarak silemez.",
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Aktif kullanıcı kalıcı olarak silinemez. "
                "Önce kullanıcıyı pasif hale getirin."
            ),
        )

    if user.deactivated_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kullanıcının pasifleştirilme tarihi bulunamadı.",
        )

    delete_available_at = user.deactivated_at + timedelta(
        days=INACTIVE_USER_RETENTION_DAYS,
    )

    if utc_now() < delete_available_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Bu kullanıcı için 30 günlük bekleme " "süresi henüz dolmadı."),
        )

    db.delete(user)
    db.commit()
