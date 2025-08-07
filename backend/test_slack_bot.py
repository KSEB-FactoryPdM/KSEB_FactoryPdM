#!/usr/bin/env python3
"""
슬랙 봇 테스트 스크립트
"""
import os
import sys
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.slack_bot_service import slack_bot_service
from app.models.notification import Notification


def test_slack_bot_direct():
    """슬랙 봇 다이렉트 테스트"""
    print("🧪 슬랙 봇 다이렉트 메시지 테스트 시작...")
    
    # 테스트용 알림 객체 생성
    test_notification = Notification(
        id=999,
        device_id="TEST-EQ-001",
        sensor_id="TEMP-001",
        alert_type="warning",
        anomaly_type="temperature_high",
        severity="high",
        message="테스트 알림: 온도가 임계값을 초과했습니다.",
        sensor_value="85.5",
        threshold_value="80.0",
        detected_at=datetime.now(),
        created_at=datetime.now()
    )
    
    # 슬랙 봇으로 다이렉트 메시지 전송
    success = slack_bot_service.send_direct_message(test_notification)
    
    if success:
        print("✅ 슬랙 봇 다이렉트 메시지 전송 성공!")
    else:
        print("❌ 슬랙 봇 다이렉트 메시지 전송 실패!")
    
    return success


def test_slack_bot_api():
    """API를 통한 슬랙 봇 테스트"""
    print("🌐 API를 통한 슬랙 봇 테스트 시작...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/notifications/test-slack-bot",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ API 슬랙 봇 테스트 성공!")
            print(f"응답: {response.json()}")
            return True
        else:
            print(f"❌ API 슬랙 봇 테스트 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
        return False


def test_slack_bot_simple():
    """간단한 테스트 메시지 전송"""
    print("📝 간단한 테스트 메시지 전송...")
    
    success = slack_bot_service.send_test_message()
    
    if success:
        print("✅ 간단한 테스트 메시지 전송 성공!")
    else:
        print("❌ 간단한 테스트 메시지 전송 실패!")
    
    return success


def main():
    """메인 테스트 함수"""
    print("🚀 KSEB Factory 슬랙 봇 테스트 시작")
    print("=" * 50)
    
    # 환경 변수 확인
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    admin_user_id = os.getenv("SLACK_ADMIN_USER_ID")
    
    if not bot_token:
        print("❌ SLACK_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일에 SLACK_BOT_TOKEN을 설정해주세요.")
        return False
    
    if not admin_user_id:
        print("❌ SLACK_ADMIN_USER_ID 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일에 SLACK_ADMIN_USER_ID를 설정해주세요.")
        return False
    
    print(f"✅ 슬랙 봇 토큰: {bot_token[:20]}...")
    print(f"✅ 관리자 사용자 ID: {admin_user_id}")
    print()
    
    # 테스트 실행
    tests = [
        ("간단한 테스트 메시지", test_slack_bot_simple),
        ("다이렉트 메시지", test_slack_bot_direct),
        ("API 테스트", test_slack_bot_api),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name} 테스트 중...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 오류 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약:")
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n총 {total_count}개 테스트 중 {success_count}개 성공")
    
    if success_count == total_count:
        print("🎉 모든 테스트가 성공했습니다!")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 설정을 확인해주세요.")
        return False


if __name__ == "__main__":
    main()
