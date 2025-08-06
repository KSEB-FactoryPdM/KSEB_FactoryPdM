"""
인증 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str = Field(..., description="사용자명")
    email: EmailStr = Field(..., description="이메일")
    full_name: Optional[str] = Field(None, description="전체 이름")
    role: str = Field(default="viewer", description="역할 (admin, operator, viewer)")


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., description="비밀번호")


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """로그인 스키마"""
    username: str = Field(..., description="사용자명")
    password: str = Field(..., description="비밀번호")


class Token(BaseModel):
    """토큰 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간 (초)")


class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


class PermissionBase(BaseModel):
    """권한 기본 스키마"""
    resource: str = Field(..., description="리소스 (devices, sensors, anomalies, rul, models)")
    action: str = Field(..., description="액션 (read, write, delete, admin)")


class PermissionCreate(PermissionBase):
    """권한 생성 스키마"""
    user_id: int = Field(..., description="사용자 ID")


class PermissionResponse(PermissionBase):
    """권한 응답 스키마"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """역할 기본 스키마"""
    name: str = Field(..., description="역할명")
    description: Optional[str] = Field(None, description="설명")


class RoleCreate(RoleBase):
    """역할 생성 스키마"""
    permissions: List[PermissionBase] = Field(default=[], description="권한 목록")


class RoleResponse(RoleBase):
    """역할 응답 스키마"""
    id: int
    created_at: datetime
    permissions: List[PermissionResponse] = []
    
    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """비밀번호 변경 스키마"""
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., description="새 비밀번호")


class PasswordReset(BaseModel):
    """비밀번호 재설정 스키마"""
    email: EmailStr = Field(..., description="이메일")


class PasswordResetConfirm(BaseModel):
    """비밀번호 재설정 확인 스키마"""
    token: str = Field(..., description="재설정 토큰")
    new_password: str = Field(..., description="새 비밀번호") 