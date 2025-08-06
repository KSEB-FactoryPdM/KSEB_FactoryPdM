"""
장비 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class DeviceBase(BaseModel):
    """장비 기본 스키마"""
    name: str = Field(..., description="장비명")
    type: Optional[str] = Field(None, description="장비 유형")
    location: Optional[str] = Field(None, description="설치 위치")
    installation_date: Optional[date] = Field(None, description="설치일")
    last_maintenance_date: Optional[date] = Field(None, description="마지막 정비일")
    status: str = Field(default="active", description="장비 상태")


class DeviceCreate(DeviceBase):
    """장비 생성 스키마"""
    id: str = Field(..., description="장비 ID")


class DeviceUpdate(BaseModel):
    """장비 업데이트 스키마"""
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    installation_date: Optional[date] = None
    last_maintenance_date: Optional[date] = None
    status: Optional[str] = None


class DeviceResponse(DeviceBase):
    """장비 응답 스키마"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """장비 목록 응답 스키마"""
    devices: List[DeviceResponse]
    total: int
    page: int
    size: int 