"""
RUL 예측 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RULPredictionBase(BaseModel):
    """RUL 예측 기본 스키마"""
    device_id: str = Field(..., description="장비 ID")
    prediction_time: datetime = Field(..., description="예측 시간")
    rul_value: float = Field(..., description="잔여수명 값 (시간)")
    confidence: float = Field(..., description="예측 신뢰도 (0-1)")
    uncertainty: Optional[float] = Field(None, description="예측 불확실성")


class RULPredictionCreate(RULPredictionBase):
    """RUL 예측 생성 스키마"""
    pass


class RULPredictionResponse(RULPredictionBase):
    """RUL 예측 응답 스키마"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RULPredictionListResponse(BaseModel):
    """RUL 예측 목록 응답 스키마"""
    predictions: List[RULPredictionResponse]
    total: int
    page: int
    size: int


class RULPredictionRequest(BaseModel):
    """RUL 예측 요청 스키마"""
    device_id: str = Field(..., description="장비 ID")
    sensor_data: List[dict] = Field(..., description="센서 데이터 리스트")
    timestamp: datetime = Field(..., description="예측 요청 시간")


class RULPredictionResult(BaseModel):
    """RUL 예측 결과 스키마"""
    device_id: str
    rul_value: float = Field(..., description="잔여수명 (시간)")
    confidence: float = Field(..., description="신뢰도")
    uncertainty: Optional[float] = Field(None, description="불확실성")
    predicted_at: datetime = Field(..., description="예측 시간")
    processing_time: float = Field(..., description="처리 시간 (초)")
    health_status: str = Field(..., description="건강 상태 (good, warning, critical)")


class RULQuery(BaseModel):
    """RUL 예측 조회 파라미터"""
    device_id: Optional[str] = Field(None, description="장비 ID")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    page: int = Field(default=1, description="페이지 번호")
    size: int = Field(default=50, description="페이지 크기")


class DeviceHealthStatus(BaseModel):
    """장비 건강 상태 스키마"""
    device_id: str
    current_rul: float = Field(..., description="현재 잔여수명")
    health_percentage: float = Field(..., description="건강도 퍼센트")
    status: str = Field(..., description="상태 (good, warning, critical)")
    last_maintenance_recommendation: Optional[datetime] = Field(None, description="정비 권장일")
    confidence: float = Field(..., description="예측 신뢰도")
    updated_at: datetime = Field(..., description="업데이트 시간") 