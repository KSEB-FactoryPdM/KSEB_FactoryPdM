#!/usr/bin/env python3
"""
KSEB Factory 통합 알림 테스트 스크립트
- 슬랙 + 이메일 동시 전송
- ML 모델 연동 테스트
- 실제 센서 데이터 시뮬레이션
"""
import os
import sys
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.notification_service import notification_service
from app.services.slack_bot_service import slack_bot_service
from app.models.notification import Notification

# ML 모델 관련 import (향후 추가될 예정)
try:
    from app.ml.anomaly_detection import AnomalyDetector
    from app.ml.rul_prediction import RULPredictor
    ML_AVAILABLE = True
except ImportError:
    print("⚠️  ML 모델이 아직 로드되지 않았습니다. models/ 디렉토리에 .pkl 파일을 추가해주세요.")
    ML_AVAILABLE = False


def test_integrated_notifications():
    """통합 알림 테스트 - 슬랙 + 이메일"""
    print("🚀 KSEB Factory 통합 알림 테스트")
    print("=" * 60)
    
    # 테스트용 알림 객체 생성
    test_notification = Notification(
        id=999,
        device_id="TEST-EQ-001",
        sensor_id="TEMP-001",
        alert_type="warning",
        anomaly_type="temperature_high",
        severity="high",
        message="통합 테스트 알림: 온도가 임계값을 초과했습니다. 슬랙과 이메일로 동시 알림이 전송됩니다.",
        sensor_value="87.3",
        threshold_value="80.0",
        detected_at=datetime.now(),
        created_at=datetime.now()
    )
    
    print("📋 테스트 알림 정보:")
    print(f"   장비: {test_notification.device_id}")
    print(f"   센서: {test_notification.sensor_id}")
    print(f"   이상 유형: {test_notification.anomaly_type}")
    print(f"   심각도: {test_notification.severity.upper()}")
    print(f"   센서 값: {test_notification.sensor_value}")
    print(f"   임계값: {test_notification.threshold_value}")
    print()
    
    # 1. 슬랙 봇 다이렉트 메시지 테스트
    print("📱 1. 슬랙 봇 다이렉트 메시지 전송...")
    try:
        slack_success = slack_bot_service.send_direct_message(test_notification)
        if slack_success:
            print("   ✅ 슬랙 다이렉트 메시지 전송 성공!")
        else:
            print("   ❌ 슬랙 다이렉트 메시지 전송 실패")
    except Exception as e:
        print(f"   ❌ 슬랙 전송 중 오류: {e}")
    
    print()
    
    # 2. 이메일 알림 테스트
    print("📧 2. 이메일 알림 전송...")
    try:
        notification_service.send_email_notification(test_notification)
        print("   ✅ 이메일 알림 전송 성공!")
    except Exception as e:
        print(f"   ❌ 이메일 전송 중 오류: {e}")
    
    print()
    print("=" * 60)
    print("🎉 통합 알림 테스트 완료!")
    print()
    print("📱 슬랙에서 확인하세요:")
    print("   - 다이렉트 메시지로 설비 이상 알림")
    print()
    print("📧 Gmail에서 확인하세요:")
    print("   - jinsatba0928@gmail.com 받은 편지함")
    print("   - 제목: [KSEB Factory] 설비 이상 탐지 - TEST-EQ-001")
    print()
    print("🔔 실제 운영에서는 다음 상황에서 자동으로 알림이 전송됩니다:")
    print("   - 센서 값이 임계값을 초과할 때")
    print("   - AI 모델이 이상을 탐지할 때")
    print("   - 설비 잔여 수명이 임계값 이하로 떨어질 때")
    print("   - 시스템 오류가 발생할 때")


def check_notification_settings():
    """알림 설정 확인"""
    print("🔍 알림 설정 확인...")
    print()
    
    # 슬랙 설정
    print("📱 슬랙 설정:")
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    slack_user_id = os.getenv("SLACK_ADMIN_USER_ID")
    
    if slack_token:
        print(f"   ✅ SLACK_BOT_TOKEN: {'*' * 20}")
    else:
        print("   ❌ SLACK_BOT_TOKEN: 설정되지 않음")
    
    if slack_user_id:
        print(f"   ✅ SLACK_ADMIN_USER_ID: {slack_user_id}")
    else:
        print("   ❌ SLACK_ADMIN_USER_ID: 설정되지 않음")
    
    print()
    
    # 이메일 설정
    print("📧 이메일 설정:")
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL")
    
    if email_username:
        print(f"   ✅ EMAIL_USERNAME: {email_username}")
    else:
        print("   ❌ EMAIL_USERNAME: 설정되지 않음")
    
    if email_password:
        print(f"   ✅ EMAIL_PASSWORD: {'*' * 16}")
    else:
        print("   ❌ EMAIL_PASSWORD: 설정되지 않음")
    
    if admin_email:
        print(f"   ✅ ADMIN_EMAIL: {admin_email}")
    else:
        print("   ❌ ADMIN_EMAIL: 설정되지 않음")
    
    print()


