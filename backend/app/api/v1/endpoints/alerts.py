"""
알림(Alerts) 조회 API - 프론트 호환 경로
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.models.notification import Notification


router = APIRouter()


def _map_status_to_filters(status: Optional[str]) -> dict:
    # status=new -> acknowledged=False
    if status == "new":
        return {"acknowledged": False}
    return {}


@router.get("/", response_model=NotificationListResponse)
async def list_alerts(
    status: Optional[str] = Query(default=None, description="new|open|resolved 등 상태"),
    device_id: Optional[str] = Query(default=None, description="장비 ID"),
    severity: Optional[str] = Query(default=None, description="심각도"),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    try:
        filters = _map_status_to_filters(status)
        # 기존 서비스 재사용 (acknowledged 필터는 여기서 직접 적용)
        query = db.query(Notification)
        if device_id:
            query = query.filter(Notification.device_id == device_id)
        if severity:
            query = query.filter(Notification.severity == severity)
        if "acknowledged" in filters:
            query = query.filter(Notification.acknowledged == filters["acknowledged"])

        rows = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return NotificationListResponse(
            notifications=rows, total=len(rows), page=1, size=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 조회 실패: {e}")


@router.get("/{alert_id}", response_model=NotificationResponse)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    try:
        row = db.query(Notification).filter(Notification.id == alert_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 조회 실패: {e}")


