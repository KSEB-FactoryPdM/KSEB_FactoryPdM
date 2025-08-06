"""
알림 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class NotificationBase(BaseModel):
    """알림 기본 스키마"""
    device_id: str = Field(..., description="장비 ID")
    sensor_id: str = Field(..., description="센서 ID")
    alert_type: str = Field(..., description="알림 유형 (warning, critical)")
    anomaly_type: str = Field(..., description="이상 유형 (vibration, temperature, current)")
    severity: str = Field(..., description="심각도 (low, medium, high, critical)")
    message: str = Field(..., description="알림 메시지")
    detected_at: datetime = Field(..., description="감지 시간")


class NotificationCreate(NotificationBase):
    """알림 생성 스키마"""
    pass


class NotificationUpdate(BaseModel):
    """알림 업데이트 스키마"""
    acknowledged: Optional[bool] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class NotificationResponse(NotificationBase):
    """알림 응답 스키마"""
    id: int
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationChannelBase(BaseModel):
    """알림 채널 기본 스키마"""
    name: str = Field(..., description="채널명 (email, sms, tts, kakao)")
    enabled: bool = Field(default=True, description="활성화 여부")
    config: Optional[Dict[str, Any]] = Field(None, description="채널 설정")


class NotificationChannelCreate(NotificationChannelBase):
    """알림 채널 생성 스키마"""
    pass


class NotificationChannelUpdate(BaseModel):
    """알림 채널 업데이트 스키마"""
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class NotificationChannelResponse(NotificationChannelBase):
    """알림 채널 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotificationLogBase(BaseModel):
    """알림 로그 기본 스키마"""
    notification_id: int = Field(..., description="알림 ID")
    channel_id: int = Field(..., description="채널 ID")
    status: str = Field(..., description="전송 상태 (sent, failed, pending)")
    error_message: Optional[str] = Field(None, description="오류 메시지")


class NotificationLogCreate(NotificationLogBase):
    """알림 로그 생성 스키마"""
    pass


class NotificationLogResponse(NotificationLogBase):
    """알림 로그 응답 스키마"""
    id: int
    sent_at: datetime
    
    class Config:
        from_attributes = True


class AlertRuleBase(BaseModel):
    """알림 규칙 기본 스키마"""
    name: str = Field(..., description="규칙명")
    device_id: str = Field(..., description="장비 ID")
    sensor_type: str = Field(..., description="센서 유형")
    condition: str = Field(..., description="조건 (gt, lt, eq, range)")
    threshold_value: str = Field(..., description="임계값")
    severity: str = Field(..., description="심각도 (low, medium, high, critical)")
    enabled: bool = Field(default=True, description="활성화 여부")


class AlertRuleCreate(AlertRuleBase):
    """알림 규칙 생성 스키마"""
    pass


class AlertRuleUpdate(BaseModel):
    """알림 규칙 업데이트 스키마"""
    name: Optional[str] = None
    condition: Optional[str] = None
    threshold_value: Optional[str] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    """알림 규칙 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AlertMessage(BaseModel):
    """알림 메시지 스키마"""
    device_id: str
    device_name: Optional[str] = None
    sensor_id: str
    sensor_name: Optional[str] = None
    alert_type: str
    anomaly_type: str
    severity: str
    message: str
    detected_at: datetime
    sensor_value: Optional[float] = None
    threshold_value: Optional[float] = None


class NotificationSummary(BaseModel):
    """알림 요약 스키마"""
    total_notifications: int
    unacknowledged_count: int
    critical_count: int
    warning_count: int
    recent_notifications: List[NotificationResponse] 