"""
Prometheus 모니터링 설정
"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# 메트릭 정의
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

SENSOR_DATA_COUNT = Counter(
    'sensor_data_total',
    'Total sensor data points received',
    ['device_id', 'sensor_type']
)

ANOMALY_DETECTION_COUNT = Counter(
    'anomaly_detection_total',
    'Total anomaly detections',
    ['device_id', 'severity']
)

RUL_PREDICTION_COUNT = Counter(
    'rul_prediction_total',
    'Total RUL predictions',
    ['device_id']
)

ACTIVE_DEVICES = Gauge(
    'active_devices',
    'Number of active devices'
)

MODEL_PREDICTION_DURATION = Histogram(
    'model_prediction_duration_seconds',
    'ML model prediction duration in seconds',
    ['model_type']
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']
)

MODEL_TRAINING_COUNT = Counter(
    'model_training_total',
    'Total model training attempts',
    ['device_id', 'training_type', 'success']
)


def setup_monitoring():
    """모니터링 서버 시작"""
    try:
        start_http_server(settings.PROMETHEUS_PORT)
        logger.info(f"Prometheus 메트릭 서버가 포트 {settings.PROMETHEUS_PORT}에서 시작되었습니다")
    except Exception as e:
        logger.error(f"모니터링 서버 시작 실패: {e}")


def record_request_metrics(method: str, endpoint: str, status: int, duration: float):
    """HTTP 요청 메트릭 기록"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def record_sensor_data(device_id: str, sensor_type: str):
    """센서 데이터 메트릭 기록"""
    SENSOR_DATA_COUNT.labels(device_id=device_id, sensor_type=sensor_type).inc()


def record_anomaly_detection(device_id: str, severity: str):
    """이상 탐지 메트릭 기록"""
    ANOMALY_DETECTION_COUNT.labels(device_id=device_id, severity=severity).inc()


def record_rul_prediction(device_id: str):
    """RUL 예측 메트릭 기록"""
    RUL_PREDICTION_COUNT.labels(device_id=device_id).inc()


def update_active_devices(count: int):
    """활성 장비 수 업데이트"""
    ACTIVE_DEVICES.set(count)


def record_model_prediction(model_type: str, duration: float):
    """모델 예측 시간 메트릭 기록"""
    MODEL_PREDICTION_DURATION.labels(model_type=model_type).observe(duration)


def record_database_query(operation: str, duration: float):
    """데이터베이스 쿼리 시간 메트릭 기록"""
    DATABASE_QUERY_DURATION.labels(operation=operation).observe(duration)


def record_model_training(device_id: str, training_type: str, success: bool):
    """모델 학습 메트릭 기록"""
    success_str = "success" if success else "failure"
    MODEL_TRAINING_COUNT.labels(device_id=device_id, training_type=training_type, success=success_str).inc() 