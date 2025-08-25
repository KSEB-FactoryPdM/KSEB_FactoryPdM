import json
import asyncio
import os
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import pickle
import threading

from sqlalchemy import create_engine, text
from loguru import logger
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class AIModelService:
    def __init__(self):
        # 데이터베이스 설정 
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        self.engine = None
        
        # 모델 설정
        self.models_path = os.getenv('MODEL_PATH', './models')
        # serve_ml 번들 루트 (serve_ml 경로 우선 사용)
        self.serve_ml_root = os.getenv('SERVE_ML_ROOT', '/app/serve_ml')
        # Kafka 상태 표기를 위한 정보 (실제 소비는 사용하지 않음)
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', '')
        self.consumer_topic = os.getenv('KAFKA_CONSUMER_TOPIC', '')
        
        # 센서별 데이터 버퍼 (동적으로 생성)
        self.sensor_buffers = {}
        self.buffer_size = 100
        
        # XGBoost 모델 인스턴스
        self.current_model = None
        self.vibration_model = None
        
        # 예측 임계값
        self.anomaly_threshold = 0.05
        self.maintenance_threshold_days = 30
        
        self.running = False
        self.kafka_thread = None

    def init_database(self):
        """데이터베이스 연결 초기화"""
        try:
            self.engine = create_engine(self.db_url)
            logger.info("데이터베이스 연결 성공")
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            raise
            
    def init_models(self):
        """AI 모델 초기화 (models 폴더에서 XGBoost 모델 로드)"""
        try:
            # 레거시 pkl 로드는 기본 비활성화 (serve_ml 경로 사용)
            enable_legacy = os.getenv('ENABLE_LEGACY_PKL', 'false').lower() in ("1", "true", "yes")
            if enable_legacy:
                self.load_xgboost_models()
            else:
                self.current_model = None
                self.vibration_model = None
                logger.info("레거시 XGBoost pkl 로드를 비활성화했습니다 (serve_ml 번들 사용 권장)")
            
            logger.info("AI 모델 초기화 완료")
            
        except Exception as e:
            logger.error(f"AI 모델 초기화 실패: {e}")
            raise
            
    def load_xgboost_models(self):
        """XGBoost 모델 로드 (models 폴더에서)"""
        try:
            # Current 센서용 XGBoost 모델 로드 (레거시)
            current_model_path = os.path.join(self.models_path, 'current_xgb.pkl')
            if os.path.exists(current_model_path):
                with open(current_model_path, 'rb') as f:
                    self.current_model = pickle.load(f)
                logger.info(f"Current 센서 모델 로드 완료: {current_model_path}")
            else:
                logger.warning(f"Current 모델 파일을 찾을 수 없습니다: {current_model_path}")
                
            # Vibration 센서용 XGBoost 모델 로드 (레거시)
            vibration_model_path = os.path.join(self.models_path, 'vibration_xgb.pkl')
            if os.path.exists(vibration_model_path):
                with open(vibration_model_path, 'rb') as f:
                    self.vibration_model = pickle.load(f)
                logger.info(f"Vibration 센서 모델 로드 완료: {vibration_model_path}")
            else:
                logger.warning(f"Vibration 모델 파일을 찾을 수 없습니다: {vibration_model_path}")
                
            # 최소 하나의 모델은 로드되어야 함 (옵션: 더미 생성)
            if self.current_model is None and self.vibration_model is None:
                if os.getenv('ENABLE_DUMMY_MODELS', 'false').lower() in ("1", "true", "yes"):
                    logger.warning("사용 가능한 XGBoost 모델이 없습니다. 더미 모델을 생성합니다.")
                    self.create_dummy_models()
                else:
                    logger.warning("사용 가능한 XGBoost 모델이 없습니다. 더미 모델 생성을 비활성화했습니다.")
                
            logger.info("XGBoost 모델 로드 완료")
                    
        except Exception as e:
            logger.error(f"XGBoost 모델 로드 중 오류: {e}")
            raise

    def create_dummy_models(self):
        """테스트용 더미 모델 생성"""
        try:
            from sklearn.ensemble import RandomForestClassifier
            import numpy as np
            
            # 더미 데이터 생성
            X_dummy = np.random.random((100, 4))
            y_dummy = np.random.randint(0, 2, 100)
            
            # Current 센서용 더미 모델
            self.current_model = RandomForestClassifier(n_estimators=10, random_state=42)
            self.current_model.fit(X_dummy, y_dummy)
            
            # Vibration 센서용 더미 모델
            self.vibration_model = RandomForestClassifier(n_estimators=10, random_state=42)
            self.vibration_model.fit(X_dummy, y_dummy)
            
            logger.info("더미 모델 생성 완료 (개발/테스트용)")
            
        except ImportError:
            logger.error("scikit-learn이 설치되지 않아 더미 모델을 생성할 수 없습니다.")
            raise
        except Exception as e:
            logger.error(f"더미 모델 생성 중 오류: {e}")
            raise
            
    def preprocess_sensor_data(self, sensor_data: Dict[str, Any]) -> Optional[np.ndarray]:
        """Unity 센서 데이터 전처리"""
        try:
            sensor_type = sensor_data.get('sensor_type')
            values = sensor_data.get('values', {})
            
            if sensor_type == 'current':
                # Current 센서 (3축 데이터): x, y, z
                feature_vector = np.array([
                    values.get('x', 0.0),
                    values.get('y', 0.0), 
                    values.get('z', 0.0),
                    sensor_data.get('magnitude', 0.0)  # 벡터 크기도 포함
                ])
                
            elif sensor_type == 'vibration':
                # Vibration 센서 (1축 데이터): vibe
                vibe_value = values.get('vibe', 0.0)
                feature_vector = np.array([
                    vibe_value,
                    vibe_value ** 2,  # 제곱값 (비선형성 포착)
                    abs(vibe_value),  # 절댓값
                    sensor_data.get('magnitude', 0.0)  # magnitude와 동일하지만 일관성을 위해
                ])
                
            else:
                logger.warning(f"알 수 없는 센서 타입: {sensor_type}")
                return None
                
            # 기본 정규화 (0-1 스케일링)
            # 실제 환경에서는 학습 시 사용된 스케일러를 저장해서 사용해야 함
            feature_vector = np.clip(feature_vector / 1000.0, 0, 1)  # 임시 스케일링
            
            return feature_vector
            
        except Exception as e:
            logger.error(f"데이터 전처리 오류: {e}")
            return None
            
    def detect_anomaly(self, sensor_type: str, feature_vector: np.ndarray) -> Dict[str, Any]:
        """XGBoost 모델을 사용한 이상탐지 수행"""
        try:
            # 센서 타입에 따라 적절한 모델 선택
            if sensor_type == 'current' and self.current_model is not None:
                model = self.current_model
            elif sensor_type == 'vibration' and self.vibration_model is not None:
                model = self.vibration_model
            else:
                logger.warning(f"센서 타입 {sensor_type}에 대한 모델을 찾을 수 없습니다.")
                return {
                    'is_anomaly': False,
                    'anomaly_score': 0.0,
                    'confidence': 0.0,
                    'threshold': self.anomaly_threshold
                }
            
            # XGBoost 모델로 예측 (이상 확률 반환)
            feature_vector_2d = feature_vector.reshape(1, -1)
            
            # 모델이 predict_proba를 지원하는 경우 확률 사용, 아니면 predict 사용
            if hasattr(model, 'predict_proba'):
                prediction = model.predict_proba(feature_vector_2d)
                # 이진 분류의 경우 이상 클래스 확률 (클래스 1)
                anomaly_score = prediction[0][1] if prediction.shape[1] > 1 else prediction[0][0]
            else:
                prediction = model.predict(feature_vector_2d)
                anomaly_score = float(prediction[0])
            
            # 이상 여부 판정
            is_anomaly = anomaly_score > self.anomaly_threshold
            confidence = min(1.0, anomaly_score)
            
            return {
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(anomaly_score),
                'confidence': float(confidence),
                'threshold': self.anomaly_threshold
            }
            
        except Exception as e:
            logger.error(f"이상탐지 오류 ({sensor_type}): {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'threshold': self.anomaly_threshold
            }
            
    def predict_maintenance_need(self, sensor_type: str, feature_vector: np.ndarray, anomaly_score: float) -> Dict[str, Any]:
        """이상 점수 기반 예지보전 예측 (간소화된 버전)"""
        try:
            # 이상 점수를 기반으로 예지보전 필요성 판단
            # 실제 환경에서는 별도의 회귀 모델이나 더 복잡한 로직 사용 가능
            
            # 이상 점수에 따른 위험도 계산
            if anomaly_score > 0.8:
                risk_level = 'critical'
                remaining_days = max(1, 7 - (anomaly_score - 0.8) * 35)  # 1-7일
            elif anomaly_score > 0.6:
                risk_level = 'high' 
                remaining_days = 7 + (0.8 - anomaly_score) * 115  # 7-30일
            elif anomaly_score > 0.3:
                risk_level = 'medium'
                remaining_days = 30 + (0.6 - anomaly_score) * 200  # 30-90일
            else:
                risk_level = 'low'
                remaining_days = 90 + (0.3 - anomaly_score) * 900  # 90-365일
                
            remaining_days = max(1, min(365, remaining_days))
            confidence = min(1.0, anomaly_score + 0.2)  # 이상 점수가 높을수록 신뢰도 높음
            
            return {
                'remaining_days': float(remaining_days),
                'confidence': float(confidence),
                'risk_level': risk_level,
                'needs_maintenance': remaining_days < self.maintenance_threshold_days
            }
            
        except Exception as e:
            logger.error(f"예지보전 예측 오류 ({sensor_type}): {e}")
            return {
                'remaining_days': 365.0,
                'confidence': 0.0,
                'risk_level': 'low',
                'needs_maintenance': False
            }
            
    def save_prediction_to_db(self, sensor_id: str, equipment_id: int, predictions: Dict[str, Any]):
        """예측 결과를 데이터베이스에 저장"""
        try:
            current_time = datetime.utcnow()
            
            # 이상탐지 결과 저장
            anomaly_result = predictions['anomaly']
            sensor_type = predictions.get('sensor_type', 'unknown')
            anomaly_query = text("""
                INSERT INTO predictions (time, equipment_id, model_name, prediction_type, 
                                       prediction_value, confidence, threshold, is_anomaly)
                VALUES (:time, :equipment_id, :model_name, :prediction_type, 
                        :prediction_value, :confidence, :threshold, :is_anomaly)
            """)
            
            with self.engine.connect() as conn:
                conn.execute(anomaly_query, {
                    'time': current_time,
                    'equipment_id': equipment_id,
                    'model_name': f'xgb_{sensor_type}_anomaly',
                    'prediction_type': 'anomaly',
                    'prediction_value': anomaly_result['anomaly_score'],
                    'confidence': anomaly_result['confidence'],
                    'threshold': anomaly_result['threshold'],
                    'is_anomaly': anomaly_result['is_anomaly']
                })
                
                # 예지보전 결과 저장
                maintenance_result = predictions['maintenance']
                maintenance_query = text("""
                    INSERT INTO predictions (time, equipment_id, model_name, prediction_type,
                                           prediction_value, confidence, threshold, is_anomaly)
                    VALUES (:time, :equipment_id, :model_name, :prediction_type,
                            :prediction_value, :confidence, :threshold, :is_anomaly)
                """)
                
                conn.execute(maintenance_query, {
                    'time': current_time,
                    'equipment_id': equipment_id,
                    'model_name': f'xgb_{sensor_type}_maintenance',
                    'prediction_type': 'remaining_life',
                    'prediction_value': maintenance_result['remaining_days'],
                    'confidence': maintenance_result['confidence'],
                    'threshold': self.maintenance_threshold_days,
                    'is_anomaly': maintenance_result['needs_maintenance']
                })
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"DB 저장 오류: {e}")
            
    def generate_alert_if_needed(self, sensor_id: str, equipment_id: int, predictions: Dict[str, Any]):
        """필요시 알림 생성"""
        try:
            current_time = datetime.utcnow()
            alerts = []
            
            # 이상탐지 알림
            if predictions['anomaly']['is_anomaly']:
                alert = {
                    'equipment_id': equipment_id,
                    'alert_type': 'anomaly_detected',
                    'severity': 'high',
                    'title': f'센서 이상 감지: {sensor_id}',
                    'message': f'이상 점수: {predictions["anomaly"]["anomaly_score"]:.4f}',
                    'created_at': current_time
                }
                alerts.append(alert)
                
            # 예지보전 알림
            maintenance = predictions['maintenance']
            if maintenance['needs_maintenance']:
                severity = 'critical' if maintenance['risk_level'] == 'critical' else 'high'
                alert = {
                    'equipment_id': equipment_id,
                    'alert_type': 'maintenance_required',
                    'severity': severity,
                    'title': f'예지보전 알림: {sensor_id}',
                    'message': f'예상 잔여 수명: {maintenance["remaining_days"]:.1f}일',
                    'created_at': current_time
                }
                alerts.append(alert)
                
            # 알림 DB 저장
            if alerts:
                self.save_alerts_to_db(alerts)
                
        except Exception as e:
            logger.error(f"알림 생성 오류: {e}")
            
    def save_alerts_to_db(self, alerts: List[Dict[str, Any]]):
        """알림을 데이터베이스에 저장"""
        try:
            query = text("""
                INSERT INTO alerts (equipment_id, alert_type, severity, title, message, created_at)
                VALUES (:equipment_id, :alert_type, :severity, :title, :message, :created_at)
            """)
            
            with self.engine.connect() as conn:
                for alert in alerts:
                    conn.execute(query, alert)
                conn.commit()
                
            logger.info(f"{len(alerts)}개의 알림이 생성되었습니다")
            
        except Exception as e:
            logger.error(f"알림 저장 오류: {e}")
            
    def process_sensor_data(self, data: Dict[str, Any]):
        """Unity 센서 데이터 처리 및 AI 모델 예측 수행"""
        try:
            sensor_id = data.get('sensor_id', 'unknown')
            equipment_id = data.get('equipment_id', sensor_id)  # Unity device ID 사용
            sensor_type = data.get('sensor_type', 'unknown')
            
            # 데이터 전처리
            feature_vector = self.preprocess_sensor_data(data)
            if feature_vector is None:
                logger.warning(f"데이터 전처리 실패: {sensor_id}")
                return
                
            # 센서별 버퍼 동적 생성
            if sensor_id not in self.sensor_buffers:
                self.sensor_buffers[sensor_id] = deque(maxlen=self.buffer_size)
                
            # 버퍼에 특성 벡터 추가
            self.sensor_buffers[sensor_id].append(feature_vector)
            
            # 이상탐지 수행 (실시간으로 각 데이터 포인트마다 수행)
            anomaly_result = self.detect_anomaly(sensor_type, feature_vector)
            
            # 예지보전 수행 (이상 점수 기반)
            maintenance_result = self.predict_maintenance_need(
                sensor_type, feature_vector, anomaly_result['anomaly_score']
            )
            
            # 결과 통합
            predictions = {
                'anomaly': anomaly_result,
                'maintenance': maintenance_result,
                'timestamp': datetime.utcnow().isoformat(),
                'sensor_id': sensor_id,
                'sensor_type': sensor_type,
                'equipment_id': equipment_id
            }
            
            # 결과 저장
            self.save_prediction_to_db(sensor_id, equipment_id, predictions)
            
            # 알림 생성
            self.generate_alert_if_needed(sensor_id, equipment_id, predictions)
            
            logger.debug(f"AI 예측 완료: {sensor_id} ({sensor_type}), "
                       f"이상: {anomaly_result['is_anomaly']}, "
                       f"점수: {anomaly_result['anomaly_score']:.3f}, "
                       f"잔여수명: {maintenance_result['remaining_days']:.1f}일")
                
        except Exception as e:
            logger.error(f"센서 데이터 처리 오류: {e}")
            
    def start_kafka_consumer(self):
        """레거시 Kafka Consumer (미사용)"""
        logger.info("Kafka Consumer 기능은 serve_ml 경로로 대체되었습니다")

    async def start(self):
        """AI 모델 서비스 시작 (FastAPI와 함께 사용)"""
        logger.info("AI 모델 서비스 시작")
        
        try:
            # 데이터베이스 초기화
            self.init_database()
            
            # AI 모델 초기화
            self.init_models()
            
            # Kafka Consumer는 사용하지 않음
            
            self.running = True
            logger.info("AI 모델 서비스가 정상적으로 시작되었습니다")
            
        except Exception as e:
            logger.error(f"AI 모델 서비스 시작 중 오류: {e}")
            raise
            
    async def stop(self):
        """AI 모델 서비스 중지"""
        logger.info("AI 모델 서비스 중지 중...")
        
        self.running = False
        
        if self.engine:
            self.engine.dispose()
            logger.info("데이터베이스 연결 해제")
            
        logger.info("AI 모델 서비스가 정상적으로 중지되었습니다")


