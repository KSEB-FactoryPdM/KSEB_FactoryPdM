"""
인증 API 엔드포인트
"""
from datetime import timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_user, get_current_active_user, require_admin_permission
)
from app.schemas.auth import (
    UserCreate, UserResponse, UserLogin, Token, UserUpdate,
    PasswordChange, PermissionCreate, PermissionResponse
)
from app.services.auth_service import auth_service
from app.models.user import User

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
def register_user(
    user_create: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """사용자 등록"""
    try:
        user = auth_service.create_user(db, user_create)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 등록 중 오류가 발생했습니다"
        )


@router.post("/login", response_model=Token)
def login_user(
    user_login: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """사용자 로그인"""
    try:
        access_token = auth_service.authenticate_user_and_create_token(
            db, user_login.username, user_login.password
        )
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 사용자명 또는 비밀번호입니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800  # 30분
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 중 오류가 발생했습니다"
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """현재 사용자 정보 조회"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """현재 사용자 정보 업데이트"""
    try:
        user = auth_service.update_user(db, current_user.id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 업데이트 중 오류가 발생했습니다"
        )


@router.post("/change-password")
def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """비밀번호 변경"""
    try:
        success = auth_service.change_password(
            db, current_user.id, 
            password_change.current_password, 
            password_change.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 올바르지 않습니다"
            )
        
        return {"message": "비밀번호가 성공적으로 변경되었습니다"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 변경 중 오류가 발생했습니다"
        )


@router.get("/users", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin_permission()),
    db: Session = Depends(get_db)
) -> Any:
    """사용자 목록 조회 (관리자만)"""
    try:
        users = auth_service.get_users(db, skip=skip, limit=limit)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin_permission()),
    db: Session = Depends(get_db)
) -> Any:
    """사용자 조회 (관리자만)"""
    try:
        user = auth_service.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 조회 중 오류가 발생했습니다"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin_permission()),
    db: Session = Depends(get_db)
) -> Any:
    """사용자 정보 업데이트 (관리자만)"""
    try:
        user = auth_service.update_user(db, user_id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 업데이트 중 오류가 발생했습니다"
        )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin_permission()),
    db: Session = Depends(get_db)
) -> Any:
    """사용자 삭제 (관리자만)"""
    try:
        success = auth_service.delete_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        return {"message": "사용자가 성공적으로 삭제되었습니다"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 삭제 중 오류가 발생했습니다"
        )


@router.get("/users/{user_id}/permissions", response_model=List[PermissionResponse])
def get_user_permissions(
    user_id: int,
    current_user: User = Depends(require_admin_permission()),
    db: Session = Depends(get_db)
) -> Any:
    """사용자 권한 조회 (관리자만)"""
    try:
        permissions = auth_service.get_user_permissions(db, user_id)
        return permissions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 권한 조회 중 오류가 발생했습니다"
        )


@router.post("/users/{user_id}/permissions", response_model=PermissionResponse)
def add_user_permission(
    user_id: int,
    permission_create: PermissionCreate,
    current_user: User = Depends(require_admin_permission()),
    db: Session = Depends(get_db)
) -> Any:
    """사용자 권한 추가 (관리자만)"""
    try:
        success = auth_service.add_user_permission(
            db, user_id, permission_create.resource, permission_create.action
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="권한 추가에 실패했습니다"
            )
        
        # 새로 생성된 권한 반환
        permissions = auth_service.get_user_permissions(db, user_id)
        for permission in permissions:
            if (permission.resource == permission_create.resource and 
                permission.action == permission_create.action):
                return permission
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="권한 생성 후 조회에 실패했습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 권한 추가 중 오류가 발생했습니다"
        )


@router.delete("/users/{user_id}/permissions")
def remove_user_permission(
    user_id: int,
    resource: str,
    action: str,
    current_user: User = Depends(require_admin_permission()),
    db: Session = Depends(get_db)
) -> Any:
    """사용자 권한 제거 (관리자만)"""
    try:
        success = auth_service.remove_user_permission(db, user_id, resource, action)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="권한 제거에 실패했습니다"
            )
        
        return {"message": "권한이 성공적으로 제거되었습니다"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 권한 제거 중 오류가 발생했습니다"
        ) 