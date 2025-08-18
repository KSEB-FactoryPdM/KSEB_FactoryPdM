"""
Unity 센서 시뮬레이터 (MQTT 퍼블리셔)

MQTT 브로커로 주기적으로 센서 데이터를 퍼블리시합니다.
DataCollector가 구독하는 토픽/페이로드 형식을 그대로 따릅니다.

토픽:
  - unity/sensors/<device>/data       # 전류(x,y,z)
  - unity/sensors/<device>/vibration  # 진동(vibe)

페이로드 예시(JSON):
  {"device":"L-CAHU-01R","timestamp":"2024-01-01T00:00:00Z","x":1.2,"y":-0.5,"z":0.8}
  {"device":"L-CAHU-01R","timestamp":"2024-01-01T00:00:00Z","vibe":0.12}
"""

import os
import time
import math
import json
from datetime import datetime, timezone
from typing import List

import paho.mqtt.client as mqtt
from loguru import logger


def parse_devices(env_value: str) -> List[str]:
    devices = [d.strip() for d in (env_value or "").split(",") if d.strip()]
    return devices or ["L-CAHU-01R"]


class UnitySensorSimulator:
    def __init__(self):
        # MQTT 브로커 설정 (ConfigMap: smart-factory-config 에서 공급)
        self.mqtt_host = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))

        # 시뮬레이터 설정
        self.devices = parse_devices(os.getenv("SIM_DEVICES", "L-CAHU-01R"))
        self.interval_ms = int(os.getenv("SIM_INTERVAL_MS", "1000"))
        self.mode = os.getenv("SIM_MODE", "both").lower()  # both|data|vibration
        # 시뮬레이터 파라미터(전역)
        self.base = float(os.getenv("SIM_BASE", "50"))
        self.amplitude = float(os.getenv("SIM_AMPLITUDE", "10"))
        self.noise = float(os.getenv("SIM_NOISE", "0.5"))

        # serve_ml 피처 퍼블리시 설정
        self.publish_serve_ml = os.getenv("SERVE_ML_PUBLISH", "true").lower() in ("1", "true", "yes")
        self.serve_ml_topic_base = os.getenv("SERVE_ML_FEATURE_TOPIC_BASE", "serve-ml")
        self.sim_power = os.getenv("SIM_POWER", "11kW")
        self.sim_model_version = os.getenv("SIM_MODEL_VERSION", "demo.v1")

        # MQTT 클라이언트
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"MQTT 연결 성공: {self.mqtt_host}:{self.mqtt_port}")
        else:
            logger.error(f"MQTT 연결 실패 rc={rc}")

    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"MQTT 연결 종료 rc={rc}")

    def connect(self):
        attempts = 0
        last_err = None
        while attempts < 30:
            try:
                self.client.connect(self.mqtt_host, self.mqtt_port, 60)
                return
            except Exception as e:
                last_err = e
                attempts += 1
                logger.warning(f"MQTT 연결 재시도 {attempts}/30: {e}")
                time.sleep(2)
        logger.error(f"MQTT 연결 실패: {last_err}")
        raise last_err

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def gen_current(self, t: float):
        # 간단한 사인파 + 노이즈(전역 파라미터 기반)
        x = self.base + self.amplitude * math.sin(t) + (self.noise * (2 * (os.urandom(1)[0] / 255.0) - 1))
        y = self.base + self.amplitude * math.sin(t + 2.09) + (self.noise * (2 * (os.urandom(1)[0] / 255.0) - 1))
        z = self.base + self.amplitude * math.sin(t + 4.18) + (self.noise * (2 * (os.urandom(1)[0] / 255.0) - 1))
        return x, y, z

    def gen_vibration(self, t: float):
        vibe = abs(self.amplitude * math.sin(t)) + (self.noise * (2 * (os.urandom(1)[0] / 255.0) - 1))
        return max(0.0, vibe)

    

    def publish(self):
        self.client.loop_start()
        logger.info(
            f"Unity 센서 시뮬레이터 시작 devices={self.devices}, interval_ms={self.interval_ms}, mode={self.mode}"
        )

        start = time.time()
        try:
            while True:
                t = time.time() - start
                ts = self.now_iso()
                for device in self.devices:
                    if self.mode in ("both", "data"):
                        x, y, z = self.gen_current(t)
                        payload = {
                            "device": device,
                            "timestamp": ts,
                            "x": round(x, 3),
                            "y": round(y, 3),
                            "z": round(z, 3),
                        }
                        topic = f"unity/sensors/{device}/data"
                        self.client.publish(topic, json.dumps(payload), qos=1)

                    if self.mode in ("both", "vibration"):
                        vibe = self.gen_vibration(t)
                        payload = {
                            "device": device,
                            "timestamp": ts,
                            "vibe": round(vibe, 3),
                        }
                        topic = f"unity/sensors/{device}/vibration"
                        self.client.publish(topic, json.dumps(payload), qos=1)

                    # serve_ml 피처 퍼블리시 (선택)
                    if self.publish_serve_ml:
                        # 현재 시점 값으로 간단 피처 구성
                        # 데이터 모드가 아닐 때도 최소 값 생성
                        x2, y2, z2 = self.gen_current(t)
                        vibe2 = self.gen_vibration(t)
                        feats = self.build_features(x2, y2, z2, vibe2)
                        feature_payload = {
                            "power": self.sim_power,
                            "model_version": self.sim_model_version,
                            "features": feats,
                        }
                        feature_topic = f"{self.serve_ml_topic_base}/{device}/features"
                        self.client.publish(feature_topic, json.dumps(feature_payload), qos=1)

                time.sleep(max(0.05, self.interval_ms / 1000.0))
        except KeyboardInterrupt:
            logger.info("시뮬레이터 종료 요청")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT 연결 해제")


