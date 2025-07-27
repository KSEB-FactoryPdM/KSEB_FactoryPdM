"""
센서 데이터 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SensorDataBase(BaseModel):
    """센서 데이터 기본 스키마"""
    device_id: str = Field(..., description="장비 ID")
    sensor_type: str = Field(..., description="센서 유형 (vibration, temperature, current)")
    value: float = Field(..., description="센서 값")
    unit: Optional[str] = Field(None, description="단위")


class SensorDataCreate(SensorDataBase):
    """센서 데이터 생성 스키마"""
    time: datetime = Field(..., description="측정 시간")


class SensorDataResponse(SensorDataBase):
    """센서 데이터 응답 스키마"""
    time: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class SensorDataListResponse(BaseModel):
    """센서 데이터 목록 응답 스키마"""
    data: List[SensorDataResponse]
    total: int
    device_id: str
    sensor_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class SensorDataQuery(BaseModel):
    """센서 데이터 조회 파라미터"""
    device_id: str = Field(..., description="장비 ID")
    sensor_type: Optional[str] = Field(None, description="센서 유형")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    limit: int = Field(default=1000, description="조회 개수 제한")
    offset: int = Field(default=0, description="오프셋")


class SensorDataBatch(BaseModel):
    """센서 데이터 배치 스키마"""
    device_id: str
    sensor_data: List[SensorDataCreate] 