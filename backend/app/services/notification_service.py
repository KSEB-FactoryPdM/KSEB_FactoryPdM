"""
알림 서비스
"""
import logging
import smtplib
import json
import requests
from datetime import datetime
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
import os

from app.models.notification import Notification, NotificationChannel, NotificationLog, AlertRule
from app.models.device import Device
from app.models.sensor import Sensor
from app.schemas.notification import (
    NotificationCreate, NotificationUpdate, AlertMessage,
    NotificationChannelCreate, AlertRuleCreate
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """알림 서비스"""
    
    def __init__(self):
        self.channels = {}
        self._load_channels()
    
    def _load_channels(self):
        """알림 채널 로드"""
        try:
            # 기본 채널 설정
            self.channels = {
                "email": {
                    "enabled": bool(settings.EMAIL_USERNAME and settings.EMAIL_PASSWORD),
                    "config": {
                        "smtp_server": settings.EMAIL_SMTP_SERVER,
                        "smtp_port": settings.EMAIL_SMTP_PORT,
                        "username": settings.EMAIL_USERNAME,
                        "password": settings.EMAIL_PASSWORD
                    }
                },
                "kakao": {
                    "enabled": bool(settings.KAKAO_API_KEY and settings.KAKAO_TEMPLATE_ID),
                    "config": {
                        "api_key": settings.KAKAO_API_KEY,
                        "template_id": settings.KAKAO_TEMPLATE_ID
                    }
                },
                "tts": {
                    "enabled": True,
                    "config": {}
                }
            }
        except Exception as e:
            logger.error(f"알림 채널 로드 실패: {e}")
    
    def create_notification(
        self, 
        db: Session, 
        device_id: str,
        sensor_id: str,
        alert_type: str,
        anomaly_type: str,
        severity: str,
        message: str,
        sensor_value: Optional[float] = None,
        threshold_value: Optional[float] = None
    ) -> Notification:
        """알림 생성"""
        try:
            notification = Notification(
                device_id=device_id,
                sensor_id=sensor_id,
                alert_type=alert_type,
                anomaly_type=anomaly_type,
                severity=severity,
                message=message,
                detected_at=datetime.utcnow()
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # 실시간 알림 전송
            self._send_real_time_notifications(notification, sensor_value, threshold_value)
            
            logger.info(f"알림 생성 완료: {notification.id}")
            return notification
            
        except Exception as e:
            db.rollback()
            logger.error(f"알림 생성 실패: {e}")
            raise
    
    def _send_real_time_notifications(
        self, 
        notification: Notification,
        sensor_value: Optional[float] = None,
        threshold_value: Optional[float] = None
    ):
        """실시간 알림 전송"""
        try:
            # 알림 메시지 생성
            alert_message = AlertMessage(
                device_id=notification.device_id,
                sensor_id=notification.sensor_id,
                alert_type=notification.alert_type,
                anomaly_type=notification.anomaly_type,
                severity=notification.severity,
                message=notification.message,
                detected_at=notification.detected_at,
                sensor_value=sensor_value,
                threshold_value=threshold_value
            )
            
            # 각 채널별로 알림 전송
            if self.channels.get("email", {}).get("enabled", False):
                self._send_email_notification(alert_message)
            
            if self.channels.get("kakao", {}).get("enabled", False):
                self._send_kakao_notification(alert_message)
            
            if self.channels.get("tts", {}).get("enabled", False):
                self._send_tts_notification(alert_message)
            
            logger.info(f"실시간 알림 전송 완료: {notification.id}")
            
        except Exception as e:
            logger.error(f"실시간 알림 전송 실패: {e}")
    
    def _send_email_notification(self, alert_message: AlertMessage):
        """이메일 알림 전송"""
        try:
            config = self.channels["email"]["config"]
            
            if not all([config.get("smtp_server"), config.get("username"), config.get("password")]):
                logger.warning("이메일 설정이 불완전합니다")
                return
            
            # 관리자 이메일 주소를 환경변수에서 가져옴
            admin_email = os.getenv('ADMIN_EMAIL')
            if not admin_email:
                logger.warning("ADMIN_EMAIL 환경변수가 설정되지 않았습니다")
                return
            
            # 이메일 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = config["username"]
            msg['To'] = admin_email
            msg['Subject'] = f"[{alert_message.severity.upper()}] {alert_message.anomaly_type} 이상 탐지"
            
            # 이메일 본문
            body = f"""
            장비 이상 탐지 알림
            
            장비 ID: {alert_message.device_id}
            센서 ID: {alert_message.sensor_id}
            이상 유형: {alert_message.anomaly_type}
            심각도: {alert_message.severity}
            알림 유형: {alert_message.alert_type}
            감지 시간: {alert_message.detected_at}
            
            메시지: {alert_message.message}
            
            센서 값: {alert_message.sensor_value}
            임계값: {alert_message.threshold_value}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 이메일 전송
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
            server.login(config["username"], config["password"])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"이메일 알림 전송 완료: {alert_message.device_id}")
            
        except Exception as e:
            logger.error(f"이메일 알림 전송 실패: {e}")
    
    def _send_kakao_notification(self, alert_message: AlertMessage):
        """카카오 알림톡 전송"""
        try:
            config = self.channels["kakao"]["config"]
            
            if not all([config.get("api_key"), config.get("template_id")]):
                logger.warning("카카오 알림톡 설정이 불완전합니다")
                return
            
            # 카카오 알림톡 설정을 환경변수에서 가져옴
            kakao_userid = os.getenv('KAKAO_USERID')
            kakao_sender = os.getenv('KAKAO_SENDER')  
            kakao_receiver = os.getenv('KAKAO_RECEIVER')
            kakao_token = os.getenv('KAKAO_TOKEN', '')
            
            if not all([kakao_userid, kakao_sender, kakao_receiver]):
                logger.warning("카카오 알림톡 필수 환경변수가 설정되지 않았습니다 (KAKAO_USERID, KAKAO_SENDER, KAKAO_RECEIVER)")
                return
            
            # 카카오 알림톡 API 호출
            url = "https://kakaoapi.aligo.in/akv10/talk/add/"
            
            data = {
                "apikey": config["api_key"],
                "userid": kakao_userid,
                "token": kakao_token,
                "sender": kakao_sender,
                "tpl_code": config["template_id"],
                "receiver": kakao_receiver,
                "msg": f"[{alert_message.severity.upper()}] {alert_message.anomaly_type} 이상 탐지\n장비: {alert_message.device_id}\n센서: {alert_message.sensor_id}\n시간: {alert_message.detected_at}\n{alert_message.message}"
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result_code") == "1":
                    logger.info(f"카카오 알림톡 전송 완료: {alert_message.device_id}")
                else:
                    logger.error(f"카카오 알림톡 전송 실패: {result}")
            else:
                logger.error(f"카카오 알림톡 API 오류: {response.status_code}")
                
        except Exception as e:
            logger.error(f"카카오 알림톡 전송 실패: {e}")
    
    def _send_tts_notification(self, alert_message: AlertMessage):
        """TTS 음성 알림 전송"""
        try:
            # TTS 메시지 생성
            tts_message = f"""
            경고! {alert_message.device_id} 장비에서 {alert_message.anomaly_type} 이상이 탐지되었습니다.
            심각도는 {alert_message.severity}입니다.
            즉시 확인이 필요합니다.
            """
            
            # TTS 시스템 호출 (실제 구현에서는 TTS 엔진 연동)
            logger.info(f"TTS 알림 메시지: {tts_message}")
            
            # 여기에 실제 TTS 시스템 연동 코드 추가
            # 예: pyttsx3, gTTS, Azure Speech Service 등
            
        except Exception as e:
            logger.error(f"TTS 알림 전송 실패: {e}")
    
    def get_notifications(
        self, 
        db: Session, 
        device_id: Optional[str] = None,
        alert_type: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """알림 목록 조회"""
        query = db.query(Notification)
        
        if device_id:
            query = query.filter(Notification.device_id == device_id)
        
        if alert_type:
            query = query.filter(Notification.alert_type == alert_type)
        
        if acknowledged is not None:
            query = query.filter(Notification.acknowledged == acknowledged)
        
        return query.order_by(Notification.detected_at.desc()).offset(skip).limit(limit).all()
    
    def acknowledge_notification(
        self, 
        db: Session, 
        notification_id: int, 
        acknowledged_by: str
    ) -> Optional[Notification]:
        """알림 확인 처리"""
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            
            if not notification:
                return None
            
            notification.acknowledged = True
            notification.acknowledged_by = acknowledged_by
            notification.acknowledged_at = datetime.utcnow()
            
            db.commit()
            db.refresh(notification)
            
            logger.info(f"알림 확인 처리 완료: {notification_id}")
            return notification
            
        except Exception as e:
            db.rollback()
            logger.error(f"알림 확인 처리 실패: {e}")
            return None
    
    def create_alert_rule(
        self, 
        db: Session, 
        alert_rule_create: AlertRuleCreate
    ) -> AlertRule:
        """알림 규칙 생성"""
        try:
            alert_rule = AlertRule(**alert_rule_create.dict())
            
            db.add(alert_rule)
            db.commit()
            db.refresh(alert_rule)
            
            logger.info(f"알림 규칙 생성 완료: {alert_rule.id}")
            return alert_rule
            
        except Exception as e:
            db.rollback()
            logger.error(f"알림 규칙 생성 실패: {e}")
            raise
    
    def get_alert_rules(
        self, 
        db: Session, 
        device_id: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> List[AlertRule]:
        """알림 규칙 목록 조회"""
        query = db.query(AlertRule)
        
        if device_id:
            query = query.filter(AlertRule.device_id == device_id)
        
        if enabled is not None:
            query = query.filter(AlertRule.enabled == enabled)
        
        return query.all()
    
    def check_alert_conditions(
        self, 
        db: Session, 
        device_id: str,
        sensor_type: str,
        sensor_value: float
    ) -> List[AlertRule]:
        """알림 조건 확인"""
        try:
            rules = self.get_alert_rules(db, device_id=device_id, enabled=True)
            triggered_rules = []
            
            for rule in rules:
                if rule.sensor_type != sensor_type:
                    continue
                
                threshold = float(rule.threshold_value)
                
                if rule.condition == "gt" and sensor_value > threshold:
                    triggered_rules.append(rule)
                elif rule.condition == "lt" and sensor_value < threshold:
                    triggered_rules.append(rule)
                elif rule.condition == "eq" and sensor_value == threshold:
                    triggered_rules.append(rule)
                elif rule.condition == "range":
                    # 범위 조건 처리 (예: "10,20" -> 10 < value < 20)
                    try:
                        min_val, max_val = map(float, rule.threshold_value.split(","))
                        if min_val < sensor_value < max_val:
                            triggered_rules.append(rule)
                    except:
                        continue
            
            return triggered_rules
            
        except Exception as e:
            logger.error(f"알림 조건 확인 실패: {e}")
            return []
    
    def get_notification_summary(self, db: Session) -> Dict[str, Any]:
        """알림 요약 정보 조회"""
        try:
            total = db.query(Notification).count()
            unacknowledged = db.query(Notification).filter(Notification.acknowledged == False).count()
            critical = db.query(Notification).filter(Notification.alert_type == "critical").count()
            warning = db.query(Notification).filter(Notification.alert_type == "warning").count()
            
            recent = db.query(Notification).order_by(Notification.detected_at.desc()).limit(10).all()
            
            return {
                "total_notifications": total,
                "unacknowledged_count": unacknowledged,
                "critical_count": critical,
                "warning_count": warning,
                "recent_notifications": recent
            }
            
        except Exception as e:
            logger.error(f"알림 요약 조회 실패: {e}")
            return {
                "total_notifications": 0,
                "unacknowledged_count": 0,
                "critical_count": 0,
                "warning_count": 0,
                "recent_notifications": []
            }


# 전역 알림 서비스 인스턴스
notification_service = NotificationService() 