def check_ml_models():
    """ML 모델 상태 확인"""
    print("🤖 ML 모델 상태 확인...")
    print()
    
    models_dir = os.path.join(os.path.dirname(__file__), "app", "models")
    
    if not os.path.exists(models_dir):
        print(f"   ❌ 모델 디렉토리가 없습니다: {models_dir}")
        return False
    
    pkl_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    
    if not pkl_files:
        print(f"   ❌ .pkl 파일이 없습니다: {models_dir}")
        print("   📝 models/ 디렉토리에 다음 파일들을 추가해주세요:")
        print("      - anomaly_detection_model.pkl")
        print("      - rul_prediction_model.pkl")
        return False
    
    print(f"   ✅ 발견된 모델 파일들:")
    for pkl_file in pkl_files:
        file_path = os.path.join(models_dir, pkl_file)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        print(f"      - {pkl_file} ({file_size:.1f} MB)")
    
    print()
    return True


def generate_sensor_data():
    """센서 데이터 시뮬레이션"""
    print("📊 센서 데이터 시뮬레이션...")
    print()
    
    # 실제 센서 데이터 패턴 시뮬레이션
    sensor_data = {
        "temperature": {
            "normal": (60, 75),      # 정상 온도 범위
            "warning": (75, 85),     # 경고 온도 범위
            "critical": (85, 95)     # 위험 온도 범위
        },
        "vibration": {
            "normal": (0.1, 0.5),    # 정상 진동 범위
            "warning": (0.5, 1.0),   # 경고 진동 범위
            "critical": (1.0, 2.0)   # 위험 진동 범위
        },
        "pressure": {
            "normal": (100, 120),    # 정상 압력 범위
            "warning": (120, 140),   # 경고 압력 범위
            "critical": (140, 160)   # 위험 압력 범위
        }
    }
    
    # 현재 시간 기준으로 시계열 데이터 생성
    current_time = datetime.now()
    data_points = []
    
    for i in range(10):  # 최근 10개 데이터 포인트
        timestamp = current_time - timedelta(minutes=i*5)
        
        # 정상 상태 (80% 확률)
        if random.random() < 0.8:
            temp = random.uniform(*sensor_data["temperature"]["normal"])
            vib = random.uniform(*sensor_data["vibration"]["normal"])
            press = random.uniform(*sensor_data["pressure"]["normal"])
            status = "normal"
        else:
            # 이상 상태 (20% 확률)
            if random.random() < 0.7:  # 경고 상태
                temp = random.uniform(*sensor_data["temperature"]["warning"])
                vib = random.uniform(*sensor_data["vibration"]["warning"])
                press = random.uniform(*sensor_data["pressure"]["warning"])
                status = "warning"
            else:  # 위험 상태
                temp = random.uniform(*sensor_data["temperature"]["critical"])
                vib = random.uniform(*sensor_data["vibration"]["critical"])
                press = random.uniform(*sensor_data["pressure"]["critical"])
                status = "critical"
        
        data_point = {
            "timestamp": timestamp,
            "temperature": round(temp, 2),
            "vibration": round(vib, 3),
            "pressure": round(press, 1),
            "status": status
        }
        data_points.append(data_point)
    
    # 최신 데이터가 맨 앞에 오도록 역순 정렬
    data_points.reverse()
    
    print("   📈 생성된 센서 데이터:")
    for i, data in enumerate(data_points):
        status_emoji = {"normal": "🟢", "warning": "🟡", "critical": "🔴"}
        print(f"      {i+1:2d}. {data['timestamp'].strftime('%H:%M:%S')} | "
              f"온도: {data['temperature']:5.1f}°C | "
              f"진동: {data['vibration']:5.3f} | "
              f"압력: {data['pressure']:5.1f} | "
              f"{status_emoji[data['status']]} {data['status']}")
    
    print()
    return data_points


def test_ml_integration(sensor_data):
    """ML 모델 연동 테스트"""
    print("🤖 ML 모델 연동 테스트...")
    print()
    
    if not ML_AVAILABLE:
        print("   ⚠️  ML 모델이 로드되지 않았습니다.")
        print("   📝 models/ 디렉토리에 .pkl 파일을 추가한 후 다시 시도해주세요.")
        print()
        return None, None
    
    try:
        # 이상 탐지 모델 테스트
        print("   🔍 이상 탐지 모델 테스트...")
        anomaly_detector = AnomalyDetector()
        
        # 최신 센서 데이터로 이상 탐지
        latest_data = sensor_data[-1]
        anomaly_score = anomaly_detector.detect_anomaly(latest_data)
        
        print(f"      최신 데이터: {latest_data}")
        print(f"      이상 점수: {anomaly_score:.3f}")
        
        if anomaly_score > 0.8:
            print("      🚨 이상 탐지됨!")
            anomaly_detected = True
        else:
            print("      ✅ 정상 상태")
            anomaly_detected = False
        
        # RUL 예측 모델 테스트
        print("   ⏰ 잔여 수명 예측 모델 테스트...")
        rul_predictor = RULPredictor()
        
        # 시계열 데이터로 RUL 예측
        rul_prediction = rul_predictor.predict_rul(sensor_data)
        
        print(f"      예측 잔여 수명: {rul_prediction:.1f} 시간")
        
        if rul_prediction < 24:
            print("      ⚠️  유지보수 필요!")
            maintenance_needed = True
        else:
            print("      ✅ 정상 운영 가능")
            maintenance_needed = False
        
        print()
        return anomaly_detected, maintenance_needed
        
    except Exception as e:
        print(f"   ❌ ML 모델 테스트 중 오류: {e}")
        print()
        return None, None


