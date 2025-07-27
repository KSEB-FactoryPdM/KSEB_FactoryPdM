"""
센서 데이터 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.services.sensor_service import SensorService
from app.schemas.sensor import (
    SensorDataCreate,
    SensorDataResponse,
    SensorDataQuery,
    SensorDataListResponse,
    SensorDataBatch
)

router = APIRouter()


@router.post("/data", response_model=dict)
async def save_sensor_data(
    sensor_data: SensorDataCreate,
    db: Session = Depends(get_db)
):
    """센서 데이터 저장"""
    try:
        success = SensorService.save_sensor_data(db, sensor_data)
        if success:
            return {"message": "센서 데이터가 성공적으로 저장되었습니다"}
        else:
            raise HTTPException(status_code=500, detail="센서 데이터 저장 실패")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 데이터 저장 실패: {str(e)}")


@router.post("/data/batch", response_model=dict)
async def save_sensor_data_batch(
    batch_data: SensorDataBatch,
    db: Session = Depends(get_db)
):
    """센서 데이터 배치 저장"""
    try:
        success = SensorService.save_sensor_data_batch(db, batch_data.device_id, batch_data.sensor_data)
        if success:
            return {
                "message": "센서 데이터 배치 저장 완료",
                "device_id": batch_data.device_id,
                "count": len(batch_data.sensor_data)
            }
        else:
            raise HTTPException(status_code=500, detail="센서 데이터 배치 저장 실패")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 데이터 배치 저장 실패: {str(e)}")


@router.get("/data/{device_id}", response_model=SensorDataListResponse)
async def get_sensor_data(
    device_id: str,
    sensor_type: Optional[str] = Query(default=None, description="센서 유형"),
    start_time: Optional[datetime] = Query(default=None, description="시작 시간"),
    end_time: Optional[datetime] = Query(default=None, description="종료 시간"),
    limit: int = Query(default=1000, ge=1, le=10000, description="조회 개수 제한"),
    offset: int = Query(default=0, ge=0, description="오프셋"),
    db: Session = Depends(get_db)
):
    """센서 데이터 조회"""
    try:
        query = SensorDataQuery(
            device_id=device_id,
            sensor_type=sensor_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        sensor_data = SensorService.get_sensor_data(query)
        total = SensorService.get_sensor_data_count(device_id, sensor_type)
        
        return SensorDataListResponse(
            data=sensor_data,
            total=total,
            device_id=device_id,
            sensor_type=sensor_type,
            start_time=start_time,
            end_time=end_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 데이터 조회 실패: {str(e)}")


@router.get("/data/{device_id}/latest", response_model=SensorDataResponse)
async def get_latest_sensor_data(
    device_id: str,
    sensor_type: Optional[str] = Query(default=None, description="센서 유형"),
    db: Session = Depends(get_db)
):
    """최신 센서 데이터 조회"""
    try:
        latest_data = SensorService.get_latest_sensor_data(device_id, sensor_type)
        if not latest_data:
            raise HTTPException(status_code=404, detail="센서 데이터를 찾을 수 없습니다")
        return latest_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최신 센서 데이터 조회 실패: {str(e)}")


@router.get("/data/{device_id}/count")
async def get_sensor_data_count(
    device_id: str,
    sensor_type: Optional[str] = Query(default=None, description="센서 유형"),
    db: Session = Depends(get_db)
):
    """센서 데이터 개수 조회"""
    try:
        count = SensorService.get_sensor_data_count(device_id, sensor_type)
        return {
            "device_id": device_id,
            "sensor_type": sensor_type,
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"센서 데이터 개수 조회 실패: {str(e)}") 