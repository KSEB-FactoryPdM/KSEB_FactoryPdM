"""
장비 메타데이터 모델
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Equipment(Base):
    """장비 메타데이터 모델"""
    __tablename__ = "equipment"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # CAHU, PAHU, PAC, EF, SF, DEF, DSF 등 공조기 설비
    category = Column(String(50))  # production, utility, safety, etc.
    location = Column(String(100))  # 공장, 건물, 층, 구역
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100), unique=True)
    installation_date = Column(DateTime(timezone=True))
    warranty_expiry = Column(DateTime(timezone=True))
    last_maintenance = Column(DateTime(timezone=True))
    next_maintenance = Column(DateTime(timezone=True))
    status = Column(String(20), default="active")  # active, inactive, maintenance, retired
    description = Column(Text)
    specifications = Column(Text)  # JSON 형태의 상세 사양
    operating_hours = Column(Float, default=0.0)
    max_operating_hours = Column(Float)
    criticality = Column(String(20), default="medium")  # low, medium, high, critical
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계
    sensors = relationship("Sensor", back_populates="equipment")
    
    def __repr__(self):
        return f"<Equipment(id={self.id}, name={self.name}, type={self.type})>"


class Sensor(Base):
    """센서 메타데이터 모델"""
    __tablename__ = "sensors"
    
    id = Column(String(50), primary_key=True, index=True)
    equipment_id = Column(String(50), ForeignKey("equipment.id"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # vibration, temperature, pressure, current, etc.
    unit = Column(String(20))  # g, °C, Pa, A, etc.
    location = Column(String(100))  # 센서 설치 위치
    manufacturer = Column(String(100))
    model = Column(String(100))
    serial_number = Column(String(100))
    installation_date = Column(DateTime(timezone=True))
    calibration_date = Column(DateTime(timezone=True))
    next_calibration = Column(DateTime(timezone=True))
    status = Column(String(20), default="active")  # active, inactive, maintenance, retired
    sampling_rate = Column(Float)  # Hz
    range_min = Column(Float)
    range_max = Column(Float)
    accuracy = Column(Float)  # ±%
    description = Column(Text)
    specifications = Column(Text)  # JSON 형태의 상세 사양
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계
    equipment = relationship("Equipment", back_populates="sensors")
    
    def __repr__(self):
        return f"<Sensor(id={self.id}, name={self.name}, type={self.type})>"


class MaintenanceSchedule(Base):
    """정비 일정 모델"""
    __tablename__ = "maintenance_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(50), ForeignKey("equipment.id"), nullable=False)
    schedule_type = Column(String(50), nullable=False)  # preventive, predictive, corrective
    description = Column(Text)
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    estimated_duration = Column(Integer)  # 분 단위
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(20), default="scheduled")  # scheduled, in_progress, completed, cancelled
    assigned_to = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<MaintenanceSchedule(id={self.id}, equipment_id={self.equipment_id}, scheduled_date={self.scheduled_date})>"


class MaintenanceHistory(Base):
    """정비 이력 모델"""
    __tablename__ = "maintenance_history"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(50), ForeignKey("equipment.id"), nullable=False)
    maintenance_type = Column(String(50), nullable=False)  # preventive, predictive, corrective
    description = Column(Text)
    performed_date = Column(DateTime(timezone=True), nullable=False)
    duration = Column(Integer)  # 분 단위
    performed_by = Column(String(100))
    parts_replaced = Column(Text)  # JSON 형태
    cost = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<MaintenanceHistory(id={self.id}, equipment_id={self.equipment_id}, performed_date={self.performed_date})>" 