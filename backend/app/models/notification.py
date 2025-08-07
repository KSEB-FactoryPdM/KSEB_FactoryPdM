"""
알림 관련 모델
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Notification(Base):
    """알림 모델"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), nullable=False, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(20), nullable=False)  # warning, critical
    anomaly_type = Column(String(50), nullable=False)  # vibration, temperature, current
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    message = Column(Text, nullable=False)
    sensor_value = Column(String(50))  # 센서 값
    threshold_value = Column(String(50))  # 임계값
    detected_at = Column(DateTime(timezone=True), nullable=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(50))
    acknowledged_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Notification(device_id={self.device_id}, alert_type={self.alert_type})>"


class NotificationChannel(Base):
    """알림 채널 모델"""
    __tablename__ = "notification_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)  # email, sms, tts, kakao
    enabled = Column(Boolean, default=True)
    config = Column(Text)  # JSON 형태의 설정
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationChannel(name={self.name}, enabled={self.enabled})>"


class NotificationLog(Base):
    """알림 전송 로그 모델"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("notification_channels.id"), nullable=False)
    status = Column(String(20), nullable=False)  # sent, failed, pending
    error_message = Column(Text)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    notification = relationship("Notification")
    channel = relationship("NotificationChannel")
    
    def __repr__(self):
        return f"<NotificationLog(notification_id={self.notification_id}, status={self.status})>"


class AlertRule(Base):
    """알림 규칙 모델"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    device_id = Column(String(50), nullable=False)
    sensor_type = Column(String(50), nullable=False)
    condition = Column(String(20), nullable=False)  # gt, lt, eq, range
    threshold_value = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AlertRule(name={self.name}, device_id={self.device_id})>" 