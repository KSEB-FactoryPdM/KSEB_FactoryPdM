"""
MQTT 수신 → feature 기반 serve_ml 번들 추론 → DB 저장 파이프라인

주의: 원시신호를 보내는 경우 동일한 피처 추출 로직/파라미터가 서버에 있어야 합니다.
초기에는 feature 입력을 권장 (feature_spec.yaml 키 기반)
"""

import json
import os
from datetime import datetime
from typing import Dict, Any

import paho.mqtt.client as mqtt
from loguru import logger
from sqlalchemy import text

from app.services.serve_ml_loader import serve_ml_registry
from app.core.database import get_timescale_engine
from app.core.database import SessionLocal
from app.services.notification_service import notification_service


class ServeMLMqttInfer:
    def __init__(self):
        self.mqtt_host = os.getenv("MQTT_BROKER_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_BROKER_PORT", 1883))
        self.topic = os.getenv("SERVE_ML_FEATURE_TOPIC", "serve-ml/+/features")
        # topic 예: serve-ml/<equipment_id>/features
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.timescale_engine = get_timescale_engine()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"MQTT 연결 성공: {self.mqtt_host}:{self.mqtt_port}")
            client.subscribe(self.topic)
            logger.info(f"토픽 구독: {self.topic}")
        else:
            logger.error(f"MQTT 연결 실패: rc={rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split("/")
            # ['serve-ml', '<equipment_id>', 'features']
            equipment_id = topic_parts[1] if len(topic_parts) >= 3 else None
            payload = json.loads(msg.payload.decode("utf-8"))
            # payload: { power?, model_version?, features: {...} }

            if not equipment_id or "features" not in payload:
                logger.warning("잘못된 메시지: equipment_id/features 누락")
                return

            power = payload.get("power")
            model_version = payload.get("model_version")
            features: Dict[str, Any] = payload["features"]

            # power 자동 선택 (없으면 휴리스틱 기반 버킷 선택)
            selected_power = power
            if selected_power is None:
                try:
                    selected_power = serve_ml_registry.select_power_by_rule(equipment_id, features)
                except Exception:
                    selected_power = None

            bundle = serve_ml_registry.resolve_bundle(equipment_id, selected_power, model_version)
            result = bundle.infer(features)

            with self.timescale_engine.connect() as conn:
                query = text(
                    """
                    INSERT INTO serve_ml_predictions (
                        time, equipment_id, power, model_version,
                        is_anomaly, confidence, scores, thresholds, modalities,
                        features, bundle_path
                    ) VALUES (
                        :time, :equipment_id, :power, :model_version,
                        :is_anomaly, :confidence, CAST(:scores AS JSONB), CAST(:thresholds AS JSONB), CAST(:modalities AS JSONB),
                        CAST(:features AS JSONB), :bundle_path
                    )
                    """
                )
                import json as _json
                payload_db = {
                    "time": datetime.utcnow(),
                    "equipment_id": equipment_id,
                    "power": selected_power or "auto",
                    "model_version": model_version or bundle.bundle_dir.name,
                    "is_anomaly": result["is_anomaly"],
                    "confidence": float(result.get("confidence", 0.0)),
                    "scores": _json.dumps(result.get("scores")),
                    "thresholds": _json.dumps(result.get("thresholds")),
                    "modalities": _json.dumps(result.get("modalities")),
                    "features": _json.dumps(result.get("used_features")),
                    "bundle_path": str(bundle.bundle_dir),
                }
                conn.execute(query, payload_db)
                conn.commit()

            logger.info(f"serve_ml 추론 완료: {equipment_id}, anomaly={result['is_anomaly']}, conf={result.get('confidence', 0.0):.3f}")

            # 이상 발생 시 알림 전송 (Slack/Email)
            try:
                if bool(result.get("is_anomaly")):
                    confidence = float(result.get("confidence", 0.0))
                    if confidence > 0.8:
                        severity = "critical"
                    elif confidence > 0.6:
                        severity = "high"
                    elif confidence > 0.4:
                        severity = "medium"
                    else:
                        severity = "low"

                    anomaly_type = "general_anomaly"
                    sensor_value = None
                    try:
                        scores = result.get("scores") or {}
                        if isinstance(scores, dict) and scores:
                            top_key = max(scores.keys(), key=lambda k: scores[k] if scores[k] is not None else float('-inf'))
                            anomaly_type = str(top_key)
                            sensor_value = float(scores.get(top_key)) if scores.get(top_key) is not None else None
                    except Exception:
                        pass

                    message = (
                        f"장비 {equipment_id} 이상 탐지. 모델={model_version or bundle.bundle_dir.name}, "
                        f"신뢰도={confidence:.2f}, 유형={anomaly_type}"
                    )

                    # 세션 생성/종료 보장
                    db = SessionLocal()
                    try:
                        notification_service.create_notification(
                            db=db,
                            device_id=equipment_id,
                            sensor_id=anomaly_type,
                            alert_type="anomaly",
                            anomaly_type=anomaly_type,
                            severity=severity,
                            message=message,
                            sensor_value=sensor_value,
                            threshold_value=None,
                        )
                    finally:
                        db.close()
            except Exception:
                # 알림 실패는 무시 (로그만 남김)
                logger.exception("알림 전송 실패")
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")

    def start(self):
        self.client.connect(self.mqtt_host, self.mqtt_port, 60)
        self.client.loop_start()
        logger.info("ServeML MQTT Inference 시작")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("ServeML MQTT Inference 종료")


serve_ml_mqtt_infer = ServeMLMqttInfer()