# Pydantic 모델들
class SensorData(BaseModel):
    sensor_id: str
    sensor_type: str
    equipment_id: int
    values: Dict[str, float]
    magnitude: Optional[float] = 0.0
    timestamp: Optional[str] = None

class PredictionResponse(BaseModel):
    anomaly: Dict[str, Any]
    maintenance: Dict[str, Any]
    timestamp: str
    sensor_id: str
    sensor_type: str
    equipment_id: int

# FastAPI 앱 생성
app = FastAPI(
    title="AI Model Service",
    description="스마트 팩토리 AI 모델 서비스 - 이상탐지 및 예지보전",
    version="1.0.0"
)

# 글로벌 AI 서비스 인스턴스
ai_service = None

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 AI 서비스 초기화"""
    global ai_service
    ai_service = AIModelService()
    await ai_service.start()
    logger.info("FastAPI AI Model Service 시작 완료")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리"""
    global ai_service
    if ai_service:
        await ai_service.stop()
    logger.info("FastAPI AI Model Service 종료 완료")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "ai-model-service",
        "timestamp": datetime.utcnow().isoformat(),
        "kafka_running": ai_service.running if ai_service else False,
        "models_loaded": {
            "current_model": ai_service.current_model is not None if ai_service else False,
            "vibration_model": ai_service.vibration_model is not None if ai_service else False
        }
    }