def main_env():
    sim = UnitySensorSimulator()
    sim.connect()
    sim.publish()


if __name__ == "__main__" and os.getenv("RUN_ENV_SIM") == "1":
    main_env()

"""
Unity 센서 시뮬레이터 (프로젝트 포맷 전용)
- Current: unity/sensors/{equipment_id}/data -> {device, timestamp, x, y, z}
- Vibration: unity/sensors/{equipment_id}/vibration -> {device, timestamp, vibe}

장비 ID는 반드시 serve_ml 디렉토리에서만 로드하여, 알 수 없는 장비명이 나오지 않도록 한다.
"""

import json
import os
import time
import random
import logging
from datetime import datetime
from typing import Dict, Any, List

import paho.mqtt.client as mqtt
from app.services.serve_ml_loader import serve_ml_registry


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnitySensorSimulator:
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect

        # 발행 주기(초)
        self.publish_interval = 2.0
        # 기본 활성화 (환경변수 불필요). 에러 없이 동작하도록 serve_ml_loader가 lazy-load/예외처리됨
        self.publish_serve_ml_features = True
        self.is_running = False

        # RUL 캘리브레이션 스케일과 정합되도록 진동 기본 스케일(소수점 수천분대)로 설정
        # 필요 시 환경변수로 조정
        import os as _os
        self.vibe_mean = float(_os.getenv("SIM_VIBE_MEAN", "0.008"))
        self.vibe_std = float(_os.getenv("SIM_VIBE_STD", "0.002"))

        # serve_ml에서만 장비 로드
        try:
            self.equipment_ids: List[str] = serve_ml_registry.list_equipment() or []
        except Exception as e:
            logger.error(f"serve_ml 장비 로드 실패: {e}")
            self.equipment_ids = []

        if not self.equipment_ids:
            logger.warning("serve_ml 디렉토리에 장비가 없습니다. 시뮬레이터는 데이터를 발행하지 않습니다.")

        # 이상치 주입 설정 (테스트용: 극단적 이상치)
        self.target_device_id = "L-DEF-01"
        self.global_anomaly_prob = 0  # 모든 장비 0% 이상치
        # 기본 전략: 모든 장비에서 항상 이상치 발생
        self.target_anomaly_prob = 1.0
        self.anomaly_amplify_min = 3.0  # 테스트용: 극단적으로 괴랄한 이상치
        self.anomaly_amplify_max = 10.0  # 테스트용: 극단적으로 괴랄한 이상치

    # MQTT 콜백
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"✅ MQTT 연결 성공: {self.broker_host}:{self.broker_port}")
        else:
            logger.error(f"❌ MQTT 연결 실패 (rc={rc})")

    def on_publish(self, client, userdata, mid):
        logger.debug(f"📤 발행 성공 MID={mid}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"⚠️ 예기치 않은 연결 해제 (rc={rc})")
        else:
            logger.info("✅ MQTT 정상 종료")

    # 데이터 생성/발행
    def generate_sensor_data(self) -> Dict[str, Any]:
        timestamp = datetime.utcnow().isoformat()
        sensor_data: Dict[str, Any] = {}

        for equipment_id in self.equipment_ids:
            # Current (x,y,z): -1 ~ 1 범위의 작은 변동값
            x_val = random.uniform(-1.0, 1.0)
            y_val = random.uniform(-1.0, 1.0)
            z_val = random.uniform(-1.0, 1.0)
            sensor_data[f"unity/sensors/{equipment_id}/data"] = {
                "device": equipment_id,
                "timestamp": timestamp,
                "x": round(x_val, 3),
                "y": round(y_val, 3),
                "z": round(z_val, 3),
            }

            # Vibration (vibe): 캘리브레이션 스케일(수천분대)로 생성
            vibe_val = abs(random.gauss(self.vibe_mean, self.vibe_std))
            sensor_data[f"unity/sensors/{equipment_id}/vibration"] = {
                "device": equipment_id,
                "timestamp": timestamp,
                "vibe": round(vibe_val, 3),
            }

            # 장비별 확률로 이상치 주입 (대상 장비는 높게, 그 외는 매우 낮게)
            anomaly_prob = (
                self.target_anomaly_prob
                if equipment_id == self.target_device_id
                else self.global_anomaly_prob
            )
            if random.random() < anomaly_prob:
                data_topic = f"unity/sensors/{equipment_id}/data"
                vib_topic = f"unity/sensors/{equipment_id}/vibration"
                if data_topic in sensor_data:
                    for axis in ("x", "y", "z"):
                        amplify = random.uniform(self.anomaly_amplify_min, self.anomaly_amplify_max)
                        sensor_data[data_topic][axis] = round(
                            sensor_data[data_topic][axis] * amplify, 3
                        )
                if vib_topic in sensor_data:
                    amplify = random.uniform(self.anomaly_amplify_min, self.anomaly_amplify_max)
                    sensor_data[vib_topic]["vibe"] = round(
                        sensor_data[vib_topic]["vibe"] * amplify, 3
                    )

        return sensor_data

    def publish_sensor_data(self, sensor_data: Dict[str, Any]):
        for topic, payload in sensor_data.items():
            try:
                payload_json = json.dumps(payload, ensure_ascii=False)
                result = self.client.publish(topic, payload_json, qos=1)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    logger.error(f"❌ 발행 실패: {topic}")
            except Exception as e:
                logger.error(f"❌ 발행 오류: {e}")

        # serve_ml feature 퍼블리시 (bundle feature_spec 기준 간단 매핑)
        if self.publish_serve_ml_features and self.equipment_ids:
            try:
                for equipment_id in self.equipment_ids:
                    powers = serve_ml_registry.list_powers(equipment_id)
                    if not powers:
                        continue
                    power = powers[0]
                    versions = serve_ml_registry.list_versions(equipment_id, power)
                    if not versions:
                        continue
                    bundle = serve_ml_registry.resolve_bundle(equipment_id, power, None)

                    # feature_spec 키 전부를 채워 차원/순서 일치 보장(원 설계 유지)
                    base_cur = sensor_data.get(f"unity/sensors/{equipment_id}/data", {})
                    base_vib = sensor_data.get(f"unity/sensors/{equipment_id}/vibration", {})
                    feature_payload: Dict[str, float] = {}
                    for k in bundle.feature_spec.feature_keys:
                        if k.startswith("vib_"):
                            feature_payload[k] = float(base_vib.get("vibe", 0.0))
                        elif k.startswith("cur_x_"):
                            feature_payload[k] = float(base_cur.get("x", 0.0))
                        elif k.startswith("cur_y_"):
                            feature_payload[k] = float(base_cur.get("y", 0.0))
                        elif k.startswith("cur_z_"):
                            feature_payload[k] = float(base_cur.get("z", 0.0))
                        else:
                            feature_payload[k] = 0.0

                    serve_ml_topic = f"serve-ml/{equipment_id}/features"
                    self.client.publish(serve_ml_topic, json.dumps({
                        "power": power,
                        "features": feature_payload
                    }, ensure_ascii=False), qos=1)
            except Exception as e:
                logger.error(f"serve_ml feature 발행 오류: {e}")

    # 실행 제어
    def start_simulation(self, mode: str = "realtime"):
        try:
            logger.info(f"🔌 MQTT 연결: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            self.is_running = True
            logger.info("🚀 Unity 센서 시뮬레이터 시작")

            if mode == "realtime":
                self._run_realtime()
            else:
                logger.error(f"❌ 알 수 없는 모드: {mode}")
        except KeyboardInterrupt:
            logger.info("중단 요청")
        except Exception as e:
            logger.error(f"❌ 시뮬레이션 오류: {e}")
        finally:
            self.stop_simulation()

    def _run_realtime(self):
        logger.info("🔄 실시간 시뮬레이션 시작")
        while self.is_running:
            try:
                data = self.generate_sensor_data()
                self.publish_sensor_data(data)
                time.sleep(self.publish_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ 루프 오류: {e}")
                time.sleep(1)

    def stop_simulation(self):
        self.is_running = False
        try:
            self.client.loop_stop()
            self.client.disconnect()
        finally:
            logger.info("✅ Unity 센서 시뮬레이터 종료")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Unity 센서 시뮬레이터")
    parser.add_argument("--host", default="localhost", help="MQTT 브로커 호스트")
    parser.add_argument("--port", type=int, default=1883, help="MQTT 브로커 포트")
    parser.add_argument("--mode", choices=["realtime"], default="realtime", help="시뮬레이션 모드")
    parser.add_argument("--interval", type=float, default=1.0, help="발행 간격(초)")
    parser.add_argument("--target-device", default="L-DEF-01", help="자주 이상치 발생 장비 ID")
    parser.add_argument(
        "--target-anomaly-prob", type=float, default=1.0, help="대상 장비 이상치 확률 (0~1)"
    )
    parser.add_argument(
        "--global-anomaly-prob", type=float, default=0.0, help="그 외 장비 이상치 확률 (0~1)"
    )

    args = parser.parse_args()
    sim = UnitySensorSimulator(args.host, args.port)
    sim.publish_interval = args.interval
    # 이상치 주입 설정 덮어쓰기 (CLI)
    sim.target_device_id = args.target_device
    sim.target_anomaly_prob = args.target_anomaly_prob
    sim.global_anomaly_prob = args.global_anomaly_prob

    try:
        sim.start_simulation(args.mode)
    except KeyboardInterrupt:
        print("\n⏹️  시뮬레이터 종료")


if __name__ == "__main__":
    main()
