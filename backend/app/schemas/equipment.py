"""
장비 메타데이터 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class EquipmentBase(BaseModel):
    """장비 기본 스키마"""
    id: str = Field(..., description="장비 ID")
    name: str = Field(..., description="장비명")
    type: str = Field(..., description="장비 유형 (CAHU, PAHU, PAC, EF, SF, DEF, DSF 등 공조기 설비)")
    category: Optional[str] = Field(None, description="카테고리 (production, utility, safety, etc.)")
    location: Optional[str] = Field(None, description="설치 위치")
    manufacturer: Optional[str] = Field(None, description="제조사")
    model: Optional[str] = Field(None, description="모델명")
    serial_number: Optional[str] = Field(None, description="시리얼 번호")
    installation_date: Optional[datetime] = Field(None, description="설치일")
    warranty_expiry: Optional[datetime] = Field(None, description="보증 만료일")
    last_maintenance: Optional[datetime] = Field(None, description="마지막 정비일")
    next_maintenance: Optional[datetime] = Field(None, description="다음 정비일")
    status: str = Field(default="active", description="상태 (active, inactive, maintenance, retired)")
    description: Optional[str] = Field(None, description="설명")
    specifications: Optional[Dict[str, Any]] = Field(None, description="상세 사양")
    operating_hours: float = Field(default=0.0, description="운전 시간")
    max_operating_hours: Optional[float] = Field(None, description="최대 운전 시간")
    criticality: str = Field(default="medium", description="중요도 (low, medium, high, critical)")


class EquipmentCreate(EquipmentBase):
    """장비 생성 스키마"""
    pass


class EquipmentUpdate(BaseModel):
    """장비 업데이트 스키마"""
    name: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    status: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    operating_hours: Optional[float] = None
    max_operating_hours: Optional[float] = None
    criticality: Optional[str] = None


class EquipmentResponse(EquipmentBase):
    """장비 응답 스키마"""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SensorBase(BaseModel):
    """센서 기본 스키마"""
    id: str = Field(..., description="센서 ID")
    equipment_id: str = Field(..., description="장비 ID")
    name: str = Field(..., description="센서명")
    type: str = Field(..., description="센서 유형 (current, vibration)")
    unit: Optional[str] = Field(None, description="단위 (A: 전류, mm/s: 진동)")
    location: Optional[str] = Field(None, description="설치 위치")
    manufacturer: Optional[str] = Field(None, description="제조사")
    model: Optional[str] = Field(None, description="모델명")
    serial_number: Optional[str] = Field(None, description="시리얼 번호")
    installation_date: Optional[datetime] = Field(None, description="설치일")
    calibration_date: Optional[datetime] = Field(None, description="교정일")
    next_calibration: Optional[datetime] = Field(None, description="다음 교정일")
    status: str = Field(default="active", description="상태 (active, inactive, maintenance, retired)")
    sampling_rate: Optional[float] = Field(None, description="샘플링 레이트 (Hz)")
    range_min: Optional[float] = Field(None, description="최소 범위")
    range_max: Optional[float] = Field(None, description="최대 범위")
    accuracy: Optional[float] = Field(None, description="정확도 (±%)")
    description: Optional[str] = Field(None, description="설명")
    specifications: Optional[Dict[str, Any]] = Field(None, description="상세 사양")


class SensorCreate(SensorBase):
    """센서 생성 스키마"""
    pass


class SensorUpdate(BaseModel):
    """센서 업데이트 스키마"""
    name: Optional[str] = None
    type: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    calibration_date: Optional[datetime] = None
    next_calibration: Optional[datetime] = None
    status: Optional[str] = None
    sampling_rate: Optional[float] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    accuracy: Optional[float] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None


class SensorResponse(SensorBase):
    """센서 응답 스키마"""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EquipmentWithSensors(EquipmentResponse):
    """센서가 포함된 장비 응답 스키마"""
    sensors: List[SensorResponse] = []


class MaintenanceScheduleBase(BaseModel):
    """정비 일정 기본 스키마"""
    equipment_id: str = Field(..., description="장비 ID")
    schedule_type: str = Field(..., description="정비 유형 (preventive, predictive, corrective)")
    description: Optional[str] = Field(None, description="설명")
    scheduled_date: datetime = Field(..., description="예정일")
    estimated_duration: Optional[int] = Field(None, description="예상 소요시간 (분)")
    priority: str = Field(default="medium", description="우선순위 (low, medium, high, critical)")
    status: str = Field(default="scheduled", description="상태 (scheduled, in_progress, completed, cancelled)")
    assigned_to: Optional[str] = Field(None, description="담당자")
    notes: Optional[str] = Field(None, description="비고")


class MaintenanceScheduleCreate(MaintenanceScheduleBase):
    """정비 일정 생성 스키마"""
    pass


class MaintenanceScheduleUpdate(BaseModel):
    """정비 일정 업데이트 스키마"""
    schedule_type: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceScheduleResponse(MaintenanceScheduleBase):
    """정비 일정 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MaintenanceHistoryBase(BaseModel):
    """정비 이력 기본 스키마"""
    equipment_id: str = Field(..., description="장비 ID")
    maintenance_type: str = Field(..., description="정비 유형 (preventive, predictive, corrective)")
    description: Optional[str] = Field(None, description="설명")
    performed_date: datetime = Field(..., description="수행일")
    duration: Optional[int] = Field(None, description="소요시간 (분)")
    performed_by: Optional[str] = Field(None, description="수행자")
    parts_replaced: Optional[Dict[str, Any]] = Field(None, description="교체 부품")
    cost: Optional[float] = Field(None, description="비용")
    notes: Optional[str] = Field(None, description="비고")


class MaintenanceHistoryCreate(MaintenanceHistoryBase):
    """정비 이력 생성 스키마"""
    pass


class MaintenanceHistoryResponse(MaintenanceHistoryBase):
    """정비 이력 응답 스키마"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class EquipmentSummary(BaseModel):
    """장비 요약 스키마"""
    total_equipment: int
    active_equipment: int
    maintenance_equipment: int
    critical_equipment: int
    equipment_by_type: Dict[str, int]
    equipment_by_location: Dict[str, int]


class SensorSummary(BaseModel):
    """센서 요약 스키마"""
    total_sensors: int
    active_sensors: int
    sensors_by_type: Dict[str, int]
    sensors_by_equipment: Dict[str, int] 