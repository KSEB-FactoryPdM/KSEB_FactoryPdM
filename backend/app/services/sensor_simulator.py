import json
import asyncio
import os
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any

import paho.mqtt.client as mqtt
from loguru import logger


class SensorSimulator:
    def __init__(self):
        # MQTT 설정
        self.mqtt_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        self.mqtt_client = mqtt.Client()
        
        # 시뮬레이션 설정
        self.running = False
        self.simulation_speed = 1.0  # 실시간 배속
        self.data_interval = 1.0     # 데이터 전송 간격 (초)
        
        # 센서 정의
        self.sensors = self.define_sensors()
        
        # 이상 상황 시뮬레이션
        self.anomaly_probability = 0.05  # 5% 확률로 이상 데이터 생성
        self.equipment_status = {
            1: 'normal',  # 압축기
            2: 'normal',  # 모터  
            3: 'normal',  # 펌프
            4: 'normal',  # 밸브
            5: 'normal'   # 컨베이어
        }
        
    def define_sensors(self) -> List[Dict[str, Any]]:
        """센서 정의"""
        return [
            # 압축기 A-001 센서들
            {
                'sensor_id': 'TEMP_A001',
                'equipment_id': 1,
                'type': 'temperature',
                'unit': '°C',
                'normal_range': (20, 80),
                'warning_range': (80, 95),
                'critical_range': (95, 120),
                'base_value': 45,
                'noise_level': 2.0,
                'trend': 'stable'
            },
            {
                'sensor_id': 'PRES_A001', 
                'equipment_id': 1,
                'type': 'pressure',
                'unit': 'bar',
                'normal_range': (2, 8),
                'warning_range': (8, 9),
                'critical_range': (9, 10),
                'base_value': 5.5,
                'noise_level': 0.3,
                'trend': 'stable'
            },
            {
                'sensor_id': 'VIB_A001',
                'equipment_id': 1, 
                'type': 'vibration',
                'unit': 'mm/s',
                'normal_range': (0, 15),
                'warning_range': (15, 25),
                'critical_range': (25, 50),
                'base_value': 8,
                'noise_level': 1.5,
                'trend': 'stable'
            },
            
            # 모터 M-001 센서들
            {
                'sensor_id': 'TEMP_M001',
                'equipment_id': 2,
                'type': 'temperature', 
                'unit': '°C',
                'normal_range': (30, 90),
                'warning_range': (90, 110),
                'critical_range': (110, 130),
                'base_value': 60,
                'noise_level': 3.0,
                'trend': 'stable'
            },
            {
                'sensor_id': 'CURR_M001',
                'equipment_id': 2,
                'type': 'current',
                'unit': 'A', 
                'normal_range': (10, 80),
                'warning_range': (80, 90),
                'critical_range': (90, 100),
                'base_value': 45,
                'noise_level': 2.5,
                'trend': 'stable'
            },
            {
                'sensor_id': 'RPM_M001',
                'equipment_id': 2,
                'type': 'rpm',
                'unit': 'rpm',
                'normal_range': (1000, 2800),
                'warning_range': (2800, 2950),
                'critical_range': (2950, 3000),
                'base_value': 1800,
                'noise_level': 50,
                'trend': 'stable'
            },
            
            # 펌프 P-001 센서들
            {
                'sensor_id': 'FLOW_P001',
                'equipment_id': 3,
                'type': 'flow_rate',
                'unit': 'L/min',
                'normal_range': (100, 800),
                'warning_range': (800, 900),
                'critical_range': (900, 1000),
                'base_value': 450,
                'noise_level': 20,
                'trend': 'stable'
            },
            {
                'sensor_id': 'PRES_P001',
                'equipment_id': 3,
                'type': 'pressure',
                'unit': 'bar',
                'normal_range': (3, 12),
                'warning_range': (12, 14),
                'critical_range': (14, 15),
                'base_value': 7.5,
                'noise_level': 0.5,
                'trend': 'stable'
            },
            
            # 밸브 V-001 센서
            {
                'sensor_id': 'POS_V001',
                'equipment_id': 4,
                'type': 'position',
                'unit': '%',
                'normal_range': (0, 100),
                'warning_range': (100, 100),
                'critical_range': (100, 100),
                'base_value': 50,
                'noise_level': 5,
                'trend': 'stable'
            },
            
            # 컨베이어 C-001 센서
            {
                'sensor_id': 'SPEED_C001',
                'equipment_id': 5,
                'type': 'speed',
                'unit': 'm/min',
                'normal_range': (10, 90),
                'warning_range': (90, 95),
                'critical_range': (95, 100),
                'base_value': 50,
                'noise_level': 3,
                'trend': 'stable'
            }
        ]
        
    def init_mqtt_client(self):
        """MQTT 클라이언트 초기화"""
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info(f"MQTT 브로커 연결 성공: {self.mqtt_host}:{self.mqtt_port}")
            else:
                logger.error(f"MQTT 브로커 연결 실패. 코드: {rc}")
                
        def on_disconnect(client, userdata, rc):
            logger.warning(f"MQTT 브로커 연결 끊김. 코드: {rc}")
            
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_disconnect = on_disconnect
        
    def generate_sensor_value(self, sensor: Dict[str, Any], timestamp: datetime) -> float:
        """센서 값 생성"""
        base_value = sensor['base_value']
        noise_level = sensor['noise_level']
        equipment_id = sensor['equipment_id']
        
        # 기본 노이즈 추가
        noise = random.gauss(0, noise_level)
        
        # 시간 기반 패턴 추가 (일일 주기, 주간 주기 등)
        hour_of_day = timestamp.hour
        day_pattern = math.sin(2 * math.pi * hour_of_day / 24) * (base_value * 0.1)
        
        # 설비 상태에 따른 값 조정
        status = self.equipment_status.get(equipment_id, 'normal')
        
        if status == 'warning':
            # 경고 상태: 값이 정상 범위 상한에 가까워짐
            base_value += base_value * 0.2
        elif status == 'critical':
            # 위험 상태: 값이 경고 범위를 벗어남
            base_value += base_value * 0.4
        elif status == 'failure':
            # 고장 상태: 불규칙한 값
            noise += random.gauss(0, noise_level * 3)
            
        # 이상치 생성 (확률적)
        if random.random() < self.anomaly_probability:
            anomaly_factor = random.choice([-1, 1]) * random.uniform(0.3, 0.8)
            base_value += base_value * anomaly_factor
            logger.debug(f"이상치 생성: {sensor['sensor_id']}, factor: {anomaly_factor}")
            
        value = base_value + noise + day_pattern
        
        # 최소/최대 값 제한
        min_val = min(sensor['normal_range'][0], sensor['warning_range'][0], sensor['critical_range'][0])
        max_val = max(sensor['normal_range'][1], sensor['warning_range'][1], sensor['critical_range'][1])
        
        return max(min_val * 0.8, min(value, max_val * 1.2))
        
    def create_sensor_data(self, sensor: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
        """센서 데이터 생성"""
        value = self.generate_sensor_value(sensor, timestamp)
        
        # 상태 판정
        status = 'normal'
        if value >= sensor['critical_range'][0]:
            status = 'critical'
        elif value >= sensor['warning_range'][0]:
            status = 'warning'
            
        return {
            'value': round(value, 2),
            'unit': sensor['unit'],
            'type': sensor['type'],
            'status': status,
            'timestamp': timestamp.isoformat(),
            'equipment_id': sensor['equipment_id'],
            'quality': random.randint(95, 100),  # 데이터 품질
            'source': 'simulator'
        }
        
    def publish_sensor_data(self, sensor_id: str, data: Dict[str, Any]):
        """MQTT로 센서 데이터 발행"""
        topic = f"factory/sensors/{sensor_id}/data"
        payload = json.dumps(data)
        
        try:
            result = self.mqtt_client.publish(topic, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"센서 데이터 발행: {sensor_id} -> {data['value']}")
            else:
                logger.error(f"MQTT 발행 실패: {sensor_id}, 코드: {result.rc}")
        except Exception as e:
            logger.error(f"MQTT 발행 중 오류: {e}")
            
    def simulate_equipment_degradation(self):
        """설비 열화 시뮬레이션"""
        # 무작위로 설비 상태 변경 (낮은 확률)
        for equipment_id in self.equipment_status:
            change_probability = 0.01  # 1% 확률
            
            if random.random() < change_probability:
                current_status = self.equipment_status[equipment_id]
                
                if current_status == 'normal':
                    # 정상 -> 경고 (5% 확률)
                    if random.random() < 0.05:
                        self.equipment_status[equipment_id] = 'warning'
                        logger.info(f"설비 {equipment_id} 상태 변경: normal -> warning")
                        
                elif current_status == 'warning':
                    # 경고 -> 위험 (10% 확률) 또는 경고 -> 정상 (70% 확률)
                    if random.random() < 0.1:
                        self.equipment_status[equipment_id] = 'critical'
                        logger.warning(f"설비 {equipment_id} 상태 변경: warning -> critical")
                    elif random.random() < 0.7:
                        self.equipment_status[equipment_id] = 'normal'
                        logger.info(f"설비 {equipment_id} 상태 변경: warning -> normal")
                        
                elif current_status == 'critical':
                    # 위험 -> 고장 (15% 확률) 또는 위험 -> 경고 (50% 확률)
                    if random.random() < 0.15:
                        self.equipment_status[equipment_id] = 'failure'
                        logger.error(f"설비 {equipment_id} 상태 변경: critical -> failure")
                    elif random.random() < 0.5:
                        self.equipment_status[equipment_id] = 'warning'
                        logger.info(f"설비 {equipment_id} 상태 변경: critical -> warning")
                        
                elif current_status == 'failure':
                    # 고장 -> 정상 (유지보수 완료, 30% 확률)
                    if random.random() < 0.3:
                        self.equipment_status[equipment_id] = 'normal'
                        logger.info(f"설비 {equipment_id} 유지보수 완료: failure -> normal")
                        
    async def start(self):
        """센서 시뮬레이터 시작"""
        logger.info("스마트팩토리 센서 시뮬레이터 시작")
        
        try:
            # MQTT 클라이언트 초기화
            self.init_mqtt_client()
            
            # MQTT 브로커 연결
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            self.running = True
            logger.info(f"센서 시뮬레이터가 정상적으로 시작되었습니다 (센서 수: {len(self.sensors)})")
            
            simulation_step = 0
            
            # 메인 시뮬레이션 루프
            while self.running:
                current_time = datetime.utcnow()
                
                # 모든 센서 데이터 생성 및 전송
                for sensor in self.sensors:
                    sensor_data = self.create_sensor_data(sensor, current_time)
                    self.publish_sensor_data(sensor['sensor_id'], sensor_data)
                    
                # 설비 열화 시뮬레이션 (매 10초마다)
                if simulation_step % 10 == 0:
                    self.simulate_equipment_degradation()
                    
                # 상태 로깅 (매 60초마다)
                if simulation_step % 60 == 0:
                    active_sensors = len(self.sensors)
                    logger.info(f"시뮬레이션 진행 중 - 활성 센서: {active_sensors}, 설비 상태: {self.equipment_status}")
                    
                simulation_step += 1
                
                # 다음 사이클까지 대기
                await asyncio.sleep(self.data_interval / self.simulation_speed)
                
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단되었습니다")
        except Exception as e:
            logger.error(f"시뮬레이터 실행 중 오류: {e}")
        finally:
            await self.stop()
            
    async def stop(self):
        """센서 시뮬레이터 중지"""
        logger.info("센서 시뮬레이터 중지 중...")
        
        self.running = False
        
        if hasattr(self, 'mqtt_client'):
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("MQTT 클라이언트 연결 해제")
            
        logger.info("센서 시뮬레이터가 정상적으로 중지되었습니다")


async def main():
    """메인 함수"""
    simulator = SensorSimulator()
    try:
        await simulator.start()
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 치명적 오류: {e}")
    finally:
        await simulator.stop()


if __name__ == "__main__":
    # 로깅 설정
    logger.add("logs/sensor_simulator.log", rotation="1 day", retention="7 days")
    
    # 이벤트 루프 실행
    asyncio.run(main()) 