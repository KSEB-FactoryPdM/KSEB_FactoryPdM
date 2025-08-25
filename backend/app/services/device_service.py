"""
장비 관리 서비스
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceResponse
from app.core.monitoring import update_active_devices

logger = logging.getLogger(__name__)


class DeviceService:
    """장비 관리 서비스"""
    
    @staticmethod
    def create_device(db: Session, device: DeviceCreate) -> DeviceResponse:
        """장비 생성"""
        try:
            db_device = Device(
                id=device.id,
                name=device.name,
                type=device.type,
                location=device.location,
                installation_date=device.installation_date,
                last_maintenance_date=device.last_maintenance_date,
                status=device.status
            )
            db.add(db_device)
            db.commit()
            db.refresh(db_device)
            
            logger.info(f"장비 생성 완료: {device.id}")
            return DeviceResponse.from_orm(db_device)
            
        except Exception as e:
            db.rollback()
            logger.error(f"장비 생성 실패: {e}")
            raise
    
    @staticmethod
    def get_device(db: Session, device_id: str) -> Optional[DeviceResponse]:
        """장비 조회"""
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device:
                return DeviceResponse.from_orm(device)
            return None
            
        except Exception as e:
            logger.error(f"장비 조회 실패: {e}")
            raise
    
    @staticmethod
    def get_devices(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[DeviceResponse]:
        """장비 목록 조회"""
        try:
            query = db.query(Device)
            
            if status:
                query = query.filter(Device.status == status)
            
            devices = query.offset(skip).limit(limit).all()
            
            # 활성 장비 수 업데이트
            active_count = db.query(Device).filter(Device.status == "active").count()
            update_active_devices(active_count)
            
            return [DeviceResponse.from_orm(device) for device in devices]
            
        except Exception as e:
            logger.error(f"장비 목록 조회 실패: {e}")
            raise
    
    @staticmethod
    def update_device(
        db: Session, 
        device_id: str, 
        device_update: DeviceUpdate
    ) -> Optional[DeviceResponse]:
        """장비 정보 업데이트"""
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return None
            
            update_data = device_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(device, field, value)
            
            device.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(device)
            
            logger.info(f"장비 업데이트 완료: {device_id}")
            return DeviceResponse.from_orm(device)
            
        except Exception as e:
            db.rollback()
            logger.error(f"장비 업데이트 실패: {e}")
            raise
    
    @staticmethod
    def delete_device(db: Session, device_id: str) -> bool:
        """장비 삭제"""
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return False
            
            db.delete(device)
            db.commit()
            
            logger.info(f"장비 삭제 완료: {device_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"장비 삭제 실패: {e}")
            raise
    
    @staticmethod
    def get_device_count(db: Session, status: Optional[str] = None) -> int:
        """장비 수 조회"""
        try:
            query = db.query(Device)
            if status:
                query = query.filter(Device.status == status)
            return query.count()
            
        except Exception as e:
            logger.error(f"장비 수 조회 실패: {e}")
            raise 