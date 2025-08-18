"""
슬랙 봇 서비스 - 다이렉트 메시지 전송
"""
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

from app.core.config import settings
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class SlackBotService:
    """슬랙 봇 서비스 - 다이렉트 메시지 전송"""
    
    def __init__(self):
        self.bot_token = getattr(settings, 'SLACK_BOT_TOKEN', None)
        self.admin_user_id = getattr(settings, 'SLACK_ADMIN_USER_ID', None)
        self.base_url = "https://slack.com/api"
        
    def send_direct_message(self, notification: Notification) -> bool:
        """다이렉트 메시지 전송"""
        try:
            if not self.bot_token or not self.admin_user_id:
                logger.warning("슬랙 봇 토큰 또는 관리자 사용자 ID가 설정되지 않았습니다")
                return False
            
            # 메시지 텍스트 생성
            message_text = self._format_message_text(notification)
            
            # 슬랙 API 호출
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }

            # 단순: 설정된 admin_user_id를 채널로 직접 사용 (D/C/G ID 권장)
            channel_id = self.admin_user_id
            if not channel_id:
                logger.error("슬랙 관리자 채널/사용자 ID가 설정되지 않았습니다")
                return False

            payload = {
                "channel": channel_id,
                "text": message_text,
                "blocks": self._create_message_blocks(notification)
            }

            response = requests.post(
                f"{self.base_url}/chat.postMessage",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    logger.info(f"슬랙 다이렉트 메시지 전송 성공: {notification.device_id}")
                    return True
                else:
                    error_msg = result.get('error', 'unknown_error')
                    logger.error(f"슬랙 API 오류: {error_msg}")
                    if error_msg == 'missing_scope':
                        logger.error("슬랙 봇에 필요한 권한이 없습니다. 다음 권한을 추가해주세요:")
                        logger.error("- chat:write")
                        logger.error("- im:write")
                        logger.error("- users:read")
                    return False
            else:
                logger.error(f"슬랙 API 호출 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"슬랙 다이렉트 메시지 전송 중 오류: {e}")
            return False

    # 간단 버전: 채널 해석/오픈 로직 제거
    
    def _format_message_text(self, notification: Notification) -> str:
        """메시지 텍스트 포맷팅"""
        severity_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚡",
            "low": "ℹ️"
        }
        
        emoji = severity_emoji.get(notification.severity, "📢")
        
        return (
            f"{emoji} *KSEB Factory 설비 이상 탐지*\n"
            f"• 장비: `{notification.device_id}`\n"
            f"• 센서: `{notification.sensor_id}`\n"
            f"• 이상 유형: `{notification.anomaly_type}`\n"
            f"• 심각도: `{notification.severity.upper()}`\n"
            f"• 메시지: {notification.message}"
        )
    
    def _create_message_blocks(self, notification: Notification) -> List[Dict]:
        """슬랙 블록 키트를 사용한 메시지 블록 생성"""
        severity_color = {
            "critical": "#ff0000",
            "high": "#ff6600", 
            "medium": "#ffcc00",
            "low": "#00cc00"
        }
        
        color = severity_color.get(notification.severity, "#cccccc")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 설비 이상 탐지 - {notification.device_id}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*장비 ID:*\n`{notification.device_id}`"
                    },
                    {
                        "type": "mrkdwn", 
                        "text": f"*센서 ID:*\n`{notification.sensor_id}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*이상 유형:*\n`{notification.anomaly_type}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*심각도:*\n`{notification.severity.upper()}`"
                    }
                ]
            }
        ]
        
        # 센서 값과 임계값이 있는 경우 추가
        if notification.sensor_value is not None or notification.threshold_value is not None:
            sensor_fields = []
            if notification.sensor_value is not None:
                try:
                    sensor_val = float(notification.sensor_value)
                    sensor_fields.append({
                        "type": "mrkdwn",
                        "text": f"*센서 값:*\n`{sensor_val:.2f}`"
                    })
                except (ValueError, TypeError):
                    sensor_fields.append({
                        "type": "mrkdwn",
                        "text": f"*센서 값:*\n`{notification.sensor_value}`"
                    })
            if notification.threshold_value is not None:
                try:
                    threshold_val = float(notification.threshold_value)
                    sensor_fields.append({
                        "type": "mrkdwn", 
                        "text": f"*임계값:*\n`{threshold_val:.2f}`"
                    })
                except (ValueError, TypeError):
                    sensor_fields.append({
                        "type": "mrkdwn", 
                        "text": f"*임계값:*\n`{notification.threshold_value}`"
                    })
            
            blocks.append({
                "type": "section",
                "fields": sensor_fields
            })
        
        # 상세 메시지 추가
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*상세 메시지:*\n{notification.message}"
            }
        })
        
        # 시간 정보 추가
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"발견 시간: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        # 액션 버튼 추가 (선택사항)
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "확인 완료",
                        "emoji": True
                    },
                    "style": "primary",
                    "value": f"ack_{notification.id}",
                    "action_id": "acknowledge_alert"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "상세 보기",
                        "emoji": True
                    },
                    "value": f"view_{notification.id}",
                    "action_id": "view_details"
                }
            ]
        })
        
        return blocks
    
    def send_test_message(self) -> bool:
        """테스트 메시지 전송"""
        try:
            if not self.bot_token or not self.admin_user_id:
                logger.warning("슬랙 봇 토큰 또는 관리자 사용자 ID가 설정되지 않았습니다")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json"
            }

            channel_id = self.admin_user_id
            if not channel_id:
                logger.error("테스트용 슬랙 채널/사용자 ID가 설정되지 않았습니다")
                return False

            payload = {
                "channel": channel_id,
                "text": "🧪 KSEB Factory 슬랙 봇 테스트 메시지입니다.",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🧪 *KSEB Factory 슬랙 봇 테스트*\n\n슬랙 봇이 정상적으로 작동하고 있습니다!"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/chat.postMessage",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    logger.info("슬랙 봇 테스트 메시지 전송 성공")
                    return True
                else:
                    logger.error(f"슬랙 API 오류: {result.get('error')}")
                    return False
            else:
                logger.error(f"슬랙 API 호출 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"슬랙 봇 테스트 메시지 전송 중 오류: {e}")
            return False


# 전역 인스턴스
slack_bot_service = SlackBotService()
