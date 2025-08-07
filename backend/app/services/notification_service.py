"""
알림 서비스 - 슬랙, 이메일, 웹 알림 통합
"""
import logging
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.websocket_manager import websocket_manager
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.services.slack_bot_service import slack_bot_service

logger = logging.getLogger(__name__)


class NotificationService:
    """통합 알림 서비스"""
    
    def __init__(self):
        self.slack_webhook_url = settings.SLACK_WEBHOOK_URL
        self.email_smtp_server = settings.EMAIL_SMTP_SERVER
        self.email_smtp_port = settings.EMAIL_SMTP_PORT
        self.email_username = settings.EMAIL_USERNAME
        self.email_password = settings.EMAIL_PASSWORD
        
    def create_notification(self, 
                          db: Session,
                          device_id: str,
                          sensor_id: str,
                          alert_type: str,
                          anomaly_type: str,
                          severity: str,
                          message: str,
                          sensor_value: Optional[float] = None,
                          threshold_value: Optional[float] = None) -> Notification:
        """통합 알림 생성 및 전송"""
        try:
            # 1. 데이터베이스에 알림 저장
            notification_data = NotificationCreate(
                device_id=device_id,
                sensor_id=sensor_id,
                alert_type=alert_type,
                anomaly_type=anomaly_type,
                severity=severity,
                message=message,
                sensor_value=sensor_value,
                threshold_value=threshold_value,
                created_at=datetime.now()
            )
            
            notification = Notification(**notification_data.dict())
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # 2. 슬랙 웹훅 알림 전송
            self.send_slack_notification(notification)
            
            # 3. 슬랙 봇 다이렉트 메시지 전송
            self.send_slack_direct_message(notification)
            
            # 4. 이메일 알림 전송
            self.send_email_notification(notification)
            
            # 5. 웹 알림 이벤트 생성
            self.create_web_notification_event(notification)
            
            logger.info(f"통합 알림 전송 완료: {device_id} - {severity}")
            return notification
            
        except Exception as e:
            logger.error(f"알림 생성 실패: {e}")
            raise
    
    def send_slack_notification(self, notification: Notification):
        """슬랙 알림 전송"""
        try:
            if not self.slack_webhook_url:
                logger.warning("슬랙 웹훅 URL이 설정되지 않았습니다")
                return
            
            # 슬랙 메시지 포맷팅
            color_map = {
                "critical": "#ff0000",  # 빨간색
                "high": "#ff6600",      # 주황색
                "medium": "#ffcc00",    # 노란색
                "low": "#00cc00"        # 초록색
            }
            
            color = color_map.get(notification.severity, "#cccccc")
            
            slack_message = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"🚨 설비 이상 탐지 - {notification.device_id}",
                        "fields": [
                            {
                                "title": "장비 ID",
                                "value": notification.device_id,
                                "short": True
                            },
                            {
                                "title": "센서 ID", 
                                "value": notification.sensor_id,
                                "short": True
                            },
                            {
                                "title": "이상 유형",
                                "value": notification.anomaly_type,
                                "short": True
                            },
                            {
                                "title": "심각도",
                                "value": notification.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "센서 값",
                                "value": f"{notification.sensor_value:.2f}" if notification.sensor_value else "N/A",
                                "short": True
                            },
                            {
                                "title": "임계값",
                                "value": f"{notification.threshold_value:.2f}" if notification.threshold_value else "N/A",
                                "short": True
                            },
                            {
                                "title": "상세 메시지",
                                "value": notification.message,
                                "short": False
                            }
                        ],
                        "footer": "KSEB Factory PdM System",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            # 슬랙 API 호출
            response = requests.post(
                self.slack_webhook_url,
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"슬랙 알림 전송 성공: {notification.device_id}")
            else:
                logger.error(f"슬랙 알림 전송 실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"슬랙 알림 전송 중 오류: {e}")
    
    def send_slack_direct_message(self, notification: Notification):
        """슬랙 봇 다이렉트 메시지 전송"""
        try:
            success = slack_bot_service.send_direct_message(notification)
            if success:
                logger.info(f"슬랙 다이렉트 메시지 전송 성공: {notification.device_id}")
            else:
                logger.warning(f"슬랙 다이렉트 메시지 전송 실패: {notification.device_id}")
        except Exception as e:
            logger.error(f"슬랙 다이렉트 메시지 전송 중 오류: {e}")
    
    def send_email_notification(self, notification: Notification):
        """이메일 알림 전송"""
        try:
            if not all([self.email_username, self.email_password]):
                logger.warning("이메일 설정이 완료되지 않았습니다")
                return
            
            # 이메일 메시지 생성
            subject = f"[KSEB Factory] 설비 이상 탐지 - {notification.device_id}"
            
            html_content = f"""
            <html>
            <body>
                <h2 style="color: {'#ff0000' if notification.severity == 'critical' else '#ff6600' if notification.severity == 'high' else '#ffcc00' if notification.severity == 'medium' else '#00cc00'};">
                    🚨 설비 이상 탐지 알림
                </h2>
                
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">장비 ID</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{notification.device_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">센서 ID</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{notification.sensor_id}</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">이상 유형</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{notification.anomaly_type}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">심각도</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{notification.severity.upper()}</td>
                    </tr>
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">센서 값</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{notification.sensor_value:.2f if notification.sensor_value else 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">임계값</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{notification.threshold_value:.2f if notification.threshold_value else 'N/A'}</td>
                    </tr>
                </table>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px;">
                    <strong>상세 메시지:</strong><br>
                    {notification.message}
                </div>
                
                <p style="margin-top: 20px; color: #666; font-size: 12px;">
                    발송 시간: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}<br>
                    KSEB Factory Predictive Maintenance System
                </p>
            </body>
            </html>
            """
            
            # 이메일 전송
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_username
            msg['To'] = settings.ADMIN_EMAIL  # 관리자 이메일로 전송
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.email_smtp_server, self.email_smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
            
            logger.info(f"이메일 알림 전송 성공: {notification.device_id}")
            
        except Exception as e:
            logger.error(f"이메일 알림 전송 중 오류: {e}")
    
    def create_web_notification_event(self, notification: Notification):
        """웹 알림 이벤트 생성 (WebSocket용)"""
        try:
            # WebSocket을 통해 실시간 알림 전송
            event_data = {
                "id": notification.id,
                "device_id": notification.device_id,
                "sensor_id": notification.sensor_id,
                "alert_type": notification.alert_type,
                "anomaly_type": notification.anomaly_type,
                "severity": notification.severity,
                "message": notification.message,
                "sensor_value": notification.sensor_value,
                "threshold_value": notification.threshold_value,
                "created_at": notification.created_at.isoformat(),
                "tts_message": self.generate_tts_message(notification)
            }
            
            # WebSocket 매니저를 통해 전송
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(websocket_manager.send_notification(event_data))
            except RuntimeError:
                # 이벤트 루프가 없는 경우 (백그라운드에서 실행)
                logger.info(f"웹 알림 이벤트 생성: {notification.device_id}")
            
        except Exception as e:
            logger.error(f"웹 알림 이벤트 생성 중 오류: {e}")
    
    def generate_tts_message(self, notification: Notification) -> str:
        """TTS용 메시지 생성"""
        severity_korean = {
            "critical": "치명적",
            "high": "높음", 
            "medium": "보통",
            "low": "낮음"
        }
        
        tts_message = f"""
        경고. {notification.device_id} 장비에서 {notification.anomaly_type} 이상이 탐지되었습니다. 
        심각도는 {severity_korean.get(notification.severity, notification.severity)}입니다. 
        즉시 확인이 필요합니다.
        """
        
        return tts_message.strip()
    
    def get_notifications(self, db: Session, device_id: Optional[str] = None, 
                         severity: Optional[str] = None, limit: int = 100) -> List[Notification]:
        """알림 조회"""
        query = db.query(Notification)
        
        if device_id:
            query = query.filter(Notification.device_id == device_id)
        
        if severity:
            query = query.filter(Notification.severity == severity)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()


# 전역 인스턴스
notification_service = NotificationService() 