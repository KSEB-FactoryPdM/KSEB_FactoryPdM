import json
import asyncio
import os
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import pickle

import torch
import torch.nn as nn
from kafka import KafkaConsumer
from sqlalchemy import create_engine, text
from loguru import logger


class AIModelService:
    def __init__(self):
        # Kafka 설정
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.consumer_topic = 'sensor-data-processed'
        
        # 데이터베이스 설정 
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        self.engine = None
        
        # 모델 설정
        self.sequence_length = 30  # 30개 데이터 포인트로 예측
        self.input_size = 1  # 센서 값 하나
        
        # 센서별 데이터 버퍼
        self.sensor_buffers = {}
        self.buffer_size = 100
        
        # 모델 인스턴스
        self.anomaly_models = {}
        self.maintenance_models = {}
        
        # 예측 임계값
        self.anomaly_threshold = 0.05
        self.maintenance_threshold_days = 30
        
        self.running = False
        
    def init_database(self):
        """데이터베이스 연결 초기화"""
        try:
            self.engine = create_engine(self.db_url)
            logger.info("데이터베이스 연결 성공")
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            raise
            
    def init_models(self):
        """AI 모델 초기화"""
        try:
            # 센서별 모델 초기화 (current 3축 + vibration 센서)
            sensor_ids = [
                # CAHU (중앙공조기) 센서
                'L-CAHU-01R_CURR_X', 'L-CAHU-01R_CURR_Y', 'L-CAHU-01R_CURR_Z', 'L-CAHU-01R_VIB',
                'L-CAHU-02R_CURR_X', 'L-CAHU-02R_CURR_Y', 'L-CAHU-02R_CURR_Z', 'L-CAHU-02R_VIB',
                'L-CAHU-03R_CURR_X', 'L-CAHU-03R_CURR_Y', 'L-CAHU-03R_CURR_Z', 'L-CAHU-03R_VIB',
                
                # PAHU (1차공조기) 센서
                'L-PAHU-01R_CURR_X', 'L-PAHU-01R_CURR_Y', 'L-PAHU-01R_CURR_Z', 'L-PAHU-01R_VIB',
                'L-PAHU-02R_CURR_X', 'L-PAHU-02R_CURR_Y', 'L-PAHU-02R_CURR_Z', 'L-PAHU-02R_VIB',
                
                # PAC (패키지 에어컨) 센서
                'L-PAC-01R_CURR_X', 'L-PAC-01R_CURR_Y', 'L-PAC-01R_CURR_Z', 'L-PAC-01R_VIB',
                'L-PAC-02R_CURR_X', 'L-PAC-02R_CURR_Y', 'L-PAC-02R_CURR_Z', 'L-PAC-02R_VIB',
                'L-PAC-03R_CURR_X', 'L-PAC-03R_CURR_Y', 'L-PAC-03R_CURR_Z', 'L-PAC-03R_VIB',
                
                # EF (배기팬) 센서
                'L-EF-01R_CURR_X', 'L-EF-01R_CURR_Y', 'L-EF-01R_CURR_Z', 'L-EF-01R_VIB',
                'L-EF-02R_CURR_X', 'L-EF-02R_CURR_Y', 'L-EF-02R_CURR_Z', 'L-EF-02R_VIB',
                
                # SF (급기팬) 센서
                'L-SF-01R_CURR_X', 'L-SF-01R_CURR_Y', 'L-SF-01R_CURR_Z', 'L-SF-01R_VIB',
                'L-SF-02R_CURR_X', 'L-SF-02R_CURR_Y', 'L-SF-02R_CURR_Z', 'L-SF-02R_VIB',
                
                # DEF (제습배기팬) 센서
                'L-DEF-01R_CURR_X', 'L-DEF-01R_CURR_Y', 'L-DEF-01R_CURR_Z', 'L-DEF-01R_VIB',
                'L-DEF-02R_CURR_X', 'L-DEF-02R_CURR_Y', 'L-DEF-02R_CURR_Z', 'L-DEF-02R_VIB',
                
                # DSF (제습급기팬) 센서
                'L-DSF-01R_CURR_X', 'L-DSF-01R_CURR_Y', 'L-DSF-01R_CURR_Z', 'L-DSF-01R_VIB',
                'L-DSF-02R_CURR_X', 'L-DSF-02R_CURR_Y', 'L-DSF-02R_CURR_Z', 'L-DSF-02R_VIB'
            ]
            
            for sensor_id in sensor_ids:
                # 센서 데이터 버퍼 초기화
                self.sensor_buffers[sensor_id] = deque(maxlen=self.buffer_size)
                
            # 사전 훈련된 모델 로드
            self.load_pretrained_models()
            
            logger.info(f"AI 모델 초기화 완료 (센서 수: {len(sensor_ids)})")
            
        except Exception as e:
            logger.error(f"AI 모델 초기화 실패: {e}")
            raise
            
    def load_pretrained_models(self):
        """사전 훈련된 모델 로드"""
        models_dir = os.getenv('MODEL_PATH', 'models')
        
        if not os.path.exists(models_dir):
            logger.error(f"모델 디렉토리가 존재하지 않습니다: {models_dir}")
            raise FileNotFoundError(f"모델 디렉토리를 찾을 수 없습니다: {models_dir}")
            
        try:
            # current 3축 + vibration 센서들
            sensor_ids = [
                # CAHU (중앙공조기) 센서
                'L-CAHU-01R_CURR_X', 'L-CAHU-01R_CURR_Y', 'L-CAHU-01R_CURR_Z', 'L-CAHU-01R_VIB',
                'L-CAHU-02R_CURR_X', 'L-CAHU-02R_CURR_Y', 'L-CAHU-02R_CURR_Z', 'L-CAHU-02R_VIB',
                'L-CAHU-03R_CURR_X', 'L-CAHU-03R_CURR_Y', 'L-CAHU-03R_CURR_Z', 'L-CAHU-03R_VIB',
                
                # PAHU (1차공조기) 센서
                'L-PAHU-01R_CURR_X', 'L-PAHU-01R_CURR_Y', 'L-PAHU-01R_CURR_Z', 'L-PAHU-01R_VIB',
                'L-PAHU-02R_CURR_X', 'L-PAHU-02R_CURR_Y', 'L-PAHU-02R_CURR_Z', 'L-PAHU-02R_VIB',
                
                # PAC (패키지 에어컨) 센서
                'L-PAC-01R_CURR_X', 'L-PAC-01R_CURR_Y', 'L-PAC-01R_CURR_Z', 'L-PAC-01R_VIB',
                'L-PAC-02R_CURR_X', 'L-PAC-02R_CURR_Y', 'L-PAC-02R_CURR_Z', 'L-PAC-02R_VIB',
                'L-PAC-03R_CURR_X', 'L-PAC-03R_CURR_Y', 'L-PAC-03R_CURR_Z', 'L-PAC-03R_VIB',
                
                # EF (배기팬) 센서
                'L-EF-01R_CURR_X', 'L-EF-01R_CURR_Y', 'L-EF-01R_CURR_Z', 'L-EF-01R_VIB',
                'L-EF-02R_CURR_X', 'L-EF-02R_CURR_Y', 'L-EF-02R_CURR_Z', 'L-EF-02R_VIB',
                
                # SF (급기팬) 센서
                'L-SF-01R_CURR_X', 'L-SF-01R_CURR_Y', 'L-SF-01R_CURR_Z', 'L-SF-01R_VIB',
                'L-SF-02R_CURR_X', 'L-SF-02R_CURR_Y', 'L-SF-02R_CURR_Z', 'L-SF-02R_VIB',
                
                # DEF (제습배기팬) 센서
                'L-DEF-01R_CURR_X', 'L-DEF-01R_CURR_Y', 'L-DEF-01R_CURR_Z', 'L-DEF-01R_VIB',
                'L-DEF-02R_CURR_X', 'L-DEF-02R_CURR_Y', 'L-DEF-02R_CURR_Z', 'L-DEF-02R_VIB',
                
                # DSF (제습급기팬) 센서
                'L-DSF-01R_CURR_X', 'L-DSF-01R_CURR_Y', 'L-DSF-01R_CURR_Z', 'L-DSF-01R_VIB',
                'L-DSF-02R_CURR_X', 'L-DSF-02R_CURR_Y', 'L-DSF-02R_CURR_Z', 'L-DSF-02R_VIB'
            ]
                         
            for sensor_id in sensor_ids:
                # 이상탐지 모델 로드
                anomaly_path = os.path.join(models_dir, f"anomaly_{sensor_id}.pth")
                if os.path.exists(anomaly_path):
                    self.anomaly_models[sensor_id] = torch.load(anomaly_path, map_location='cpu')
                    self.anomaly_models[sensor_id].eval()
                    logger.info(f"이상탐지 모델 로드 완료: {sensor_id}")
                else:
                    logger.warning(f"이상탐지 모델 파일을 찾을 수 없습니다: {anomaly_path}")
                    
                # 예지보전 모델 로드
                maintenance_path = os.path.join(models_dir, f"maintenance_{sensor_id}.pth")
                if os.path.exists(maintenance_path):
                    self.maintenance_models[sensor_id] = torch.load(maintenance_path, map_location='cpu')
                    self.maintenance_models[sensor_id].eval()
                    logger.info(f"예지보전 모델 로드 완료: {sensor_id}")
                else:
                    logger.warning(f"예지보전 모델 파일을 찾을 수 없습니다: {maintenance_path}")
                    
            # 로드된 모델 개수 확인
            loaded_anomaly = len(self.anomaly_models)
            loaded_maintenance = len(self.maintenance_models)
            logger.info(f"모델 로드 완료 - 이상탐지: {loaded_anomaly}개, 예지보전: {loaded_maintenance}개")
            
            if loaded_anomaly == 0 and loaded_maintenance == 0:
                raise RuntimeError("사용 가능한 사전 훈련된 모델이 없습니다.")
                    
        except Exception as e:
            logger.error(f"모델 로드 중 오류: {e}")
            raise
            
    def preprocess_sensor_data(self, sensor_data: Dict[str, Any]) -> Optional[float]:
        """센서 데이터 전처리"""
        try:
            value = sensor_data['data']['value']
            
            # 기본 정규화 (센서별로 다르게 설정 가능)
            sensor_id = sensor_data['sensor_id']
            
            # 센서별 정규화 범위 (공조기 설비 전용)
            normalization_ranges = {}
            
            # 센서 타입별 기본 범위 설정 (current와 vibration만)
            def get_normalization_range(sensor_id):
                if 'CURR' in sensor_id:  # current 센서 (X, Y, Z)
                    return (0, 100)    # 전류 센서: 0~100A
                elif 'VIB' in sensor_id:  # vibration 센서
                    return (0, 100)    # 진동 센서: 0~100mm/s
                else:
                    return (0, 100)    # 기본 범위
            
            min_val, max_val = get_normalization_range(sensor_id)
            normalized_value = (value - min_val) / (max_val - min_val)
            
            # 범위 제한
            normalized_value = max(0, min(1, normalized_value))
            
            return normalized_value
            
        except Exception as e:
            logger.error(f"데이터 전처리 오류: {e}")
            return None
            
    def detect_anomaly(self, sensor_id: str, sequence: List[float]) -> Dict[str, Any]:
        """이상탐지 수행"""
        try:
            if sensor_id not in self.anomaly_models:
                logger.warning(f"센서 {sensor_id}에 대한 이상탐지 모델을 찾을 수 없습니다.")
                return {
                    'is_anomaly': False,
                    'reconstruction_error': 0.0,
                    'confidence': 0.0,
                    'threshold': self.anomaly_threshold
                }
                
            model = self.anomaly_models[sensor_id]
            
            # 시퀀스를 텐서로 변환
            input_tensor = torch.FloatTensor(sequence).unsqueeze(0).unsqueeze(-1)
            
            with torch.no_grad():
                # 모델 추론
                output = model(input_tensor)
                
                # 재구성 오류 계산 (모델 출력에 따라 다를 수 있음)
                if hasattr(output, 'shape') and len(output.shape) > 1:
                    original = input_tensor[:, -1, :]  # 마지막 값
                    reconstruction_error = torch.mean((original - output) ** 2).item()
                else:
                    reconstruction_error = float(output)
                
                # 이상 여부 판정
                is_anomaly = reconstruction_error > self.anomaly_threshold
                confidence = min(1.0, reconstruction_error / self.anomaly_threshold)
                
            return {
                'is_anomaly': bool(is_anomaly),
                'reconstruction_error': float(reconstruction_error),
                'confidence': float(confidence),
                'threshold': self.anomaly_threshold
            }
            
        except Exception as e:
            logger.error(f"이상탐지 오류 ({sensor_id}): {e}")
            return {
                'is_anomaly': False,
                'reconstruction_error': 0.0,
                'confidence': 0.0,
                'threshold': self.anomaly_threshold
            }
            
    def predict_remaining_life(self, sensor_id: str, sequence: List[float]) -> Dict[str, Any]:
        """사전 훈련된 모델을 사용한 잔여 수명 예측"""
        try:
            if sensor_id not in self.maintenance_models:
                logger.warning(f"센서 {sensor_id}에 대한 예지보전 모델을 찾을 수 없습니다.")
                return {
                    'remaining_days': 365.0,
                    'confidence': 0.0,
                    'risk_level': 'unknown',
                    'needs_maintenance': False
                }
                
            model = self.maintenance_models[sensor_id]
            
            # 시퀀스를 텐서로 변환
            input_tensor = torch.FloatTensor(sequence).unsqueeze(0).unsqueeze(-1)
            
            with torch.no_grad():
                # 잔여 수명 예측 (일 단위)
                prediction = model(input_tensor)
                predicted_days = float(prediction.item()) if hasattr(prediction, 'item') else float(prediction)
                
                # 음수 방지
                predicted_days = max(0, predicted_days)
                
                # 신뢰도 계산 (간단한 방법)
                confidence = 0.8 if predicted_days > 0 else 0.2
                
                # 위험도 판정
                risk_level = 'low'
                if predicted_days < 7:
                    risk_level = 'critical'
                elif predicted_days < 30:
                    risk_level = 'high'
                elif predicted_days < 90:
                    risk_level = 'medium'
                    
            return {
                'remaining_days': float(predicted_days),
                'confidence': float(confidence),
                'risk_level': risk_level,
                'needs_maintenance': predicted_days < self.maintenance_threshold_days
            }
            
        except Exception as e:
            logger.error(f"수명 예측 오류 ({sensor_id}): {e}")
            return {
                'remaining_days': 365.0,
                'confidence': 0.0,
                'risk_level': 'unknown',
                'needs_maintenance': False
            }
            
    def save_prediction_to_db(self, sensor_id: str, equipment_id: int, predictions: Dict[str, Any]):
        """예측 결과를 데이터베이스에 저장"""
        try:
            current_time = datetime.utcnow()
            
            # 이상탐지 결과 저장
            anomaly_result = predictions['anomaly']
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
                    'model_name': f'anomaly_detector_{sensor_id}',
                    'prediction_type': 'anomaly',
                    'prediction_value': anomaly_result['reconstruction_error'],
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
                    'model_name': f'maintenance_predictor_{sensor_id}',
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
                    'message': f'재구성 오류: {predictions["anomaly"]["reconstruction_error"]:.4f}',
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
        """센서 데이터 처리 및 예측 수행"""
        try:
            sensor_id = data['sensor_id']
            equipment_id = data.get('equipment_id', 0)
            
            # 데이터 전처리
            processed_value = self.preprocess_sensor_data(data)
            if processed_value is None:
                return
                
            # 버퍼에 데이터 추가
            self.sensor_buffers[sensor_id].append(processed_value)
            
            # 충분한 데이터가 있을 때만 예측 수행
            if len(self.sensor_buffers[sensor_id]) >= self.sequence_length:
                # 최근 시퀀스 추출
                sequence = list(self.sensor_buffers[sensor_id])[-self.sequence_length:]
                
                # 이상탐지 수행
                anomaly_result = self.detect_anomaly(sensor_id, sequence)
                
                # 예지보전 수행
                maintenance_result = self.predict_remaining_life(sensor_id, sequence)
                
                # 결과 통합
                predictions = {
                    'anomaly': anomaly_result,
                    'maintenance': maintenance_result,
                    'timestamp': datetime.utcnow().isoformat(),
                    'sensor_id': sensor_id
                }
                
                # 결과 저장
                self.save_prediction_to_db(sensor_id, equipment_id, predictions)
                
                # 알림 생성
                self.generate_alert_if_needed(sensor_id, equipment_id, predictions)
                
                logger.debug(f"예측 완료: {sensor_id}, 이상: {anomaly_result['is_anomaly']}, "
                           f"잔여수명: {maintenance_result['remaining_days']:.1f}일")
                
        except Exception as e:
            logger.error(f"센서 데이터 처리 오류: {e}")
            
    async def start(self):
        """AI 모델 서비스 시작"""
        logger.info("AI 모델 서비스 시작")
        
        try:
            # 데이터베이스 초기화
            self.init_database()
            
            # AI 모델 초기화
            self.init_models()
            
            # Kafka Consumer 설정
            consumer = KafkaConsumer(
                self.consumer_topic,
                bootstrap_servers=self.kafka_servers.split(','),
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='ai_model_service',
                auto_offset_reset='latest'
            )
            
            self.running = True
            logger.info("AI 모델 서비스가 정상적으로 시작되었습니다")
            
            # 메시지 처리 루프
            for message in consumer:
                if not self.running:
                    break
                    
                try:
                    sensor_data = message.value
                    self.process_sensor_data(sensor_data)
                    
                except Exception as e:
                    logger.error(f"메시지 처리 오류: {e}")
                    
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단되었습니다")
        except Exception as e:
            logger.error(f"AI 모델 서비스 실행 중 오류: {e}")
        finally:
            await self.stop()
            
    async def stop(self):
        """AI 모델 서비스 중지"""
        logger.info("AI 모델 서비스 중지 중...")
        
        self.running = False
        
        if self.engine:
            self.engine.dispose()
            logger.info("데이터베이스 연결 해제")
            
        logger.info("AI 모델 서비스가 정상적으로 중지되었습니다")


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