@app.get("/ready")
async def readiness_check():
    """준비 상태 체크 엔드포인트"""
    if not ai_service or not ai_service.running:
        raise HTTPException(status_code=503, detail="AI Service not ready")
    
    return {
        "status": "ready",
        "service": "ai-model-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(sensor_data: SensorData):
    """센서 데이터에 대한 실시간 예측"""
    if not ai_service:
        raise HTTPException(status_code=503, detail="AI Service not available")
    
    try:
        # 센서 데이터를 딕셔너리로 변환
        data_dict = sensor_data.dict()
        
        # 데이터 전처리
        feature_vector = ai_service.preprocess_sensor_data(data_dict)
        if feature_vector is None:
            raise HTTPException(status_code=400, detail="데이터 전처리 실패")
        
        # 이상탐지 수행
        anomaly_result = ai_service.detect_anomaly(sensor_data.sensor_type, feature_vector)
        
        # 예지보전 수행
        maintenance_result = ai_service.predict_maintenance_need(
            sensor_data.sensor_type, feature_vector, anomaly_result['anomaly_score']
        )
        
        # 결과 반환
        return PredictionResponse(
            anomaly=anomaly_result,
            maintenance=maintenance_result,
            timestamp=datetime.utcnow().isoformat(),
            sensor_id=sensor_data.sensor_id,
            sensor_type=sensor_data.sensor_type,
            equipment_id=sensor_data.equipment_id
        )
        
    except Exception as e:
        logger.error(f"예측 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"예측 처리 중 오류: {str(e)}")

@app.get("/models/status")
async def get_models_status():
    """모델 상태 정보 조회"""
    if not ai_service:
        raise HTTPException(status_code=503, detail="AI Service not available")
    
    return {
        "models": {
            "current_model": {
                "loaded": ai_service.current_model is not None,
                "path": os.path.join(ai_service.models_path, 'current_xgb.pkl')
            },
            "vibration_model": {
                "loaded": ai_service.vibration_model is not None,
                "path": os.path.join(ai_service.models_path, 'vibration_xgb.pkl')
            }
        },
        "thresholds": {
            "anomaly_threshold": ai_service.anomaly_threshold,
            "maintenance_threshold_days": ai_service.maintenance_threshold_days
        },
        "kafka": {
            "running": ai_service.running,
            "servers": ai_service.kafka_servers,
            "topic": ai_service.consumer_topic
        },
        "serve_ml": {
            "root": ai_service.serve_ml_root
        }
    }

@app.get("/stats")
async def get_service_stats():
    """서비스 통계 정보"""
    if not ai_service:
        raise HTTPException(status_code=503, detail="AI Service not available")
    
    return {
        "sensor_buffers": {
            sensor_id: len(buffer) 
            for sensor_id, buffer in ai_service.sensor_buffers.items()
        },
        "buffer_size": ai_service.buffer_size,
        "service_running": ai_service.running,
        "uptime": datetime.utcnow().isoformat()
    }

async def main():
    """메인 함수"""
    service = AIModelService()
    try:
        await service.start()
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 치명적 오류: {e}")
    finally:
        await service.stop()


if __name__ == "__main__":
    # 로깅 설정
    logger.add("logs/ai_model_service.log", rotation="1 day", retention="7 days")
    
    # 이벤트 루프 실행
    asyncio.run(main()) 