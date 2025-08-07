"""
알림 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.websocket_manager import websocket_manager
from app.services.notification_service import notification_service
from app.schemas.notification import NotificationResponse, NotificationListResponse

router = APIRouter()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """실시간 알림 WebSocket 연결"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (필요시)
            data = await websocket.receive_text()
            # 여기서 클라이언트 메시지 처리 가능
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    device_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """알림 목록 조회"""
    try:
        notifications = notification_service.get_notifications(
            db=db, 
            device_id=device_id, 
            severity=severity, 
            limit=limit
        )
        
        return NotificationListResponse(
            notifications=notifications,
            total=len(notifications),
            page=1,
            size=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 조회 실패: {str(e)}")


@router.get("/stats")
async def get_notification_stats(db: Session = Depends(get_db)):
    """알림 통계 조회"""
    try:
        notifications = notification_service.get_notifications(db=db, limit=1000)
        
        stats = {
            "total_notifications": len(notifications),
            "critical_count": len([n for n in notifications if n.severity == "critical"]),
            "high_count": len([n for n in notifications if n.severity == "high"]),
            "medium_count": len([n for n in notifications if n.severity == "medium"]),
            "low_count": len([n for n in notifications if n.severity == "low"]),
            "websocket_connections": websocket_manager.get_connection_count()
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 통계 조회 실패: {str(e)}")


@router.get("/websocket/status")
async def get_websocket_status():
    """WebSocket 연결 상태 조회"""
    return websocket_manager.get_connection_info() 