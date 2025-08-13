"""
장비 관리 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.services.device_service import DeviceService
from app.schemas.device import (
    DeviceCreate, 
    DeviceUpdate, 
    DeviceResponse, 
    DeviceListResponse
)
from fastapi import Body
from datetime import datetime
from app.models.notification import Notification

router = APIRouter()


@router.post("/", response_model=DeviceResponse)
async def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db)
):
    """장비 생성"""
    try:
        # 기존 장비 확인
        existing_device = DeviceService.get_device(db, device.id)
        if existing_device:
            raise HTTPException(status_code=400, detail="이미 존재하는 장비 ID입니다")
        
        return DeviceService.create_device(db, device)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 생성 실패: {str(e)}")


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """장비 조회"""
    try:
        device = DeviceService.get_device(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다")
        return device
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 조회 실패: {str(e)}")


@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    skip: int = Query(default=0, ge=0, description="건너뛸 개수"),
    limit: int = Query(default=100, ge=1, le=1000, description="조회할 개수"),
    status: Optional[str] = Query(default=None, description="장비 상태 필터"),
    db: Session = Depends(get_db)
):
    """장비 목록 조회"""
    try:
        devices = DeviceService.get_devices(db, skip=skip, limit=limit, status=status)
        total = DeviceService.get_device_count(db, status=status)
        
        return DeviceListResponse(
            devices=devices,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 목록 조회 실패: {str(e)}")


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """장비 정보 업데이트"""
    try:
        updated_device = DeviceService.update_device(db, device_id, device_update)
        if not updated_device:
            raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다")
        return updated_device
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 업데이트 실패: {str(e)}")


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """장비 삭제"""
    try:
        success = DeviceService.delete_device(db, device_id)
        if not success:
            raise HTTPException(status_code=404, detail="장비를 찾을 수 없습니다")
        return {"message": "장비가 성공적으로 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"장비 삭제 실패: {str(e)}") 


# 추가 기능: 임계치, 제어, 정비 요청 (프론트 스펙 대응)
@router.get("/{device_id}/threshold", response_model=dict)
async def get_device_threshold(device_id: str):
    # 실제로는 장비 설정 테이블에서 조회
    return {"device_id": device_id, "threshold": 50.0, "updated_at": datetime.utcnow().isoformat()}


@router.post("/{device_id}/threshold", response_model=dict)
async def set_device_threshold(device_id: str, payload: dict = Body(...)):
    # 실제로는 저장 후 감사 로그 기록
    return {"device_id": device_id, "threshold": float(payload.get("threshold", 0)), "updated_at": datetime.utcnow().isoformat()}


@router.post("/{device_id}/acknowledge", response_model=dict)
async def acknowledge_alert(device_id: str, db: Session = Depends(get_db)):
    # 최신 미확인 알림 1건을 ACK 처리 (예시)
    row = (
        db.query(Notification)
        .filter(Notification.device_id == device_id, Notification.acknowledged == False)  # noqa: E712
        .order_by(Notification.created_at.desc())
        .first()
    )
    if row:
        row.acknowledged = True
        row.acknowledged_at = datetime.utcnow()
        db.commit()
    return {"ok": True, "action": "acknowledge", "device_id": device_id, "time": datetime.utcnow().isoformat()}


@router.post("/{device_id}/stop", response_model=dict)
async def remote_stop_device(device_id: str):
    # 실제로는 제어 명령 발행 (예: MQTT/Kafka topic)
    return {"ok": True, "action": "stop", "device_id": device_id, "time": datetime.utcnow().isoformat()}


@router.post("/{device_id}/maintenance-request", response_model=dict)
async def request_maintenance(device_id: str, reason: Optional[str] = Body(default=None, embed=True)):
    # 실제로는 정비요청 테이블에 기록
    return {"ok": True, "action": "maintenance-request", "device_id": device_id, "reason": reason, "time": datetime.utcnow().isoformat()}