def create_ml_notification(anomaly_detected, maintenance_needed, sensor_data):
    """ML 결과 기반 알림 생성"""
    if not anomaly_detected and not maintenance_needed:
        print("   ✅ 모든 상태가 정상입니다. 알림이 필요하지 않습니다.")
        return None
    
    latest_data = sensor_data[-1]
    
    if anomaly_detected:
        # 이상 탐지 알림
        notification = Notification(
            id=999,
            device_id="ML-TEST-EQ-001",
            sensor_id="AI-ANOMALY",
            alert_type="anomaly",
            anomaly_type="ml_detected_anomaly",
            severity="high" if latest_data["status"] == "critical" else "medium",
            message=f"AI 모델이 이상을 탐지했습니다. 센서 상태: {latest_data['status']}",
            sensor_value=str(latest_data["temperature"]),
            threshold_value="75.0",
            detected_at=datetime.now(),
            created_at=datetime.now()
        )
    else:
        # 유지보수 알림
        notification = Notification(
            id=999,
            device_id="ML-TEST-EQ-001",
            sensor_id="AI-RUL",
            alert_type="maintenance",
            anomaly_type="maintenance_required",
            severity="medium",
            message="AI 모델이 유지보수를 권장합니다.",
            sensor_value="N/A",
            threshold_value="24.0",
            detected_at=datetime.now(),
            created_at=datetime.now()
        )
    
    return notification


def test_advanced_integration():
    """고급 통합 테스트 - ML 모델 + 알림"""
    print("🚀 KSEB Factory 고급 통합 테스트 (ML + 알림)")
    print("=" * 70)
    
    # 1. ML 모델 상태 확인
    ml_available = check_ml_models()
    
    # 2. 센서 데이터 시뮬레이션
    sensor_data = generate_sensor_data()
    
    # 3. ML 모델 연동 테스트
    anomaly_detected, maintenance_needed = test_ml_integration(sensor_data)
    
    # 4. ML 결과 기반 알림 생성
    if anomaly_detected or maintenance_needed:
        ml_notification = create_ml_notification(anomaly_detected, maintenance_needed, sensor_data)
        
        if ml_notification:
            print("📱 ML 기반 알림 전송...")
            
            # 슬랙 알림
            try:
                slack_success = slack_bot_service.send_direct_message(ml_notification)
                if slack_success:
                    print("   ✅ 슬랙 ML 알림 전송 성공!")
                else:
                    print("   ❌ 슬랙 ML 알림 전송 실패")
            except Exception as e:
                print(f"   ❌ 슬랙 ML 알림 전송 중 오류: {e}")
            
            # 이메일 알림
            try:
                notification_service.send_email_notification(ml_notification)
                print("   ✅ 이메일 ML 알림 전송 성공!")
            except Exception as e:
                print(f"   ❌ 이메일 ML 알림 전송 중 오류: {e}")
    
    print()
    print("=" * 70)
    print("🎉 고급 통합 테스트 완료!")
    print()
    if ml_available:
        print("🤖 ML 모델 연동 상태:")
        print("   - 이상 탐지: ✅ 준비됨")
        print("   - RUL 예측: ✅ 준비됨")
        print("   - 자동 알림: ✅ 준비됨")
    else:
        print("🤖 ML 모델 연동 상태:")
        print("   - 모델 파일: ❌ 필요")
        print("   - 자동 알림: ⚠️  제한적")
    
    print()
    print("📝 다음 단계:")
    print("   1. models/ 디렉토리에 .pkl 파일 추가")
    print("   2. ML 모델 클래스 구현 (anomaly_detection.py, rul_prediction.py)")
    print("   3. 실제 센서 데이터 연동")
    print("   4. 자동화된 모니터링 시스템 구축")


if __name__ == "__main__":
    print("🔧 KSEB Factory 테스트 모드 선택:")
    print("1. 기본 알림 테스트 (슬랙 + 이메일)")
    print("2. 고급 통합 테스트 (ML + 알림)")
    print()
    
    try:
        choice = input("선택하세요 (1 또는 2): ").strip()
        
        if choice == "2":
            # 고급 통합 테스트
            test_advanced_integration()
        else:
            # 기본 알림 테스트
            check_notification_settings()
            test_integrated_notifications()
            
    except KeyboardInterrupt:
        print("\n\n👋 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")
        print("기본 알림 테스트를 실행합니다...")
        check_notification_settings()
        test_integrated_notifications()
