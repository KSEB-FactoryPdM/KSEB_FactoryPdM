"""
pytest 설정 파일
"""
import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings


# 테스트용 데이터베이스 URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# 테스트용 엔진 생성
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 테스트용 세션 팩토리
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """테스트용 데이터베이스 세션 오버라이드"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 설정"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """테스트 데이터베이스 설정"""
    # 테스트 데이터베이스 테이블 생성
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    # 테스트 데이터베이스 정리
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_db):
    """데이터베이스 세션"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator:
    """테스트 클라이언트"""
    app.dependency_overrides[get_db] = lambda: db_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """인증 헤더"""
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def admin_headers():
    """관리자 인증 헤더"""
    return {"Authorization": "Bearer admin_test_token"}


@pytest.fixture
def sample_device_data():
    """샘플 장비 데이터"""
    return {
        "id": "test_device_001",
        "name": "테스트 장비 1",
        "type": "motor",
        "location": "공장 A",
        "status": "active",
        "manufacturer": "테스트 제조사",
        "model": "TEST-001",
        "installation_date": "2023-01-01",
        "last_maintenance": "2023-12-01"
    }


@pytest.fixture
def sample_sensor_data():
    """샘플 센서 데이터"""
    return {
        "device_id": "test_device_001",
        "sensor_type": "vibration",
        "value": 0.5,
        "unit": "g",
        "time": "2023-12-01T10:00:00Z"
    }


@pytest.fixture
def sample_anomaly_data():
    """샘플 이상 탐지 데이터"""
    return {
        "device_id": "test_device_001",
        "sensor_data": {
            "vibration": {"value": 0.8, "unit": "g"},
            "temperature": {"value": 75.0, "unit": "°C"},
            "current": {"value": 15.5, "unit": "A"}
        },
        "timestamp": "2023-12-01T10:00:00Z"
    }


@pytest.fixture
def sample_rul_data():
    """샘플 RUL 예측 데이터"""
    return {
        "device_id": "test_device_001",
        "sensor_history": [
            {
                "vibration": {"value": 0.3, "unit": "g"},
                "temperature": {"value": 65.0, "unit": "°C"},
                "current": {"value": 12.0, "unit": "A"},
                "timestamp": "2023-12-01T09:00:00Z"
            },
            {
                "vibration": {"value": 0.4, "unit": "g"},
                "temperature": {"value": 68.0, "unit": "°C"},
                "current": {"value": 13.0, "unit": "A"},
                "timestamp": "2023-12-01T09:30:00Z"
            },
            {
                "vibration": {"value": 0.5, "unit": "g"},
                "temperature": {"value": 70.0, "unit": "°C"},
                "current": {"value": 14.0, "unit": "A"},
                "timestamp": "2023-12-01T10:00:00Z"
            }
        ]
    }


@pytest.fixture
def sample_user_data():
    """샘플 사용자 데이터"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "테스트 사용자",
        "role": "viewer"
    }


@pytest.fixture
def sample_admin_user_data():
    """샘플 관리자 사용자 데이터"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpass123",
        "full_name": "관리자",
        "role": "admin"
    }


# 테스트 설정
def pytest_configure(config):
    """pytest 설정"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """테스트 아이템 수정"""
    for item in items:
        if "test_ml_api" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_sensor_data" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_anomaly_detection" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit) 