"""
이상 탐지 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AnomalyEventBase(BaseModel):
    """이상 이벤트 기본 스키마"""
    device_id: str = Field(..., description="장비 ID")
    event_time: datetime = Field(..., description="이상 발생 시간")
    anomaly_score: float = Field(..., description="이상 점수 (0-1)")
    anomaly_type: Optional[str] = Field(None, description="이상 유형")
    severity: str = Field(..., description="심각도 (low, medium, high, critical)")
    description: Optional[str] = Field(None, description="이상 설명")


class AnomalyEventCreate(AnomalyEventBase):
    """이상 이벤트 생성 스키마"""
    pass


class AnomalyEventResponse(AnomalyEventBase):
    """이상 이벤트 응답 스키마"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnomalyEventListResponse(BaseModel):
    """이상 이벤트 목록 응답 스키마"""
    events: List[AnomalyEventResponse]
    total: int
    page: int
    size: int


class AnomalyDetectionRequest(BaseModel):
    """이상 탐지 요청 스키마"""
    device_id: str = Field(..., description="장비 ID")
    sensor_data: List[dict] = Field(..., description="센서 데이터 리스트")
    timestamp: datetime = Field(..., description="탐지 요청 시간")


class AnomalyDetectionResponse(BaseModel):
    """이상 탐지 응답 스키마"""
    device_id: str
    is_anomaly: bool = Field(..., description="이상 여부")
    anomaly_score: float = Field(..., description="이상 점수")
    anomaly_type: Optional[str] = Field(None, description="이상 유형")
    severity: Optional[str] = Field(None, description="심각도")
    confidence: float = Field(..., description="신뢰도")
    detected_at: datetime = Field(..., description="탐지 시간")
    processing_time: float = Field(..., description="처리 시간 (초)")


class AnomalyQuery(BaseModel):
    """이상 이벤트 조회 파라미터"""
    device_id: Optional[str] = Field(None, description="장비 ID")
    severity: Optional[str] = Field(None, description="심각도")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    page: int = Field(default=1, description="페이지 번호")
    size: int = Field(default=50, description="페이지 크기")


class ModelTrainingRequest(BaseModel):
    """모델 훈련 요청 스키마"""
    device_id: str = Field(..., description="장비 ID")
    model_type: str = Field(default="xgboost", description="모델 유형")
    normal_current_files: List[str] = Field(..., description="정상 전류 데이터 파일 경로")
    normal_vibration_files: List[str] = Field(..., description="정상 진동 데이터 파일 경로")
    abnormal_current_files: List[str] = Field(..., description="이상 전류 데이터 파일 경로")
    abnormal_vibration_files: List[str] = Field(..., description="이상 진동 데이터 파일 경로")
    
    model_config = {
        "protected_namespaces": ()
    }


class ModelTrainingResponse(BaseModel):
    """모델 훈련 응답 스키마"""
    device_id: str = Field(..., description="장비 ID")
    model_type: str = Field(..., description="모델 유형")
    status: str = Field(..., description="훈련 상태")
    accuracy: float = Field(..., description="정확도")
    precision: float = Field(..., description="정밀도")
    recall: float = Field(..., description="재현율")
    f1_score: float = Field(..., description="F1 점수")
    training_time: float = Field(..., description="훈련 시간 (초)")
    message: str = Field(..., description="응답 메시지")
    
    model_config = {
        "protected_namespaces": ()
    }


class ModelPerformanceResponse(BaseModel):
    """모델 성능 응답 스키마"""
    device_id: str = Field(..., description="장비 ID")
    model_type: str = Field(..., description="모델 유형")
    accuracy: float = Field(..., description="정확도")
    precision: float = Field(..., description="정밀도")
    recall: float = Field(..., description="재현율")
    f1_score: float = Field(..., description="F1 점수")
    last_training: datetime = Field(..., description="마지막 훈련 시간")
    total_predictions: int = Field(..., description="총 예측 수")
    anomaly_detections: int = Field(..., description="이상 탐지 수")
    message: str = Field(..., description="응답 메시지") 
    
    model_config = {
        "protected_namespaces": ()
    }