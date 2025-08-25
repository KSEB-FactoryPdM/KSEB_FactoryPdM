"""
WebSocket 매니저 - 실시간 알림 전송
"""
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 연결 관리 및 실시간 알림 전송"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """WebSocket 연결 수락"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_info[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.now(),
            "last_activity": datetime.now()
        }
        logger.info(f"WebSocket 연결됨: {user_id or 'anonymous'}")
    
    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        self.active_connections.discard(websocket)
        if websocket in self.connection_info:
            user_id = self.connection_info[websocket].get("user_id")
            del self.connection_info[websocket]
            logger.info(f"WebSocket 연결 해제됨: {user_id or 'anonymous'}")
    
    async def send_notification(self, notification_data: Dict[str, Any]):
        """실시간 알림 전송"""
        if not self.active_connections:
            logger.warning("활성 WebSocket 연결이 없습니다")
            return
        
        message = {
            "type": "notification",
            "timestamp": datetime.now().isoformat(),
            "data": notification_data
        }
        
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message))
                self.connection_info[websocket]["last_activity"] = datetime.now()
            except Exception as e:
                logger.error(f"WebSocket 메시지 전송 실패: {e}")
                disconnected.add(websocket)
        
        # 연결이 끊어진 WebSocket 제거
        for websocket in disconnected:
            self.disconnect(websocket)
        
        logger.info(f"알림 전송 완료: {len(self.active_connections)}개 연결")
    
    async def send_system_message(self, message: str, message_type: str = "info"):
        """시스템 메시지 전송"""
        system_message = {
            "type": "system",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "message_type": message_type
        }
        
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(system_message))
            except Exception as e:
                logger.error(f"시스템 메시지 전송 실패: {e}")
                disconnected.add(websocket)
        
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """모든 연결에 메시지 브로드캐스트"""
        if not self.active_connections:
            return
        
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"브로드캐스트 메시지 전송 실패: {e}")
                disconnected.add(websocket)
        
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def get_connection_count(self) -> int:
        """활성 연결 수 반환"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """연결 정보 반환"""
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "user_id": info.get("user_id"),
                    "connected_at": info.get("connected_at").isoformat(),
                    "last_activity": info.get("last_activity").isoformat()
                }
                for info in self.connection_info.values()
            ]
        }


# 전역 WebSocket 매니저 인스턴스
websocket_manager = WebSocketManager() 