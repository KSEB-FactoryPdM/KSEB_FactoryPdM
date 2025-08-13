"""
Kafka → TimescaleDB 싱크 서비스

sensor-data-raw 토픽의 메시지(원본 Unity 포맷)를 TimescaleDB의 sensor_data 하이퍼테이블로 저장.
"""

import json
import os
import time
from urllib.parse import urlparse, urlunparse
from datetime import datetime
from typing import Dict, Any

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from loguru import logger
from sqlalchemy import text, create_engine


class KafkaTimescaleSink:
    def __init__(self):
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = os.getenv('KAFKA_SENSOR_RAW_TOPIC', 'sensor-data-raw')
        self.group_id = os.getenv('KAFKA_SINK_GROUP_ID', 'kafka_timescale_sink')
        # 기본값은 로컬 개발 환경을 고려해 localhost로 설정
        self.timescale_url = os.getenv('TIMESCALE_URL', 'postgresql://user:password@localhost:5432/predictive_maintenance')
        self.engine = None
        self._init_timescale_engine_with_retry()

    def _init_timescale_engine_with_retry(self, retries: int = 30, delay_sec: float = 2.0):
        last_err = None
        for i in range(retries):
            try:
                self.engine = create_engine(self.timescale_url)
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    # 스키마 보장: 테이블/하이퍼테이블 없으면 생성
                    self._ensure_schema(conn)
                logger.info("TimescaleDB 연결 성공")
                return
            except Exception as e:
                last_err = e
                # 컨테이너 호스트명(timescaledb) 해석 실패 시 localhost로 폴백
                err_msg = str(e)
                if (
                    ("could not translate host name" in err_msg or "Name or service not known" in err_msg)
                    and ("timescaledb" in self.timescale_url)
                ):
                    parsed = urlparse(self.timescale_url)
                    hostname = parsed.hostname or ""
                    if hostname.startswith("timescaledb"):
                        userinfo = ""
                        if parsed.username:
                            userinfo += parsed.username
                            if parsed.password:
                                userinfo += f":{parsed.password}"
                            userinfo += "@"
                        hostport = "localhost"
                        if parsed.port:
                            hostport += f":{parsed.port}"
                        new_netloc = f"{userinfo}{hostport}"
                        new_url = urlunparse(parsed._replace(netloc=new_netloc))
                        logger.warning(f"Timescale 호스트명 해석 실패. URL을 localhost로 폴백: {self.timescale_url} → {new_url}")
                        self.timescale_url = new_url
                        # 다음 루프에서 폴백 URL로 재시도
                        time.sleep(delay_sec)
                        continue
                logger.warning(f"TimescaleDB 연결 재시도 {i+1}/{retries}: {e}")
                time.sleep(delay_sec)
        logger.error(f"TimescaleDB 연결 실패: {last_err}")
        raise last_err

    def _ensure_schema(self, conn):
        try:
            # 확장 설치 및 테이블 생성, 하이퍼테이블 변환, 인덱스 생성
            conn.execute(text("""
                CREATE EXTENSION IF NOT EXISTS timescaledb;
                CREATE TABLE IF NOT EXISTS sensor_data (
                    time TIMESTAMPTZ NOT NULL,
                    device TEXT NOT NULL,
                    device_id TEXT,
                    sensor_type TEXT NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    unit TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (time, device, sensor_type)
                );
            """))
            conn.execute(text("""
                SELECT create_hypertable('sensor_data','time', if_not_exists => TRUE);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sensor_data_device_time 
                ON sensor_data (device, time DESC);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sensor_data_device_id_time 
                ON sensor_data (device_id, time DESC);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sensor_data_device_type 
                ON sensor_data (device, sensor_type);
            """))
            # 기존 컬럼 타입을 TEXT로 변경
            conn.execute(text("""
                ALTER TABLE IF EXISTS sensor_data 
                    ALTER COLUMN device TYPE TEXT,
                    ALTER COLUMN device_id TYPE TEXT,
                    ALTER COLUMN sensor_type TYPE TEXT,
                    ALTER COLUMN unit TYPE TEXT;
            """))
            conn.commit()
        except Exception as e:
            # 스키마 보장 실패는 경고로 남기되, 이후 재시도/백엔드 초기화에 맡김
            logger.warning(f"Timescale 스키마 보장 실패(무시하고 진행): {e}")

    def save_record(self, sensor_id: str, data: Dict[str, Any]):
        try:
            device = data.get('device', sensor_id)
            timestamp = data.get('timestamp')
            sensor_values = []
            # Current: x,y,z  → sensor_type: x, y, z
            if 'x' in data:
                sensor_values.append({'time': timestamp, 'device': device, 'sensor_type': 'x', 'value': data['x'], 'unit': ''})
            if 'y' in data:
                sensor_values.append({'time': timestamp, 'device': device, 'sensor_type': 'y', 'value': data['y'], 'unit': ''})
            if 'z' in data:
                sensor_values.append({'time': timestamp, 'device': device, 'sensor_type': 'z', 'value': data['z'], 'unit': ''})
            # Vibration: vibe → sensor_type: vibe
            if 'vibe' in data:
                sensor_values.append({'time': timestamp, 'device': device, 'sensor_type': 'vibe', 'value': data['vibe'], 'unit': 'mm/s'})

            with self.engine.connect() as conn:
                query = text(
                    """
                    INSERT INTO sensor_data (time, device, device_id, sensor_type, value, unit)
                    VALUES (:time, :device, :device, :sensor_type, :value, :unit)
                    ON CONFLICT (time, device, sensor_type) DO UPDATE SET
                        value = EXCLUDED.value,
                        unit = EXCLUDED.unit
                    """
                )
                for row in sensor_values:
                    conn.execute(query, row)
                conn.commit()
        except Exception as e:
            logger.error(f"TimescaleDB 저장 실패: {e}")

    def start(self):
        logger.info("Kafka→Timescale 싱크 시작")
        consumer = None
        last_err = None
        for i in range(30):
            try:
                consumer = KafkaConsumer(
                    self.topic,
                    bootstrap_servers=self.kafka_servers.split(','),
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    group_id=self.group_id,
                    auto_offset_reset='latest',
                    request_timeout_ms=30000,
                    session_timeout_ms=15000,
                )
                logger.info(f"Kafka Consumer 연결 성공: {self.kafka_servers}, topic={self.topic}")
                break
            except NoBrokersAvailable as e:
                last_err = e
                logger.warning(f"Kafka 브로커 미가용, 재시도 {i+1}/30: {e}")
                time.sleep(2)
            except Exception as e:
                last_err = e
                logger.warning(f"Kafka Consumer 생성 실패, 재시도 {i+1}/30: {e}")
                time.sleep(2)
        if consumer is None:
            logger.error(f"Kafka Consumer 연결 실패: {last_err}")
            raise last_err

        for message in consumer:
            try:
                payload = message.value
                sensor_id = payload.get('sensor_id', 'unknown')
                data = payload.get('data', {})
                self.save_record(sensor_id, data)
            except Exception as e:
                logger.error(f"메시지 처리 오류: {e}")


def main():
    sink = KafkaTimescaleSink()
    sink.start()


if __name__ == "__main__":
    main()


