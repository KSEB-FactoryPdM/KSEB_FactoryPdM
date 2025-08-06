"""
애플리케이션 설정 관리
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    APP_NAME: str = "예지보전시스템"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")
    
    # CORS 설정
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS"
    )
    
    # 데이터베이스 설정 - 환경변수 필수
    DATABASE_URL: str = Field(env="DATABASE_URL", description="데이터베이스 연결 URL (필수)")
    TIMESCALE_URL: str = Field(env="TIMESCALE_URL", description="TimescaleDB 연결 URL (필수)")
    
    # MQTT 설정
    MQTT_BROKER_HOST: str = Field(default="localhost", env="MQTT_BROKER_HOST")
    MQTT_BROKER_PORT: int = Field(default=1883, env="MQTT_BROKER_PORT")
    MQTT_USERNAME: Optional[str] = Field(default=None, env="MQTT_USERNAME")
    MQTT_PASSWORD: Optional[str] = Field(default=None, env="MQTT_PASSWORD")
    MQTT_TOPIC_PREFIX: str = Field(default="sensors/", env="MQTT_TOPIC_PREFIX")
    
    # Kafka 설정
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    
    # Redis 설정
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # JWT 설정 - 환경변수 필수 (개발 환경에서는 기본값 제공)
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-b8f2c4e6a9d1f3e5c7a2b4d6e8f0a1c3", 
        env="SECRET_KEY", 
        description="JWT 암호화 키 (필수)"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # ML 모델 설정
    MODEL_PATH: str = Field(default="./models/", env="MODEL_PATH")
    ANOMALY_DETECTION_THRESHOLD: float = Field(
        default=0.8,
        env="ANOMALY_DETECTION_THRESHOLD"
    )
    RUL_PREDICTION_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7,
        env="RUL_PREDICTION_CONFIDENCE_THRESHOLD"
    )
    
    # 알림 설정
    EMAIL_SMTP_SERVER: str = Field(
        default="smtp.gmail.com",
        env="EMAIL_SMTP_SERVER"
    )
    EMAIL_SMTP_PORT: int = Field(default=587, env="EMAIL_SMTP_PORT")
    EMAIL_USERNAME: Optional[str] = Field(default=None, env="EMAIL_USERNAME")
    EMAIL_PASSWORD: Optional[str] = Field(default=None, env="EMAIL_PASSWORD")
    
    # 카카오 알림톡 설정
    KAKAO_API_KEY: Optional[str] = Field(default=None, env="KAKAO_API_KEY")
    KAKAO_TEMPLATE_ID: Optional[str] = Field(default=None, env="KAKAO_TEMPLATE_ID")
    
    # 모니터링 설정
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    GRAFANA_PORT: int = Field(default=3000, env="GRAFANA_PORT")
    
    # AWS 설정 (배포용) - 환경변수에서만
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="ap-northeast-2", env="AWS_REGION")
    AWS_EC2_INSTANCE_ID: Optional[str] = Field(default=None, env="AWS_EC2_INSTANCE_ID")
    
    # 성능 목표 설정
    MAX_CONCURRENT_DEVICES: int = Field(default=1000, env="MAX_CONCURRENT_DEVICES")
    MAX_SAMPLES_PER_SECOND: int = Field(default=100000, env="MAX_SAMPLES_PER_SECOND")
    ANOMALY_DETECTION_DELAY_SECONDS: int = Field(default=5, env="ANOMALY_DETECTION_DELAY_SECONDS")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 필수 환경변수 검증
        self._validate_required_settings()
    
    def _validate_required_settings(self):
        """필수 환경변수 검증"""
        required_vars = []
        
        if not self.DATABASE_URL:
            required_vars.append("DATABASE_URL")
        
        if not self.TIMESCALE_URL:
            required_vars.append("TIMESCALE_URL")
            
        # SECRET_KEY는 기본값이 있으므로 검증에서 제외 (개발 환경 지원)
        # 프로덕션에서는 반드시 환경변수로 설정해야 함
        if self.SECRET_KEY == "dev-secret-key-change-in-production-b8f2c4e6a9d1f3e5c7a2b4d6e8f0a1c3" and self.ENVIRONMENT == "production":
            required_vars.append("SECRET_KEY (프로덕션 환경에서는 필수)")
        
        if required_vars:
            raise ValueError(
                f"다음 환경변수들이 설정되지 않았습니다: {', '.join(required_vars)}\n"
                "이러한 환경변수들은 보안상 중요하므로 반드시 .env 파일이나 시스템 환경변수에 설정해주세요."
            )


# 전역 설정 인스턴스
settings = Settings()