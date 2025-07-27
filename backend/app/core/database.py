"""
데이터베이스 연결 및 초기화 관리
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy 설정
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스
Base = declarative_base()

# 메타데이터
metadata = MetaData()


def get_db() -> Generator:
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """데이터베이스 초기화"""
    try:
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
        
        # TimescaleDB 하이퍼테이블 생성
        await create_timescale_tables()
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise


async def create_timescale_tables():
    """TimescaleDB 하이퍼테이블 생성"""
    try:
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # 센서 데이터 하이퍼테이블 생성
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    time TIMESTAMPTZ NOT NULL,
                    device_id VARCHAR(50) NOT NULL,
                    sensor_type VARCHAR(20) NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    unit VARCHAR(10),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            
            # 하이퍼테이블로 변환
            conn.execute(text("""
                SELECT create_hypertable('sensor_data', 'time', 
                    if_not_exists => TRUE);
            """))
            
            # 인덱스 생성
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sensor_data_device_time 
                ON sensor_data (device_id, time DESC);
            """))
            
            # 이상 이벤트 테이블
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS anomaly_events (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(50) NOT NULL,
                    event_time TIMESTAMPTZ NOT NULL,
                    anomaly_score DOUBLE PRECISION NOT NULL,
                    anomaly_type VARCHAR(50),
                    severity VARCHAR(20),
                    description TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            
            # RUL 예측 결과 테이블
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS rul_predictions (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(50) NOT NULL,
                    prediction_time TIMESTAMPTZ NOT NULL,
                    rul_value DOUBLE PRECISION NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL,
                    uncertainty DOUBLE PRECISION,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            
            # 장비 정보 테이블
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS devices (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(50),
                    location VARCHAR(100),
                    installation_date DATE,
                    last_maintenance_date DATE,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))
            
            conn.commit()
            logger.info("TimescaleDB 하이퍼테이블 생성 완료")
            
    except Exception as e:
        logger.error(f"TimescaleDB 테이블 생성 실패: {e}")
        raise


def get_timescale_engine():
    """TimescaleDB 전용 엔진 반환"""
    return create_engine(
        settings.TIMESCALE_URL,
        poolclass=StaticPool,
        pool_pre_ping=True,
        echo=settings.DEBUG
    ) 