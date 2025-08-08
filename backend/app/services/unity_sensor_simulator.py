"""
Unity 센서 시뮬레이터 모방 MQTT 클라이언트
실제 Unity에서 센서 데이터를 전송하는 것처럼 보이게 하는 Python 시뮬레이터
"""

import paho.mqtt.client as mqtt
import json
import time
import os
import random
import logging
from datetime import datetime
from typing import Dict, Any, List
import asyncio
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnitySensorSimulator:
    """Unity 센서 시뮬레이터를 모방하는 클래스"""
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect
        
        # 센서 데이터 파일 경로
        self.data_dir = Path(__file__).parent.parent / "metadata"
        
        # 시뮬레이션 설정
        self.publish_interval = 2.0  # 초 (실제 공장에서는 1-5초 간격)
        self.is_running = False
        
        # 센서 상태 관리 (자연스러운 데이터 생성을 위해)
        self.sensor_states = {
            # 공조 장치 (CAHU - Central Air Handling Unit)
            "R-CAHU-01S": {
                "base_temp": 65.0,      # 기준 온도
                "base_pressure": 5.2,   # 기준 압력
                "base_vibration": 1.8,  # 기준 진동
                "temp_drift": 0.0,      # 온도 드리프트
                "pressure_drift": 0.0,  # 압력 드리프트
                "vibration_drift": 0.0, # 진동 드리프트
                "last_update": time.time(),
                "operating_hours": 2847,
                "maintenance_due": 23,
                "type": "CAHU",
                "location": "Factory-A"
            },
            "R-CAHU-02S": {
                "base_temp": 58.0,
                "base_pressure": 4.1,
                "base_vibration": 1.4,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 1563,
                "maintenance_due": 67,
                "type": "CAHU",
                "location": "Factory-B"
            },
            # 펌프 시스템
            "PUMP-001": {
                "base_temp": 45.0,
                "base_pressure": 8.5,
                "base_vibration": 2.1,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 1923,
                "maintenance_due": 45,
                "type": "PUMP",
                "location": "Factory-A"
            },
            "PUMP-002": {
                "base_temp": 42.0,
                "base_pressure": 7.8,
                "base_vibration": 1.9,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 2156,
                "maintenance_due": 12,
                "type": "PUMP",
                "location": "Factory-B"
            },
            # 압축기
            "COMP-001": {
                "base_temp": 75.0,
                "base_pressure": 12.5,
                "base_vibration": 3.2,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 3421,
                "maintenance_due": 89,
                "type": "COMPRESSOR",
                "location": "Factory-A"
            },
            "COMP-002": {
                "base_temp": 68.0,
                "base_pressure": 11.2,
                "base_vibration": 2.8,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 2987,
                "maintenance_due": 34,
                "type": "COMPRESSOR",
                "location": "Factory-B"
            },
            # 모터
            "MOTOR-001": {
                "base_temp": 55.0,
                "base_pressure": 2.1,
                "base_vibration": 4.5,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 4567,
                "maintenance_due": 156,
                "type": "MOTOR",
                "location": "Factory-A"
            },
            "MOTOR-002": {
                "base_temp": 52.0,
                "base_pressure": 1.8,
                "base_vibration": 4.1,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 3987,
                "maintenance_due": 78,
                "type": "MOTOR",
                "location": "Factory-B"
            },
            # 컨베이어
            "CONV-001": {
                "base_temp": 38.0,
                "base_pressure": 1.2,
                "base_vibration": 2.8,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 5234,
                "maintenance_due": 234,
                "type": "CONVEYOR",
                "location": "Factory-A"
            },
            "CONV-002": {
                "base_temp": 35.0,
                "base_pressure": 1.0,
                "base_vibration": 2.5,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 4876,
                "maintenance_due": 189,
                "type": "CONVEYOR",
                "location": "Factory-B"
            },
            # 보일러
            "BOIL-001": {
                "base_temp": 120.0,
                "base_pressure": 15.8,
                "base_vibration": 1.2,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 1876,
                "maintenance_due": 45,
                "type": "BOILER",
                "location": "Factory-A"
            },
            "BOIL-002": {
                "base_temp": 115.0,
                "base_pressure": 14.2,
                "base_vibration": 1.1,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 2341,
                "maintenance_due": 67,
                "type": "BOILER",
                "location": "Factory-B"
            },
            # 칠러
            "CHIL-001": {
                "base_temp": 8.0,
                "base_pressure": 6.5,
                "base_vibration": 1.8,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 3123,
                "maintenance_due": 123,
                "type": "CHILLER",
                "location": "Factory-A"
            },
            "CHIL-002": {
                "base_temp": 7.5,
                "base_pressure": 6.1,
                "base_vibration": 1.6,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 2876,
                "maintenance_due": 89,
                "type": "CHILLER",
                "location": "Factory-B"
            },
            # 팬
            "FAN-001": {
                "base_temp": 42.0,
                "base_pressure": 3.2,
                "base_vibration": 5.2,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 6543,
                "maintenance_due": 345,
                "type": "FAN",
                "location": "Factory-A"
            },
            "FAN-002": {
                "base_temp": 39.0,
                "base_pressure": 2.9,
                "base_vibration": 4.8,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 5987,
                "maintenance_due": 267,
                "type": "FAN",
                "location": "Factory-B"
            },
            # 밸브
            "VALV-001": {
                "base_temp": 35.0,
                "base_pressure": 9.8,
                "base_vibration": 0.8,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 4123,
                "maintenance_due": 178,
                "type": "VALVE",
                "location": "Factory-A"
            },
            "VALV-002": {
                "base_temp": 32.0,
                "base_pressure": 8.5,
                "base_vibration": 0.7,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 3876,
                "maintenance_due": 145,
                "type": "VALVE",
                "location": "Factory-B"
            },
            # 탱크
            "TANK-001": {
                "base_temp": 25.0,
                "base_pressure": 2.5,
                "base_vibration": 0.3,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 8765,
                "maintenance_due": 567,
                "type": "TANK",
                "location": "Factory-A"
            },
            "TANK-002": {
                "base_temp": 23.0,
                "base_pressure": 2.2,
                "base_vibration": 0.2,
                "temp_drift": 0.0,
                "pressure_drift": 0.0,
                "vibration_drift": 0.0,
                "last_update": time.time(),
                "operating_hours": 8234,
                "maintenance_due": 456,
                "type": "TANK",
                "location": "Factory-B"
            }
        }
        
    def on_connect(self, client, userdata, flags, rc):
        """MQTT 브로커 연결 콜백"""
        if rc == 0:
            logger.info("✅ Unity 센서 시뮬레이터가 MQTT 브로커에 성공적으로 연결되었습니다.")
            logger.info(f"   브로커: {self.broker_host}:{self.broker_port}")
        else:
            logger.error(f"❌ MQTT 브로커 연결 실패, 리턴 코드: {rc}")
            self._log_connection_error(rc)
            exit(1)
    
    def on_publish(self, client, userdata, mid):
        """메시지 발행 성공 콜백"""
        logger.debug(f"📤 메시지 발행 성공 (MID: {mid})")
    
    def on_disconnect(self, client, userdata, rc):
        """연결 해제 콜백"""
        if rc != 0:
            logger.warning(f"⚠️  예기치 않은 연결 해제 (코드: {rc})")
        else:
            logger.info("✅ MQTT 연결이 정상적으로 종료되었습니다.")
    
    def _log_connection_error(self, rc: int):
        """연결 오류 코드 설명"""
        error_messages = {
            1: "프로토콜 버전 불일치",
            2: "잘못된 클라이언트 식별자", 
            3: "서버 사용 불가",
            4: "잘못된 사용자 이름 또는 비밀번호",
            5: "권한 없음"
        }
        error_msg = error_messages.get(rc, "알 수 없는 오류")
        logger.error(f"   오류 설명: {error_msg}")
    
    def generate_realistic_sensor_value(self, base_value: float, drift: float, noise_level: float = 0.02) -> tuple:
        """자연스러운 센서 값 생성 (드리프트 + 노이즈)"""
        # 시간에 따른 드리프트 (매우 느린 변화)
        new_drift = drift + random.uniform(-0.001, 0.001)
        
        # 노이즈 추가 (실제 센서 노이즈)
        noise = random.gauss(0, noise_level * base_value)
        
        # 최종 값 계산
        final_value = base_value + new_drift + noise
        
        return final_value, new_drift
    
    def _get_equipment_efficiency(self, equipment_type: str) -> float:
        """장비 타입별 효율성 계산"""
        efficiency_ranges = {
            "CAHU": (88.0, 94.0),
            "PUMP": (85.0, 92.0),
            "COMPRESSOR": (82.0, 89.0),
            "MOTOR": (90.0, 96.0),
            "CONVEYOR": (92.0, 98.0),
            "BOILER": (85.0, 91.0),
            "CHILLER": (87.0, 93.0),
            "FAN": (86.0, 92.0),
            "VALVE": (94.0, 99.0),
            "TANK": (95.0, 99.5)
        }
        
        min_eff, max_eff = efficiency_ranges.get(equipment_type, (85.0, 95.0))
        return round(random.uniform(min_eff, max_eff), 1)
    
    def _get_equipment_power_consumption(self, equipment_type: str) -> float:
        """장비 타입별 전력 소비 계산"""
        power_ranges = {
            "CAHU": (25.0, 45.0),
            "PUMP": (15.0, 35.0),
            "COMPRESSOR": (40.0, 80.0),
            "MOTOR": (20.0, 50.0),
            "CONVEYOR": (10.0, 25.0),
            "BOILER": (60.0, 120.0),
            "CHILLER": (35.0, 70.0),
            "FAN": (8.0, 20.0),
            "VALVE": (2.0, 8.0),
            "TANK": (1.0, 5.0)
        }
        
        min_power, max_power = power_ranges.get(equipment_type, (20.0, 50.0))
        return round(random.uniform(min_power, max_power), 1)
    
    def update_sensor_state(self, sensor_id: str):
        """센서 상태 업데이트 (자연스러운 변화)"""
        current_time = time.time()
        state = self.sensor_states[sensor_id]
        
        # 시간 경과에 따른 자연스러운 변화
        time_diff = current_time - state["last_update"]
        
        # 운영 시간 증가 (매우 느리게)
        if random.random() < 0.1:  # 10% 확률로 운영 시간 증가
            state["operating_hours"] += 1
        
        # 유지보수 예정일 감소
        if random.random() < 0.05:  # 5% 확률로 유지보수 예정일 감소
            state["maintenance_due"] = max(0, state["maintenance_due"] - 1)
        
        state["last_update"] = current_time
    
    def generate_sensor_data(self) -> Dict[str, Any]:
        """실시간 센서 데이터 생성 (실제 공장 데이터처럼 자연스럽게)"""
        timestamp = datetime.now().isoformat()
        
        sensor_data = {}
        
        # 각 센서별로 자연스러운 데이터 생성
        for sensor_id in self.sensor_states.keys():
            state = self.sensor_states[sensor_id]
            
            # 센서 상태 업데이트
            self.update_sensor_state(sensor_id)
            
            # 장비 타입별 노이즈 레벨 설정
            noise_levels = {
                "CAHU": {"temp": 0.015, "pressure": 0.025, "vibration": 0.035},
                "PUMP": {"temp": 0.020, "pressure": 0.030, "vibration": 0.040},
                "COMPRESSOR": {"temp": 0.025, "pressure": 0.035, "vibration": 0.045},
                "MOTOR": {"temp": 0.030, "pressure": 0.020, "vibration": 0.050},
                "CONVEYOR": {"temp": 0.015, "pressure": 0.010, "vibration": 0.030},
                "BOILER": {"temp": 0.020, "pressure": 0.040, "vibration": 0.015},
                "CHILLER": {"temp": 0.015, "pressure": 0.025, "vibration": 0.025},
                "FAN": {"temp": 0.020, "pressure": 0.015, "vibration": 0.055},
                "VALVE": {"temp": 0.010, "pressure": 0.030, "vibration": 0.010},
                "TANK": {"temp": 0.005, "pressure": 0.015, "vibration": 0.005}
            }
            
            equipment_type = state["type"]
            noise = noise_levels.get(equipment_type, {"temp": 0.020, "pressure": 0.025, "vibration": 0.035})
            
            # 온도 (x축) - 장비별 특성에 맞게
            temp_value, state["temp_drift"] = self.generate_realistic_sensor_value(
                state["base_temp"], state["temp_drift"], noise["temp"]
            )
            
            # 압력 (y축) - 장비별 특성에 맞게
            pressure_value, state["pressure_drift"] = self.generate_realistic_sensor_value(
                state["base_pressure"], state["pressure_drift"], noise["pressure"]
            )
            
            # 진동 (z축) - 장비별 특성에 맞게
            vibration_value, state["vibration_drift"] = self.generate_realistic_sensor_value(
                state["base_vibration"], state["vibration_drift"], noise["vibration"]
            )
            
            # 장비 타입별 값 범위 제한
            temp_ranges = {
                "CAHU": (15.0, 95.0),
                "PUMP": (20.0, 80.0),
                "COMPRESSOR": (30.0, 120.0),
                "MOTOR": (25.0, 90.0),
                "CONVEYOR": (20.0, 60.0),
                "BOILER": (80.0, 150.0),
                "CHILLER": (5.0, 25.0),
                "FAN": (20.0, 70.0),
                "VALVE": (15.0, 60.0),
                "TANK": (10.0, 40.0)
            }
            
            pressure_ranges = {
                "CAHU": (0.5, 12.0),
                "PUMP": (5.0, 20.0),
                "COMPRESSOR": (8.0, 25.0),
                "MOTOR": (1.0, 5.0),
                "CONVEYOR": (0.5, 3.0),
                "BOILER": (10.0, 25.0),
                "CHILLER": (4.0, 12.0),
                "FAN": (1.0, 8.0),
                "VALVE": (5.0, 20.0),
                "TANK": (1.0, 8.0)
            }
            
            vibration_ranges = {
                "CAHU": (0.01, 8.0),
                "PUMP": (0.5, 10.0),
                "COMPRESSOR": (1.0, 12.0),
                "MOTOR": (2.0, 15.0),
                "CONVEYOR": (0.5, 8.0),
                "BOILER": (0.1, 5.0),
                "CHILLER": (0.5, 8.0),
                "FAN": (3.0, 18.0),
                "VALVE": (0.1, 3.0),
                "TANK": (0.01, 2.0)
            }
            
            temp_min, temp_max = temp_ranges.get(equipment_type, (15.0, 95.0))
            pressure_min, pressure_max = pressure_ranges.get(equipment_type, (0.5, 12.0))
            vibration_min, vibration_max = vibration_ranges.get(equipment_type, (0.01, 8.0))
            
            temp_value = max(temp_min, min(temp_max, temp_value))
            pressure_value = max(pressure_min, min(pressure_max, pressure_value))
            vibration_value = max(vibration_min, min(vibration_max, vibration_value))
            
            sensor_data[f"unity/sensors/{sensor_id}/data"] = {
                "device": sensor_id,
                "timestamp": timestamp,
                "x": round(temp_value, 2),
                "y": round(pressure_value, 2),
                "z": round(vibration_value, 3)
            }
            
            # 장비 상태 정보
            sensor_data[f"factory/equipment/status/{sensor_id}"] = {
                "equipment_id": sensor_id,
                "status": "running",
                "runtime_hours": state["operating_hours"],
                "maintenance_due": state["maintenance_due"],
                "timestamp": timestamp,
                "location": state["location"],
                "type": state["type"],
                "efficiency": self._get_equipment_efficiency(equipment_type),
                "power_consumption": self._get_equipment_power_consumption(equipment_type)
            }
        
        # 가끔 이상 데이터 생성 (실제 공장에서 발생하는 것처럼)
        if random.random() < 0.02:  # 2% 확률로 이상 데이터 (더 현실적)
            anomaly_sensor = random.choice(list(self.sensor_states.keys())) # 모든 센서 중 하나 선택
            anomaly_topic = f"unity/sensors/{anomaly_sensor}/data"
            
            if anomaly_topic in sensor_data:
                # 점진적인 이상 (갑작스럽지 않게)
                current_data = sensor_data[anomaly_topic]
                
                # 온도 이상 (점진적 증가)
                if random.random() < 0.7:
                    current_data["x"] = round(current_data["x"] * random.uniform(1.1, 1.3), 2)
                
                # 압력 이상
                if random.random() < 0.5:
                    current_data["y"] = round(current_data["y"] * random.uniform(1.15, 1.4), 2)
                
                # 진동 이상
                if random.random() < 0.6:
                    current_data["z"] = round(current_data["z"] * random.uniform(1.2, 1.5), 3)
                
                # 이상 알림 토픽 추가
                sensor_data[f"factory/alerts/sensor/{anomaly_sensor}"] = {
                    "alert_id": f"ALT-{int(time.time())}",
                    "equipment_id": anomaly_sensor,
                    "alert_type": "sensor_anomaly",
                    "severity": "medium",
                    "timestamp": timestamp,
                    "description": f"{anomaly_sensor} 센서에서 이상이 감지되었습니다",
                    "affected_sensors": ["temperature", "pressure", "vibration"],
                    "status": "active"
                }
        
        return sensor_data
    
    def publish_sensor_data(self, sensor_data: Dict[str, Any]):
        """센서 데이터를 MQTT 토픽으로 발행"""
        for topic, payload in sensor_data.items():
            try:
                payload_json = json.dumps(payload, ensure_ascii=False)
                result = self.client.publish(topic, payload_json, qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"📡 {topic}: {payload.get('value', 'N/A')} {payload.get('unit', '')}")
                else:
                    logger.error(f"❌ 토픽 {topic} 발행 실패")
                    
            except Exception as e:
                logger.error(f"❌ 데이터 발행 중 오류: {e}")
    
    def load_json_data(self, file_path: str) -> Dict[str, Any]:
        """JSON 파일에서 센서 데이터 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"⚠️  파일을 찾을 수 없습니다: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 오류: {e}")
            return {}
    
    def publish_json_data(self, file_path: str):
        """JSON 파일의 데이터를 MQTT로 발행"""
        sensor_data = self.load_json_data(file_path)
        
        if not sensor_data:
            return
            
        logger.info(f"📄 '{file_path}' 파일의 데이터 발행을 시작합니다...")
        
        for topic, payload in sensor_data.items():
            try:
                payload_json = json.dumps(payload, ensure_ascii=False)
                result = self.client.publish(topic, payload_json, qos=1)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"  ✅ {topic}")
                else:
                    logger.error(f"  ❌ {topic} [발행 실패]")
                    
                time.sleep(0.1)  # 발행 간격
                
            except Exception as e:
                logger.error(f"  ❌ {topic} [오류: {e}]")
    
    def start_simulation(self, mode: str = "realtime"):
        """시뮬레이션 시작"""
        try:
            # MQTT 브로커 연결
            logger.info(f"🔌 MQTT 브로커에 연결 중... ({self.broker_host}:{self.broker_port})")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            self.is_running = True
            logger.info("🚀 Unity 센서 시뮬레이터가 시작되었습니다.")
            
            if mode == "realtime":
                self._run_realtime_simulation()
            elif mode == "json":
                self._run_json_simulation()
            else:
                logger.error(f"❌ 알 수 없는 모드: {mode}")
                
        except ConnectionRefusedError:
            logger.error("❌ MQTT 브로커에 연결할 수 없습니다. 브로커가 실행 중인지 확인하세요.")
        except KeyboardInterrupt:
            logger.info("\n⏹️  시뮬레이터를 종료합니다...")
        except Exception as e:
            logger.error(f"❌ 시뮬레이션 중 오류: {e}")
        finally:
            self.stop_simulation()
    
    def _run_realtime_simulation(self):
        """실시간 센서 데이터 시뮬레이션"""
        logger.info("🔄 실시간 센서 데이터 시뮬레이션을 시작합니다...")
        
        while self.is_running:
            try:
                # 센서 데이터 생성 및 발행
                sensor_data = self.generate_sensor_data()
                self.publish_sensor_data(sensor_data)
                
                # 대기
                time.sleep(self.publish_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ 실시간 시뮬레이션 오류: {e}")
                time.sleep(1)
    
    def _run_json_simulation(self):
        """JSON 파일 기반 시뮬레이션"""
        json_files = ["device_stats.json", "device_anoms.json"]
        
        logger.info("📁 JSON 파일 기반 시뮬레이션을 시작합니다...")
        
        while self.is_running:
            for file_name in json_files:
                if not self.is_running:
                    break
                    
                file_path = self.data_dir / file_name
                self.publish_json_data(str(file_path))
                
                logger.info(f"✨ '{file_name}' 발행 완료. 5초 후 다음 파일을 시작합니다.")
                time.sleep(5)
    
    def stop_simulation(self):
        """시뮬레이션 중지"""
        self.is_running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("✅ Unity 센서 시뮬레이터가 종료되었습니다.")


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unity 센서 시뮬레이터")
    parser.add_argument("--host", default="localhost", help="MQTT 브로커 호스트")
    parser.add_argument("--port", type=int, default=1883, help="MQTT 브로커 포트")
    parser.add_argument("--mode", choices=["realtime", "json"], default="realtime", 
                       help="시뮬레이션 모드")
    parser.add_argument("--interval", type=float, default=1.0, help="발행 간격 (초)")
    
    args = parser.parse_args()
    
    # 시뮬레이터 생성 및 실행
    simulator = UnitySensorSimulator(args.host, args.port)
    simulator.publish_interval = args.interval
    
    try:
        simulator.start_simulation(args.mode)
    except KeyboardInterrupt:
        print("\n⏹️  시뮬레이터를 종료합니다...")


if __name__ == "__main__":
    main()
