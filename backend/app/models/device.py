"""
장비 정보 데이터베이스 모델
"""
from sqlalchemy import Column, String, Date, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Device(Base):
    """장비 정보 모델"""
    __tablename__ = "devices"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50))
    location = Column(String(100))
    installation_date = Column(Date)
    last_maintenance_date = Column(Date)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, type={self.type})>" 