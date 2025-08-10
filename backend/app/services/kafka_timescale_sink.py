"""
Kafka → TimescaleDB 싱크 서비스

sensor-data-raw 토픽의 메시지(원본 Unity 포맷)를 TimescaleDB의 sensor_data 하이퍼테이블로 저장.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

from kafka import KafkaConsumer
from loguru import logger
from sqlalchemy import text, create_engine


class KafkaTimescaleSink:
    def __init__(self):
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = os.getenv('KAFKA_SENSOR_RAW_TOPIC', 'sensor-data-raw')
        timescale_url = os.getenv('TIMESCALE_URL', 'postgresql://user:password@timescaledb:5432/predictive_maintenance')
        self.engine = create_engine(timescale_url)

    def save_record(self, sensor_id: str, data: Dict[str, Any]):
        try:
            device = data.get('device', sensor_id)
            timestamp = data.get('timestamp')
            sensor_values = []
            if 'x' in data:
                sensor_values.append({'time': timestamp, 'device': device, 'sensor_type': 'temperature', 'value': data['x'], 'unit': 'celsius'})
            if 'y' in data:
                sensor_values.append({'time': timestamp, 'device': device, 'sensor_type': 'pressure', 'value': data['y'], 'unit': 'bar'})
            if 'z' in data:
                sensor_values.append({'time': timestamp, 'device': device, 'sensor_type': 'vibration', 'value': data['z'], 'unit': 'mm/s'})

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
        consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.kafka_servers.split(','),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='kafka_timescale_sink',
            auto_offset_reset='latest'
        )
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


