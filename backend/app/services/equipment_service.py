"""
장비 메타데이터 관리 서비스
"""
import logging
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.equipment import Equipment, Sensor, MaintenanceSchedule, MaintenanceHistory
from app.schemas.equipment import (
    EquipmentCreate, EquipmentUpdate, SensorCreate, SensorUpdate,
    MaintenanceScheduleCreate, MaintenanceHistoryCreate
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class EquipmentService:
    """장비 메타데이터 관리 서비스"""
    
    def create_equipment(
        self, 
        db: Session, 
        equipment_create: EquipmentCreate
    ) -> Equipment:
        """장비 생성"""
        try:
            equipment_data = equipment_create.dict()
            
            # specifications을 JSON 문자열로 변환
            if equipment_data.get("specifications"):
                equipment_data["specifications"] = json.dumps(equipment_data["specifications"])
            
            equipment = Equipment(**equipment_data)
            
            db.add(equipment)
            db.commit()
            db.refresh(equipment)
            
            logger.info(f"장비 생성 완료: {equipment.id}")
            return equipment
            
        except Exception as e:
            db.rollback()
            logger.error(f"장비 생성 실패: {e}")
            raise
    
    def get_equipment(
        self, 
        db: Session, 
        equipment_id: str
    ) -> Optional[Equipment]:
        """장비 조회"""
        try:
            equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
            
            if equipment and equipment.specifications:
                try:
                    equipment.specifications = json.loads(equipment.specifications)
                except:
                    pass
            
            return equipment
            
        except Exception as e:
            logger.error(f"장비 조회 실패: {e}")
            return None
    
    def get_equipments(
        self, 
        db: Session,
        type: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Equipment]:
        """장비 목록 조회"""
        try:
            query = db.query(Equipment)
            
            if type:
                query = query.filter(Equipment.type == type)
            
            if category:
                query = query.filter(Equipment.category == category)
            
            if status:
                query = query.filter(Equipment.status == status)
            
            if location:
                query = query.filter(Equipment.location == location)
            
            equipments = query.offset(skip).limit(limit).all()
            
            # specifications JSON 파싱
            for equipment in equipments:
                if equipment.specifications:
                    try:
                        equipment.specifications = json.loads(equipment.specifications)
                    except:
                        pass
            
            return equipments
            
        except Exception as e:
            logger.error(f"장비 목록 조회 실패: {e}")
            return []
    
    def update_equipment(
        self, 
        db: Session, 
        equipment_id: str,
        equipment_update: EquipmentUpdate
    ) -> Optional[Equipment]:
        """장비 업데이트"""
        try:
            equipment = self.get_equipment(db, equipment_id)
            
            if not equipment:
                return None
            
            update_data = equipment_update.model_dump(exclude_unset=True)
            
            # specifications을 JSON 문자열로 변환
            if update_data.get("specifications"):
                update_data["specifications"] = json.dumps(update_data["specifications"])
            
            for field, value in update_data.items():
                setattr(equipment, field, value)
            
            db.commit()
            db.refresh(equipment)
            
            logger.info(f"장비 업데이트 완료: {equipment_id}")
            return equipment
            
        except Exception as e:
            db.rollback()
            logger.error(f"장비 업데이트 실패: {e}")
            return None
    
    def delete_equipment(
        self, 
        db: Session, 
        equipment_id: str
    ) -> bool:
        """장비 삭제"""
        try:
            equipment = self.get_equipment(db, equipment_id)
            
            if not equipment:
                return False
            
            db.delete(equipment)
            db.commit()
            
            logger.info(f"장비 삭제 완료: {equipment_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"장비 삭제 실패: {e}")
            return False
    
    def create_sensor(
        self, 
        db: Session, 
        sensor_create: SensorCreate
    ) -> Sensor:
        """센서 생성"""
        try:
            sensor_data = sensor_create.dict()
            
            # specifications을 JSON 문자열로 변환
            if sensor_data.get("specifications"):
                sensor_data["specifications"] = json.dumps(sensor_data["specifications"])
            
            sensor = Sensor(**sensor_data)
            
            db.add(sensor)
            db.commit()
            db.refresh(sensor)
            
            logger.info(f"센서 생성 완료: {sensor.id}")
            return sensor
            
        except Exception as e:
            db.rollback()
            logger.error(f"센서 생성 실패: {e}")
            raise
    
    def get_sensor(
        self, 
        db: Session, 
        sensor_id: str
    ) -> Optional[Sensor]:
        """센서 조회"""
        try:
            sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
            
            if sensor and sensor.specifications:
                try:
                    sensor.specifications = json.loads(sensor.specifications)
                except:
                    pass
            
            return sensor
            
        except Exception as e:
            logger.error(f"센서 조회 실패: {e}")
            return None
    
    def get_sensors(
        self, 
        db: Session,
        equipment_id: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Sensor]:
        """센서 목록 조회"""
        try:
            query = db.query(Sensor)
            
            if equipment_id:
                query = query.filter(Sensor.equipment_id == equipment_id)
            
            if type:
                query = query.filter(Sensor.type == type)
            
            if status:
                query = query.filter(Sensor.status == status)
            
            sensors = query.offset(skip).limit(limit).all()
            
            # specifications JSON 파싱
            for sensor in sensors:
                if sensor.specifications:
                    try:
                        sensor.specifications = json.loads(sensor.specifications)
                    except:
                        pass
            
            return sensors
            
        except Exception as e:
            logger.error(f"센서 목록 조회 실패: {e}")
            return []
    
    def update_sensor(
        self, 
        db: Session, 
        sensor_id: str,
        sensor_update: SensorUpdate
    ) -> Optional[Sensor]:
        """센서 업데이트"""
        try:
            sensor = self.get_sensor(db, sensor_id)
            
            if not sensor:
                return None
            
            update_data = sensor_update.dict(exclude_unset=True)
            
            # specifications을 JSON 문자열로 변환
            if update_data.get("specifications"):
                update_data["specifications"] = json.dumps(update_data["specifications"])
            
            for field, value in update_data.items():
                setattr(sensor, field, value)
            
            db.commit()
            db.refresh(sensor)
            
            logger.info(f"센서 업데이트 완료: {sensor_id}")
            return sensor
            
        except Exception as e:
            db.rollback()
            logger.error(f"센서 업데이트 실패: {e}")
            return None
    
    def delete_sensor(
        self, 
        db: Session, 
        sensor_id: str
    ) -> bool:
        """센서 삭제"""
        try:
            sensor = self.get_sensor(db, sensor_id)
            
            if not sensor:
                return False
            
            db.delete(sensor)
            db.commit()
            
            logger.info(f"센서 삭제 완료: {sensor_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"센서 삭제 실패: {e}")
            return False
    
    def get_equipment_with_sensors(
        self, 
        db: Session, 
        equipment_id: str
    ) -> Optional[Equipment]:
        """센서가 포함된 장비 조회"""
        try:
            equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
            
            if not equipment:
                return None
            
            # specifications JSON 파싱
            if equipment.specifications:
                try:
                    equipment.specifications = json.loads(equipment.specifications)
                except:
                    pass
            
            # 센서 정보도 JSON 파싱
            for sensor in equipment.sensors:
                if sensor.specifications:
                    try:
                        sensor.specifications = json.loads(sensor.specifications)
                    except:
                        pass
            
            return equipment
            
        except Exception as e:
            logger.error(f"장비 및 센서 조회 실패: {e}")
            return None
    
    def create_maintenance_schedule(
        self, 
        db: Session, 
        schedule_create: MaintenanceScheduleCreate
    ) -> MaintenanceSchedule:
        """정비 일정 생성"""
        try:
            schedule = MaintenanceSchedule(**schedule_create.dict())
            
            db.add(schedule)
            db.commit()
            db.refresh(schedule)
            
            logger.info(f"정비 일정 생성 완료: {schedule.id}")
            return schedule
            
        except Exception as e:
            db.rollback()
            logger.error(f"정비 일정 생성 실패: {e}")
            raise
    
    def get_maintenance_schedules(
        self, 
        db: Session,
        equipment_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MaintenanceSchedule]:
        """정비 일정 목록 조회"""
        try:
            query = db.query(MaintenanceSchedule)
            
            if equipment_id:
                query = query.filter(MaintenanceSchedule.equipment_id == equipment_id)
            
            if status:
                query = query.filter(MaintenanceSchedule.status == status)
            
            return query.order_by(MaintenanceSchedule.scheduled_date).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"정비 일정 목록 조회 실패: {e}")
            return []
    
    def create_maintenance_history(
        self, 
        db: Session, 
        history_create: MaintenanceHistoryCreate
    ) -> MaintenanceHistory:
        """정비 이력 생성"""
        try:
            history_data = history_create.dict()
            
            # parts_replaced을 JSON 문자열로 변환
            if history_data.get("parts_replaced"):
                history_data["parts_replaced"] = json.dumps(history_data["parts_replaced"])
            
            history = MaintenanceHistory(**history_data)
            
            db.add(history)
            db.commit()
            db.refresh(history)
            
            logger.info(f"정비 이력 생성 완료: {history.id}")
            return history
            
        except Exception as e:
            db.rollback()
            logger.error(f"정비 이력 생성 실패: {e}")
            raise
    
    def get_maintenance_history(
        self, 
        db: Session,
        equipment_id: Optional[str] = None,
        maintenance_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MaintenanceHistory]:
        """정비 이력 목록 조회"""
        try:
            query = db.query(MaintenanceHistory)
            
            if equipment_id:
                query = query.filter(MaintenanceHistory.equipment_id == equipment_id)
            
            if maintenance_type:
                query = query.filter(MaintenanceHistory.maintenance_type == maintenance_type)
            
            histories = query.order_by(MaintenanceHistory.performed_date.desc()).offset(skip).limit(limit).all()
            
            # parts_replaced JSON 파싱
            for history in histories:
                if history.parts_replaced:
                    try:
                        history.parts_replaced = json.loads(history.parts_replaced)
                    except:
                        pass
            
            return histories
            
        except Exception as e:
            logger.error(f"정비 이력 목록 조회 실패: {e}")
            return []
    
    def get_equipment_summary(self, db: Session) -> Dict[str, Any]:
        """장비 요약 정보 조회"""
        try:
            total = db.query(Equipment).count()
            active = db.query(Equipment).filter(Equipment.status == "active").count()
            maintenance = db.query(Equipment).filter(Equipment.status == "maintenance").count()
            critical = db.query(Equipment).filter(Equipment.criticality == "critical").count()
            
            # 장비 유형별 통계
            equipment_by_type = db.query(
                Equipment.type, 
                func.count(Equipment.id)
            ).group_by(Equipment.type).all()
            
            # 장비 위치별 통계
            equipment_by_location = db.query(
                Equipment.location, 
                func.count(Equipment.id)
            ).filter(Equipment.location.isnot(None)).group_by(Equipment.location).all()
            
            return {
                "total_equipment": total,
                "active_equipment": active,
                "maintenance_equipment": maintenance,
                "critical_equipment": critical,
                "equipment_by_type": dict(equipment_by_type),
                "equipment_by_location": dict(equipment_by_location)
            }
            
        except Exception as e:
            logger.error(f"장비 요약 조회 실패: {e}")
            return {
                "total_equipment": 0,
                "active_equipment": 0,
                "maintenance_equipment": 0,
                "critical_equipment": 0,
                "equipment_by_type": {},
                "equipment_by_location": {}
            }
    
    def get_sensor_summary(self, db: Session) -> Dict[str, Any]:
        """센서 요약 정보 조회"""
        try:
            total = db.query(Sensor).count()
            active = db.query(Sensor).filter(Sensor.status == "active").count()
            
            # 센서 유형별 통계
            sensors_by_type = db.query(
                Sensor.type, 
                func.count(Sensor.id)
            ).group_by(Sensor.type).all()
            
            # 장비별 센서 통계
            sensors_by_equipment = db.query(
                Sensor.equipment_id, 
                func.count(Sensor.id)
            ).group_by(Sensor.equipment_id).all()
            
            return {
                "total_sensors": total,
                "active_sensors": active,
                "sensors_by_type": dict(sensors_by_type),
                "sensors_by_equipment": dict(sensors_by_equipment)
            }
            
        except Exception as e:
            logger.error(f"센서 요약 조회 실패: {e}")
            return {
                "total_sensors": 0,
                "active_sensors": 0,
                "sensors_by_type": {},
                "sensors_by_equipment": {}
            }


# 전역 장비 서비스 인스턴스
equipment_service = EquipmentService() 