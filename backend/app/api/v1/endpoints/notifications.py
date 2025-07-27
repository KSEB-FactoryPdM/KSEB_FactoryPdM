"""
알림 관련 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse, NotificationUpdate, NotificationSummary,
    NotificationChannelResponse, AlertRuleCreate, AlertRuleResponse
)
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    device_id: Optional[str] = Query(None, description="장비 ID"),
    alert_type: Optional[str] = Query(None, description="알림 유형"),
    acknowledged: Optional[bool] = Query(None, description="확인 여부"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="반환할 항목 수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """알림 목록 조회"""
    try:
        notifications = notification_service.get_notifications(
            db=db,
            device_id=device_id,
            alert_type=alert_type,
            acknowledged=acknowledged,
            skip=skip,
            limit=limit
        )
        return notifications
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 목록 조회 실패: {str(e)}")


@router.get("/summary", response_model=NotificationSummary)
async def get_notification_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """알림 요약 정보 조회"""
    try:
        summary = notification_service.get_notification_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 요약 조회 실패: {str(e)}")


@router.put("/{notification_id}/acknowledge")
async def acknowledge_notification(
    notification_id: int,
    acknowledged_by: str = Query(..., description="확인 처리자"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """알림 확인 처리"""
    try:
        notification = notification_service.acknowledge_notification(
            db=db,
            notification_id=notification_id,
            acknowledged_by=acknowledged_by
        )
        
        if not notification:
            raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
        
        return {"message": "알림 확인 처리 완료", "notification_id": notification_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 확인 처리 실패: {str(e)}")


@router.get("/channels", response_model=List[NotificationChannelResponse])
async def get_notification_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """알림 채널 목록 조회"""
    try:
        # 실제 구현에서는 DB에서 채널 정보를 조회
        # 현재는 기본 채널 정보 반환
        channels = [
            {
                "id": 1,
                "name": "email",
                "enabled": True,
                "config": {"smtp_server": "smtp.gmail.com", "smtp_port": 587},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "kakao",
                "enabled": True,
                "config": {"api_key": "your_api_key", "template_id": "your_template_id"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 3,
                "name": "tts",
                "enabled": True,
                "config": {},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 채널 조회 실패: {str(e)}")


@router.post("/alert-rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    alert_rule_create: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """알림 규칙 생성"""
    try:
        alert_rule = notification_service.create_alert_rule(
            db=db,
            alert_rule_create=alert_rule_create
        )
        return alert_rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 규칙 생성 실패: {str(e)}")


@router.get("/alert-rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    device_id: Optional[str] = Query(None, description="장비 ID"),
    enabled: Optional[bool] = Query(None, description="활성화 여부"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """알림 규칙 목록 조회"""
    try:
        alert_rules = notification_service.get_alert_rules(
            db=db,
            device_id=device_id,
            enabled=enabled
        )
        return alert_rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 규칙 조회 실패: {str(e)}")


@router.post("/test-notification")
async def test_notification(
    device_id: str = Query(..., description="장비 ID"),
    sensor_id: str = Query(..., description="센서 ID"),
    alert_type: str = Query(..., description="알림 유형"),
    message: str = Query(..., description="테스트 메시지"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """테스트 알림 전송"""
    try:
        notification = notification_service.create_notification(
            db=db,
            device_id=device_id,
            sensor_id=sensor_id,
            alert_type=alert_type,
            anomaly_type="test",
            severity="medium",
            message=message
        )
        return {"message": "테스트 알림 전송 완료", "notification_id": notification.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"테스트 알림 전송 실패: {str(e)}") 