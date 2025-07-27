"""
알림 시스템 테스트
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.notification_service import notification_service
from app.services.equipment_service import equipment_service
from app.schemas.notification import NotificationCreate, AlertRuleCreate
from app.schemas.equipment import EquipmentCreate, SensorCreate


class TestNotificationService:
    """알림 서비스 테스트"""
    
    def test_create_notification(self, db: Session):
        """알림 생성 테스트"""
        # 테스트 알림 생성
        notification = notification_service.create_notification(
            db=db,
            device_id="test_device_001",
            sensor_id="test_sensor_001",
            alert_type="warning",
            anomaly_type="vibration_anomaly",
            severity="medium",
            message="테스트 알림 메시지",
            sensor_value=15.5,
            threshold_value=10.0
        )
        
        assert notification is not None
        assert notification.device_id == "test_device_001"
        assert notification.sensor_id == "test_sensor_001"
        assert notification.alert_type == "warning"
        assert notification.anomaly_type == "vibration_anomaly"
        assert notification.severity == "medium"
        assert notification.message == "테스트 알림 메시지"
        assert notification.acknowledged == False
    
    def test_get_notifications(self, db: Session):
        """알림 목록 조회 테스트"""
        # 테스트 알림 생성
        notification_service.create_notification(
            db=db,
            device_id="test_device_001",
            sensor_id="test_sensor_001",
            alert_type="warning",
            anomaly_type="vibration_anomaly",
            severity="medium",
            message="테스트 알림 메시지"
        )
        
        # 알림 목록 조회
        notifications = notification_service.get_notifications(
            db=db,
            device_id="test_device_001"
        )
        
        assert len(notifications) > 0
        assert notifications[0].device_id == "test_device_001"
    
    def test_acknowledge_notification(self, db: Session):
        """알림 확인 처리 테스트"""
        # 테스트 알림 생성
        notification = notification_service.create_notification(
            db=db,
            device_id="test_device_001",
            sensor_id="test_sensor_001",
            alert_type="warning",
            anomaly_type="vibration_anomaly",
            severity="medium",
            message="테스트 알림 메시지"
        )
        
        # 알림 확인 처리
        updated_notification = notification_service.acknowledge_notification(
            db=db,
            notification_id=notification.id,
            acknowledged_by="test_user"
        )
        
        assert updated_notification is not None
        assert updated_notification.acknowledged == True
        assert updated_notification.acknowledged_by == "test_user"
    
    def test_create_alert_rule(self, db: Session):
        """알림 규칙 생성 테스트"""
        alert_rule_create = AlertRuleCreate(
            name="진동 임계값 알림",
            device_id="test_device_001",
            sensor_type="vibration",
            condition="gt",
            threshold_value="10.0",
            severity="medium"
        )
        
        alert_rule = notification_service.create_alert_rule(
            db=db,
            alert_rule_create=alert_rule_create
        )
        
        assert alert_rule is not None
        assert alert_rule.name == "진동 임계값 알림"
        assert alert_rule.device_id == "test_device_001"
        assert alert_rule.sensor_type == "vibration"
        assert alert_rule.condition == "gt"
        assert alert_rule.threshold_value == "10.0"
    
    def test_check_alert_conditions(self, db: Session):
        """알림 조건 확인 테스트"""
        # 알림 규칙 생성
        alert_rule_create = AlertRuleCreate(
            name="진동 임계값 알림",
            device_id="test_device_001",
            sensor_type="vibration",
            condition="gt",
            threshold_value="10.0",
            severity="medium"
        )
        
        notification_service.create_alert_rule(db=db, alert_rule_create=alert_rule_create)
        
        # 조건 확인 (임계값 초과)
        triggered_rules = notification_service.check_alert_conditions(
            db=db,
            device_id="test_device_001",
            sensor_type="vibration",
            sensor_value=15.0
        )
        
        assert len(triggered_rules) > 0
        assert triggered_rules[0].name == "진동 임계값 알림"
        
        # 조건 확인 (임계값 미만)
        triggered_rules = notification_service.check_alert_conditions(
            db=db,
            device_id="test_device_001",
            sensor_type="vibration",
            sensor_value=5.0
        )
        
        assert len(triggered_rules) == 0
    
    def test_get_notification_summary(self, db: Session):
        """알림 요약 조회 테스트"""
        # 테스트 알림 생성
        notification_service.create_notification(
            db=db,
            device_id="test_device_001",
            sensor_id="test_sensor_001",
            alert_type="critical",
            anomaly_type="vibration_anomaly",
            severity="critical",
            message="테스트 알림 메시지"
        )
        
        # 요약 조회
        summary = notification_service.get_notification_summary(db)
        
        assert summary is not None
        assert "total_notifications" in summary
        assert "critical_count" in summary
        assert "warning_count" in summary


class TestEquipmentService:
    """장비 서비스 테스트"""
    
    def test_create_equipment(self, db: Session):
        """장비 생성 테스트"""
        equipment_create = EquipmentCreate(
            id="test_equipment_001",
            name="테스트 모터",
            type="motor",
            category="production",
            location="공장 A",
            manufacturer="테스트 제조사",
            model="TM-001",
            criticality="medium"
        )
        
        equipment = equipment_service.create_equipment(
            db=db,
            equipment_create=equipment_create
        )
        
        assert equipment is not None
        assert equipment.id == "test_equipment_001"
        assert equipment.name == "테스트 모터"
        assert equipment.type == "motor"
        assert equipment.category == "production"
    
    def test_create_sensor(self, db: Session):
        """센서 생성 테스트"""
        # 먼저 장비 생성
        equipment_create = EquipmentCreate(
            id="test_equipment_001",
            name="테스트 모터",
            type="motor",
            category="production"
        )
        equipment_service.create_equipment(db=db, equipment_create=equipment_create)
        
        # 센서 생성
        sensor_create = SensorCreate(
            id="test_sensor_001",
            equipment_id="test_equipment_001",
            name="진동 센서",
            type="vibration",
            unit="g",
            location="모터 베어링",
            manufacturer="센서 제조사",
            model="VS-001"
        )
        
        sensor = equipment_service.create_sensor(
            db=db,
            sensor_create=sensor_create
        )
        
        assert sensor is not None
        assert sensor.id == "test_sensor_001"
        assert sensor.equipment_id == "test_equipment_001"
        assert sensor.name == "진동 센서"
        assert sensor.type == "vibration"
    
    def test_get_equipment_with_sensors(self, db: Session):
        """센서가 포함된 장비 조회 테스트"""
        # 장비 생성
        equipment_create = EquipmentCreate(
            id="test_equipment_001",
            name="테스트 모터",
            type="motor",
            category="production"
        )
        equipment_service.create_equipment(db=db, equipment_create=equipment_create)
        
        # 센서 생성
        sensor_create = SensorCreate(
            id="test_sensor_001",
            equipment_id="test_equipment_001",
            name="진동 센서",
            type="vibration"
        )
        equipment_service.create_sensor(db=db, sensor_create=sensor_create)
        
        # 센서가 포함된 장비 조회
        equipment = equipment_service.get_equipment_with_sensors(
            db=db,
            equipment_id="test_equipment_001"
        )
        
        assert equipment is not None
        assert equipment.id == "test_equipment_001"
        assert len(equipment.sensors) > 0
        assert equipment.sensors[0].id == "test_sensor_001"
    
    def test_get_equipment_summary(self, db: Session):
        """장비 요약 조회 테스트"""
        # 테스트 장비 생성
        equipment_create = EquipmentCreate(
            id="test_equipment_001",
            name="테스트 모터",
            type="motor",
            category="production",
            status="active"
        )
        equipment_service.create_equipment(db=db, equipment_create=equipment_create)
        
        # 요약 조회
        summary = equipment_service.get_equipment_summary(db)
        
        assert summary is not None
        assert "total_equipment" in summary
        assert "active_equipment" in summary
        assert "equipment_by_type" in summary
    
    def test_get_sensor_summary(self, db: Session):
        """센서 요약 조회 테스트"""
        # 테스트 장비 및 센서 생성
        equipment_create = EquipmentCreate(
            id="test_equipment_001",
            name="테스트 모터",
            type="motor"
        )
        equipment_service.create_equipment(db=db, equipment_create=equipment_create)
        
        sensor_create = SensorCreate(
            id="test_sensor_001",
            equipment_id="test_equipment_001",
            name="진동 센서",
            type="vibration",
            status="active"
        )
        equipment_service.create_sensor(db=db, sensor_create=sensor_create)
        
        # 요약 조회
        summary = equipment_service.get_sensor_summary(db)
        
        assert summary is not None
        assert "total_sensors" in summary
        assert "active_sensors" in summary
        assert "sensors_by_type" in summary


class TestNotificationIntegration:
    """알림 시스템 통합 테스트"""
    
    def test_anomaly_detection_with_notification(self, db: Session):
        """이상 탐지와 알림 통합 테스트"""
        # 장비 및 센서 생성
        equipment_create = EquipmentCreate(
            id="test_device_001",
            name="테스트 모터",
            type="motor"
        )
        equipment_service.create_equipment(db=db, equipment_create=equipment_create)
        
        sensor_create = SensorCreate(
            id="test_sensor_001",
            equipment_id="test_device_001",
            name="진동 센서",
            type="vibration"
        )
        equipment_service.create_sensor(db=db, sensor_create=sensor_create)
        
        # 알림 규칙 생성
        alert_rule_create = AlertRuleCreate(
            name="진동 임계값 알림",
            device_id="test_device_001",
            sensor_type="vibration",
            condition="gt",
            threshold_value="10.0",
            severity="medium"
        )
        notification_service.create_alert_rule(db=db, alert_rule_create=alert_rule_create)
        
        # 이상 탐지 시뮬레이션 (임계값 초과)
        triggered_rules = notification_service.check_alert_conditions(
            db=db,
            device_id="test_device_001",
            sensor_type="vibration",
            sensor_value=15.0
        )
        
        assert len(triggered_rules) > 0
        
        # 알림 생성
        notification = notification_service.create_notification(
            db=db,
            device_id="test_device_001",
            sensor_id="test_sensor_001",
            alert_type="warning",
            anomaly_type="vibration_anomaly",
            severity="medium",
            message="진동 센서에서 이상이 탐지되었습니다",
            sensor_value=15.0,
            threshold_value=10.0
        )
        
        assert notification is not None
        assert notification.device_id == "test_device_001"
        assert notification.sensor_id == "test_sensor_001"
        assert notification.alert_type == "warning" 