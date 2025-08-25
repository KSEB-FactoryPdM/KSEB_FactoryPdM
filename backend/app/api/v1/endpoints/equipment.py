"""
장비 메타데이터 관련 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.equipment import (
    EquipmentCreate, EquipmentUpdate, EquipmentResponse, EquipmentWithSensors,
    SensorCreate, SensorUpdate, SensorResponse,
    MaintenanceScheduleCreate, MaintenanceScheduleResponse,
    MaintenanceHistoryCreate, MaintenanceHistoryResponse,
    EquipmentSummary, SensorSummary
)
from app.services.equipment_service import equipment_service

router = APIRouter()


# 장비 관련 엔드포인트
@router.post("/", response_model=EquipmentResponse)
async def create_equipment(
    equipment_create: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """장비 생성"""
    try:
        equipment = equipment_service.create_equipment(
            db=db,
            equipment_create=equipment_create
        )
        return equipment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 생성 실패: {str(e)}")


@router.get("/", response_model=List[EquipmentResponse])
async def get_equipments(
    type: Optional[str] = Query(None, description="장비 유형"),
    category: Optional[str] = Query(None, description="카테고리"),
    status: Optional[str] = Query(None, description="상태"),
    location: Optional[str] = Query(None, description="위치"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="반환할 항목 수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """장비 목록 조회"""
    try:
        equipments = equipment_service.get_equipments(
            db=db,
            type=type,
            category=category,
            status=status,
            location=location,
            skip=skip,
            limit=limit
        )
        return equipments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 목록 조회 실패: {str(e)}")


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """장비 상세 조회"""
    try:
        equipment = equipment_service.get_equipment(db=db, equipment_id=equipment_id)
        
        if not equipment:
            raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다")
        
        return equipment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 조회 실패: {str(e)}")


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: str,
    equipment_update: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """장비 업데이트"""
    try:
        equipment = equipment_service.update_equipment(
            db=db,
            equipment_id=equipment_id,
            equipment_update=equipment_update
        )
        
        if not equipment:
            raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다")
        
        return equipment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 업데이트 실패: {str(e)}")


@router.delete("/{equipment_id}")
async def delete_equipment(
    equipment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """장비 삭제"""
    try:
        success = equipment_service.delete_equipment(db=db, equipment_id=equipment_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다")
        
        return {"message": "장비 삭제 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 삭제 실패: {str(e)}")


@router.get("/{equipment_id}/with-sensors", response_model=EquipmentWithSensors)
async def get_equipment_with_sensors(
    equipment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """센서가 포함된 장비 조회"""
    try:
        equipment = equipment_service.get_equipment_with_sensors(db=db, equipment_id=equipment_id)
        
        if not equipment:
            raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다")
        
        return equipment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 및 센서 조회 실패: {str(e)}")


# 센서 관련 엔드포인트
@router.post("/sensors", response_model=SensorResponse)
async def create_sensor(
    sensor_create: SensorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """센서 생성"""
    try:
        sensor = equipment_service.create_sensor(
            db=db,
            sensor_create=sensor_create
        )
        return sensor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 생성 실패: {str(e)}")


@router.get("/sensors", response_model=List[SensorResponse])
async def get_sensors(
    equipment_id: Optional[str] = Query(None, description="장비 ID"),
    type: Optional[str] = Query(None, description="센서 유형"),
    status: Optional[str] = Query(None, description="상태"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="반환할 항목 수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """센서 목록 조회"""
    try:
        sensors = equipment_service.get_sensors(
            db=db,
            equipment_id=equipment_id,
            type=type,
            status=status,
            skip=skip,
            limit=limit
        )
        return sensors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 목록 조회 실패: {str(e)}")


@router.get("/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor(
    sensor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """센서 상세 조회"""
    try:
        sensor = equipment_service.get_sensor(db=db, sensor_id=sensor_id)
        
        if not sensor:
            raise HTTPException(status_code=404, detail="센서를 찾을 수 없습니다")
        
        return sensor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 조회 실패: {str(e)}")


@router.put("/sensors/{sensor_id}", response_model=SensorResponse)
async def update_sensor(
    sensor_id: str,
    sensor_update: SensorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """센서 업데이트"""
    try:
        sensor = equipment_service.update_sensor(
            db=db,
            sensor_id=sensor_id,
            sensor_update=sensor_update
        )
        
        if not sensor:
            raise HTTPException(status_code=404, detail="센서를 찾을 수 없습니다")
        
        return sensor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 업데이트 실패: {str(e)}")


@router.delete("/sensors/{sensor_id}")
async def delete_sensor(
    sensor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """센서 삭제"""
    try:
        success = equipment_service.delete_sensor(db=db, sensor_id=sensor_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="센서를 찾을 수 없습니다")
        
        return {"message": "센서 삭제 완료"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 삭제 실패: {str(e)}")


# 정비 일정 관련 엔드포인트
@router.post("/maintenance-schedules", response_model=MaintenanceScheduleResponse)
async def create_maintenance_schedule(
    schedule_create: MaintenanceScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """정비 일정 생성"""
    try:
        schedule = equipment_service.create_maintenance_schedule(
            db=db,
            schedule_create=schedule_create
        )
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정비 일정 생성 실패: {str(e)}")


@router.get("/maintenance-schedules", response_model=List[MaintenanceScheduleResponse])
async def get_maintenance_schedules(
    equipment_id: Optional[str] = Query(None, description="장비 ID"),
    status: Optional[str] = Query(None, description="상태"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="반환할 항목 수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """정비 일정 목록 조회"""
    try:
        schedules = equipment_service.get_maintenance_schedules(
            db=db,
            equipment_id=equipment_id,
            status=status,
            skip=skip,
            limit=limit
        )
        return schedules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정비 일정 조회 실패: {str(e)}")


# 정비 이력 관련 엔드포인트
@router.post("/maintenance-history", response_model=MaintenanceHistoryResponse)
async def create_maintenance_history(
    history_create: MaintenanceHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """정비 이력 생성"""
    try:
        history = equipment_service.create_maintenance_history(
            db=db,
            history_create=history_create
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정비 이력 생성 실패: {str(e)}")


@router.get("/maintenance-history", response_model=List[MaintenanceHistoryResponse])
async def get_maintenance_history(
    equipment_id: Optional[str] = Query(None, description="장비 ID"),
    maintenance_type: Optional[str] = Query(None, description="정비 유형"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="반환할 항목 수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """정비 이력 목록 조회"""
    try:
        histories = equipment_service.get_maintenance_history(
            db=db,
            equipment_id=equipment_id,
            maintenance_type=maintenance_type,
            skip=skip,
            limit=limit
        )
        return histories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정비 이력 조회 실패: {str(e)}")


# 요약 정보 관련 엔드포인트
@router.get("/summary/equipment", response_model=EquipmentSummary)
async def get_equipment_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """장비 요약 정보 조회"""
    try:
        summary = equipment_service.get_equipment_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 요약 조회 실패: {str(e)}")


@router.get("/summary/sensors", response_model=SensorSummary)
async def get_sensor_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """센서 요약 정보 조회"""
    try:
        summary = equipment_service.get_sensor_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 요약 조회 실패: {str(e)}") 