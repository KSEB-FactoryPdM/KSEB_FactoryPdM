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
        self.sensor_topic = "unity/sensors/+/data"    # MQTT 토픽 패턴 (Unity에서 전송)
        self.kafka_raw_topic = "sensor-data-raw"      # Kafka 원본 데이터 토픽
        self.kafka_ai_topic = "ai-model-input"        # AI 모델 서비스 입력 토픽
        
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
            # 토픽에서 센서 ID 추출 (unity/sensors/SENSOR_ID/data)
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
            
            # 데이터 전처리 후 AI 모델 서비스로 전송
            processed_data = self.preprocess_sensor_data(enriched_data)
            if processed_data.get('model_ready', False):
                self.send_to_kafka(self.kafka_ai_topic, sensor_id, processed_data)
                logger.debug(f"AI 모델 입력 데이터 전송 완료: {sensor_id}")
            
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
        if self.validate_sensor_data(data, sensor_id):
            enriched['quality'] = 100
        else:
            enriched['quality'] = 50
            logger.warning(f"센서 데이터 품질 저하: {sensor_id}")
            
        return enriched
        
    def validate_sensor_data(self, data: Dict[str, Any], sensor_id: str = None) -> bool:
        """센서 데이터 유효성 검증 (Unity 데이터 구조 지원)"""
        try:
            # Unity에서 보내는 데이터 구조 확인
            # Current 데이터: {device, timestamp, x, y, z}
            # Vibration 데이터: {device, timestamp, vibe}
            
            # 필수 필드 확인
            required_fields = ['device', 'timestamp']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"필수 필드 누락: {field}")
                    return False
            
            # Current 센서 데이터 검증
            if 'x' in data and 'y' in data and 'z' in data:
                # Current 센서 (3축 데이터)
                for axis in ['x', 'y', 'z']:
                    value = data[axis]
                    if not isinstance(value, (int, float)):
                        logger.warning(f"잘못된 데이터 타입: {axis}={value}")
                        return False
                    # 기본 범위 검증 (필요시 설정값으로 변경 가능)
                    if value < -1000 or value > 1000:
                        logger.warning(f"값이 범위를 벗어남: {axis}={value}")
                        return False
                        
            # Vibration 센서 데이터 검증
            elif 'vibe' in data:
                value = data['vibe']
                if not isinstance(value, (int, float)):
                    logger.warning(f"잘못된 데이터 타입: vibe={value}")
                    return False
                # 기본 범위 검증 (필요시 설정값으로 변경 가능)
                if value < 0 or value > 1000:
                    logger.warning(f"진동 값이 범위를 벗어남: vibe={value}")
                    return False
            else:
                logger.warning("알 수 없는 데이터 구조: Current(x,y,z) 또는 Vibration(vibe) 필드가 없음")
                return False
                
            # 타임스탬프 검증
            timestamp = data['timestamp']
            if not isinstance(timestamp, (int, float, str)):
                logger.warning(f"잘못된 타임스탬프 타입: {timestamp}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"데이터 검증 중 오류: {e}")
            return False
            
    def preprocess_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """센서 데이터 전처리 (Unity 데이터 구조 지원)"""
        processed = data.copy()
        
        try:
            # Unity에서 받은 원본 데이터 구조 유지
            sensor_data = data['data']
            device_id = sensor_data.get('device', 'unknown')
            
            # 데이터 타입 분류
            if 'x' in sensor_data and 'y' in sensor_data and 'z' in sensor_data:
                # Current 센서 데이터 (3축)
                processed['sensor_type'] = 'current'
                processed['values'] = {
                    'x': sensor_data['x'],
                    'y': sensor_data['y'], 
                    'z': sensor_data['z']
                }
                # 3축 벡터 크기 계산
                import math
                magnitude = math.sqrt(sensor_data['x']**2 + sensor_data['y']**2 + sensor_data['z']**2)
                processed['magnitude'] = magnitude
                
            elif 'vibe' in sensor_data:
                # Vibration 센서 데이터
                processed['sensor_type'] = 'vibration'
                processed['values'] = {
                    'vibe': sensor_data['vibe']
                }
                processed['magnitude'] = sensor_data['vibe']
                
            else:
                logger.warning(f"알 수 없는 센서 데이터 구조: {device_id}")
                processed['sensor_type'] = 'unknown'
                processed['values'] = {}
                processed['magnitude'] = 0
            
            # Unity에서 받은 device ID를 equipment_id로 사용
            processed['equipment_id'] = device_id
            
            # AI 모델 처리를 위한 추가 메타데이터
            processed['model_ready'] = True
            processed['processing_timestamp'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"데이터 전처리 중 오류: {e}")
            processed['model_ready'] = False
            
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