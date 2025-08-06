"""
API 테스트 코드
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    assert "예지보전 시스템" in response.json()["message"]


def test_health():
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_device():
    """장비 생성 테스트"""
    device_data = {
        "id": "test_device_001",
        "name": "테스트 장비 1",
        "type": "motor",
        "location": "공장 A",
        "status": "active"
    }
    
    response = client.post("/api/v1/devices/", json=device_data)
    assert response.status_code == 200
    assert response.json()["id"] == "test_device_001"


def test_get_device():
    """장비 조회 테스트"""
    response = client.get("/api/v1/devices/test_device_001")
    assert response.status_code == 200
    assert response.json()["id"] == "test_device_001"


def test_save_sensor_data():
    """센서 데이터 저장 테스트"""
    sensor_data = {
        "device_id": "test_device_001",
        "sensor_type": "vibration",
        "value": 5.2,
        "unit": "m/s²",
        "time": "2024-01-01T12:00:00Z"
    }
    
    response = client.post("/api/v1/sensors/data", json=sensor_data)
    assert response.status_code == 200


def test_anomaly_detection():
    """이상 탐지 테스트"""
    anomaly_request = {
        "device_id": "test_device_001",
        "sensor_data": [
            {
                "vibration": {"value": 5.2},
                "temperature": {"value": 45.0},
                "current": {"value": 10.5}
            }
        ],
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    response = client.post("/api/v1/anomalies/detect", json=anomaly_request)
    assert response.status_code == 200
    assert "device_id" in response.json()


def test_rul_prediction():
    """RUL 예측 테스트"""
    rul_request = {
        "device_id": "test_device_001",
        "sensor_data": [
            {
                "vibration": {"value": 5.2},
                "temperature": {"value": 45.0},
                "current": {"value": 10.5}
            }
        ],
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    response = client.post("/api/v1/rul/predict", json=rul_request)
    assert response.status_code == 200
    assert "device_id" in response.json() 