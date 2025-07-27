import json
import asyncio
import os
from typing import Dict, Any
from datetime import datetime

import paho.mqtt.client as mqtt
from kafka import KafkaProducer
from loguru import logger


class DataCollector:
    def __init__(self):
        # MQTT 설정
        self.mqtt_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        self.mqtt_client = mqtt.Client()
        
        # Kafka 설정
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.kafka_producer = None
        
        # 토픽 설정
        self.sensor_topic = "factory/sensors/+/data"  # MQTT 토픽 패턴
        self.kafka_raw_topic = "sensor-data-raw"      # Kafka 원본 데이터 토픽
        self.kafka_processed_topic = "sensor-data-processed"  # Kafka 처리된 데이터 토픽
        
        self.running = False
        
    def init_kafka_producer(self):
        """Kafka Producer 초기화"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.kafka_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Kafka Producer 연결 성공: {self.kafka_servers}")
        except Exception as e:
            logger.error(f"Kafka Producer 연결 실패: {e}")
            raise
            
    def init_mqtt_client(self):
        """MQTT 클라이언트 초기화"""
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info(f"MQTT 브로커 연결 성공: {self.mqtt_host}:{self.mqtt_port}")
                client.subscribe(self.sensor_topic)
                logger.info(f"MQTT 토픽 구독: {self.sensor_topic}")
            else:
                logger.error(f"MQTT 브로커 연결 실패. 코드: {rc}")
                
        def on_message(client, userdata, msg):
            try:
                self.process_mqtt_message(msg.topic, msg.payload.decode('utf-8'))
            except Exception as e:
                logger.error(f"MQTT 메시지 처리 중 오류: {e}")
                
        def on_disconnect(client, userdata, rc):
            logger.warning(f"MQTT 브로커 연결 끊김. 코드: {rc}")
            
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message  
        self.mqtt_client.on_disconnect = on_disconnect
        
    def process_mqtt_message(self, topic: str, payload: str):
        """MQTT 메시지 처리 및 Kafka로 전송"""
        try:
            # 토픽에서 센서 ID 추출 (factory/sensors/SENSOR_ID/data)
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3:
                sensor_id = topic_parts[2]
            else:
                logger.warning(f"잘못된 토픽 형식: {topic}")
                return
                
            # JSON 데이터 파싱
            sensor_data = json.loads(payload)
            
            # 데이터 검증 및 보강
            enriched_data = self.enrich_sensor_data(sensor_id, sensor_data)
            
            # Kafka로 원본 데이터 전송
            self.send_to_kafka(self.kafka_raw_topic, sensor_id, enriched_data)
            
            # 데이터 전처리 후 처리된 데이터 토픽으로 전송
            processed_data = self.preprocess_sensor_data(enriched_data)
            self.send_to_kafka(self.kafka_processed_topic, sensor_id, processed_data)
            
            logger.debug(f"센서 데이터 처리 완료: {sensor_id}")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}, payload: {payload}")
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {e}")
            
    def enrich_sensor_data(self, sensor_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """센서 데이터 보강"""
        current_time = datetime.utcnow()
        
        enriched = {
            'sensor_id': sensor_id,
            'timestamp': current_time.isoformat(),
            'received_at': current_time.timestamp(),
            'data': data,
            'quality': 100,  # 기본 품질 점수
            'source': 'mqtt_collector'
        }
        
        # 데이터 품질 검증
        if self.validate_sensor_data(data):
            enriched['quality'] = 100
        else:
            enriched['quality'] = 50
            logger.warning(f"센서 데이터 품질 저하: {sensor_id}")
            
        return enriched
        
    def validate_sensor_data(self, data: Dict[str, Any]) -> bool:
        """센서 데이터 유효성 검증"""
        try:
            # 필수 필드 확인
            if 'value' not in data:
                return False
                
            value = data['value']
            
            # 숫자 값 확인
            if not isinstance(value, (int, float)):
                return False
                
            # 범위 확인 (센서별 설정 필요)
            if value < -1000 or value > 10000:  # 기본 범위
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"데이터 검증 중 오류: {e}")
            return False
            
    def preprocess_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """센서 데이터 전처리"""
        processed = data.copy()
        
        try:
            sensor_value = data['data']['value']
            
            # 이동평균 계산 (간단한 예제)
            processed['moving_avg'] = sensor_value  # 실제로는 윈도우 기반 계산 필요
            
            # 이상치 감지를 위한 Z-score 계산 (간단한 예제)
            processed['z_score'] = 0.0  # 실제로는 통계 기반 계산 필요
            
            # 장비 ID 매핑
            equipment_mapping = {
                'TEMP_A001': 1, 'PRES_A001': 1, 'VIB_A001': 1,
                'TEMP_M001': 2, 'CURR_M001': 2, 'RPM_M001': 2,
                'FLOW_P001': 3, 'PRES_P001': 3,
                'POS_V001': 4,
                'SPEED_C001': 5
            }
            
            processed['equipment_id'] = equipment_mapping.get(data['sensor_id'], 0)
            
        except Exception as e:
            logger.error(f"데이터 전처리 중 오류: {e}")
            
        return processed
        
    def send_to_kafka(self, topic: str, key: str, data: Dict[str, Any]):
        """Kafka로 데이터 전송"""
        try:
            future = self.kafka_producer.send(topic, key=key, value=data)
            # 비동기 전송 완료 확인 (선택사항)
            # record_metadata = future.get(timeout=10)
            # logger.debug(f"메시지 전송 완료: {topic}, 파티션: {record_metadata.partition}")
            
        except Exception as e:
            logger.error(f"Kafka 전송 오류: {e}")
            
    async def start(self):
        """데이터 수집기 시작"""
        logger.info("스마트팩토리 데이터 수집기 시작")
        
        try:
            # Kafka Producer 초기화
            self.init_kafka_producer()
            
            # MQTT 클라이언트 초기화
            self.init_mqtt_client()
            
            # MQTT 브로커 연결
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            
            # MQTT 클라이언트 루프 시작
            self.mqtt_client.loop_start()
            
            self.running = True
            logger.info("데이터 수집기가 정상적으로 시작되었습니다")
            
            # 메인 루프
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단되었습니다")
        except Exception as e:
            logger.error(f"데이터 수집기 실행 중 오류: {e}")
        finally:
            await self.stop()
            
    async def stop(self):
        """데이터 수집기 중지"""
        logger.info("데이터 수집기 중지 중...")
        
        self.running = False
        
        if hasattr(self, 'mqtt_client'):
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT 클라이언트 연결 해제")
            
        if self.kafka_producer:
            self.kafka_producer.flush()
            self.kafka_producer.close()
            logger.info("Kafka Producer 연결 해제")
            
        logger.info("데이터 수집기가 정상적으로 중지되었습니다")


async def main():
    """메인 함수"""
    collector = DataCollector()
    try:
        await collector.start()
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 치명적 오류: {e}")
    finally:
        await collector.stop()


if __name__ == "__main__":
    # 로깅 설정
    logger.add("logs/data_collector.log", rotation="1 day", retention="7 days")
    
    # 이벤트 루프 실행
    asyncio.run(main()) 