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