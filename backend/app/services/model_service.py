"""
모델 관리 서비스
"""
import logging
import os
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import torch

from app.ml.anomaly_detection import anomaly_model
from app.ml.rul_prediction import rul_model
from app.core.config import settings
from app.core.monitoring import record_model_training, record_model_prediction

logger = logging.getLogger(__name__)


class ModelService:
    """모델 관리 서비스"""
    
    def __init__(self):
        self.model_path = settings.MODEL_PATH
        self.backup_path = os.path.join(self.model_path, "backup")
        os.makedirs(self.backup_path, exist_ok=True)
    
    def retrain_anomaly_model(self, device_id: str, sensor_data: List[dict]) -> bool:
        """이상 탐지 모델 재학습"""
        try:
            logger.info(f"장비 {device_id} 이상 탐지 모델 재학습 시작")
            
            # 기존 모델 백업
            self._backup_models(device_id, "anomaly")
            
            # 데이터 전처리
            features = self._prepare_anomaly_data(sensor_data)
            
            if len(features) < 1000:
                logger.warning(f"장비 {device_id} 이상 탐지 재학습 데이터 부족")
                return False
            
            # 모델 재학습
            success = anomaly_model.train_isolation_forest(features)
            
            if success:
                # 모델 성능 검증
                performance = self.evaluate_anomaly_model(device_id, sensor_data)
                
                if performance['accuracy'] < 0.7:  # 성능 임계값
                    logger.warning(f"장비 {device_id} 이상 탐지 모델 성능 저하")
                    self._restore_models(device_id, "anomaly")
                    return False
                
                logger.info(f"장비 {device_id} 이상 탐지 모델 재학습 완료")
                record_model_training(device_id, "anomaly_retrain", True)
                return True
            else:
                logger.error(f"장비 {device_id} 이상 탐지 모델 재학습 실패")
                self._restore_models(device_id, "anomaly")
                record_model_training(device_id, "anomaly_retrain", False)
                return False
                
        except Exception as e:
            logger.error(f"장비 {device_id} 이상 탐지 모델 재학습 중 오류: {e}")
            self._restore_models(device_id, "anomaly")
            record_model_training(device_id, "anomaly_retrain", False)
            return False
    
    def retrain_rul_model(self, device_id: str, sensor_data: List[dict]) -> bool:
        """RUL 예측 모델 재학습"""
        try:
            logger.info(f"장비 {device_id} RUL 예측 모델 재학습 시작")
            
            # 기존 모델 백업
            self._backup_models(device_id, "rul")
            
            # 모델 재학습
            success = rul_model.train_model(sensor_data)
            
            if success:
                # 모델 성능 검증
                performance = self.evaluate_rul_model(device_id, sensor_data)
                
                if performance['mae'] > 100:  # 성능 임계값
                    logger.warning(f"장비 {device_id} RUL 예측 모델 성능 저하")
                    self._restore_models(device_id, "rul")
                    return False
                
                logger.info(f"장비 {device_id} RUL 예측 모델 재학습 완료")
                record_model_training(device_id, "rul_retrain", True)
                return True
            else:
                logger.error(f"장비 {device_id} RUL 예측 모델 재학습 실패")
                self._restore_models(device_id, "rul")
                record_model_training(device_id, "rul_retrain", False)
                return False
                
        except Exception as e:
            logger.error(f"장비 {device_id} RUL 예측 모델 재학습 중 오류: {e}")
            self._restore_models(device_id, "rul")
            record_model_training(device_id, "rul_retrain", False)
            return False
    
    def evaluate_anomaly_model(self, device_id: str, test_data: List[dict]) -> Dict:
        """이상 탐지 모델 성능 평가"""
        try:
            features = self._prepare_anomaly_data(test_data)
            
            if len(features) < 100:
                return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0}
            
            # 예측 수행
            predictions = []
            actual_labels = []  # 실제 이상 여부 (예시)
            
            for i, feature in enumerate(features[:100]):  # 최대 100개 샘플로 평가
                try:
                    is_anomaly, score = anomaly_model.detect_anomaly_isolation_forest(feature)
                    predictions.append(is_anomaly)
                    # 실제 라벨은 테스트 데이터에서 추출 (예시)
                    actual_labels.append(False)  # 실제로는 테스트 데이터에서 추출
                except Exception as e:
                    logger.warning(f"모델 평가 중 예측 실패: {e}")
                    continue
            
            if len(predictions) == 0:
                return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0}
            
            # 성능 계산 (예시)
            accuracy = np.mean([p == a for p, a in zip(predictions, actual_labels)])
            
            return {
                "accuracy": accuracy,
                "precision": 0.8,  # 예시 값
                "recall": 0.75     # 예시 값
            }
            
        except Exception as e:
            logger.error(f"이상 탐지 모델 성능 평가 중 오류: {e}")
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0}
    
    def evaluate_rul_model(self, device_id: str, test_data: List[dict]) -> Dict:
        """RUL 예측 모델 성능 평가"""
        try:
            if len(test_data) < 50:
                return {"mae": 999.0, "rmse": 999.0, "r2": 0.0}
            
            # 예측 수행
            predictions = []
            actual_values = []
            
            for i in range(min(50, len(test_data))):
                try:
                    rul_value, confidence, uncertainty = rul_model.predict_rul([test_data[i]])
                    predictions.append(rul_value)
                    # 실제 RUL 값은 테스트 데이터에서 추출 (예시)
                    actual_values.append(500.0)  # 실제로는 테스트 데이터에서 추출
                except Exception as e:
                    logger.warning(f"RUL 모델 평가 중 예측 실패: {e}")
                    continue
            
            if len(predictions) == 0:
                return {"mae": 999.0, "rmse": 999.0, "r2": 0.0}
            
            # 성능 계산
            mae = np.mean(np.abs(np.array(predictions) - np.array(actual_values)))
            rmse = np.sqrt(np.mean((np.array(predictions) - np.array(actual_values)) ** 2))
            
            return {
                "mae": mae,
                "rmse": rmse,
                "r2": 0.8  # 예시 값
            }
            
        except Exception as e:
            logger.error(f"RUL 예측 모델 성능 평가 중 오류: {e}")
            return {"mae": 999.0, "rmse": 999.0, "r2": 0.0}
    
    def calculate_drift_score(self, device_id: str, recent_data: List[dict]) -> float:
        """모델 드리프트 점수 계산"""
        try:
            if len(recent_data) < 50:
                return 0.0
            
            # 최근 데이터의 특성 분포 계산
            features = self._prepare_anomaly_data(recent_data)
            
            if len(features) == 0:
                return 0.0
            
            # 간단한 드리프트 검출 (예시)
            # 실제로는 더 정교한 방법 사용 (KL divergence, statistical tests 등)
            recent_mean = np.mean(features, axis=0)
            recent_std = np.std(features, axis=0)
            
            # 기준 분포와 비교 (예시)
            baseline_mean = np.array([0.0, 0.0, 0.0])  # 기준 분포
            baseline_std = np.array([1.0, 1.0, 1.0])
            
            # 분포 차이 계산
            mean_diff = np.mean(np.abs(recent_mean - baseline_mean))
            std_diff = np.mean(np.abs(recent_std - baseline_std))
            
            drift_score = (mean_diff + std_diff) / 2.0
            
            return min(drift_score, 1.0)  # 0-1 범위로 제한
            
        except Exception as e:
            logger.error(f"드리프트 점수 계산 중 오류: {e}")
            return 0.0
    
    def emergency_retrain_models(self, device_id: str, sensor_data: List[dict]):
        """긴급 모델 재학습"""
        try:
            logger.warning(f"장비 {device_id} 긴급 재학습 시작")
            
            # 이상 탐지 모델 긴급 재학습
            anomaly_success = self.retrain_anomaly_model(device_id, sensor_data)
            
            # RUL 예측 모델 긴급 재학습
            rul_success = self.retrain_rul_model(device_id, sensor_data)
            
            if anomaly_success and rul_success:
                logger.info(f"장비 {device_id} 긴급 재학습 완료")
            else:
                logger.error(f"장비 {device_id} 긴급 재학습 실패")
                
        except Exception as e:
            logger.error(f"장비 {device_id} 긴급 재학습 중 오류: {e}")
    
    def _prepare_anomaly_data(self, sensor_data: List[dict]) -> np.ndarray:
        """이상 탐지용 데이터 전처리"""
        try:
            features = []
            for data_point in sensor_data:
                # 진동, 온도, 전류 데이터 추출
                vibration = data_point.get('vibration', {}).get('value', 0)
                temperature = data_point.get('temperature', {}).get('value', 0)
                current = data_point.get('current', {}).get('value', 0)
                
                features.append([vibration, temperature, current])
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"이상 탐지 데이터 전처리 중 오류: {e}")
            return np.array([])
    
    def _backup_models(self, device_id: str, model_type: str):
        """모델 백업"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.backup_path, f"{device_id}_{model_type}_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # 모델 파일 백업
            if model_type == "anomaly":
                source_files = ["isolation_forest.joblib", "scaler.joblib"]
            else:  # rul
                source_files = ["rul_lstm.pth", "rul_scaler.joblib", "rul_target_scaler.joblib"]
            
            for file_name in source_files:
                source_path = os.path.join(self.model_path, file_name)
                if os.path.exists(source_path):
                    import shutil
                    shutil.copy2(source_path, os.path.join(backup_dir, file_name))
            
            logger.info(f"장비 {device_id} {model_type} 모델 백업 완료")
            
        except Exception as e:
            logger.error(f"모델 백업 중 오류: {e}")
    
    def _restore_models(self, device_id: str, model_type: str):
        """모델 복원"""
        try:
            # 가장 최근 백업 찾기
            backup_pattern = f"{device_id}_{model_type}_*"
            backup_dirs = [d for d in os.listdir(self.backup_path) if d.startswith(f"{device_id}_{model_type}_")]
            
            if not backup_dirs:
                logger.warning(f"장비 {device_id} {model_type} 모델 백업이 없습니다")
                return
            
            latest_backup = sorted(backup_dirs)[-1]
            backup_dir = os.path.join(self.backup_path, latest_backup)
            
            # 모델 파일 복원
            if model_type == "anomaly":
                source_files = ["isolation_forest.joblib", "scaler.joblib"]
            else:  # rul
                source_files = ["rul_lstm.pth", "rul_scaler.joblib", "rul_target_scaler.joblib"]
            
            for file_name in source_files:
                source_path = os.path.join(backup_dir, file_name)
                target_path = os.path.join(self.model_path, file_name)
                if os.path.exists(source_path):
                    import shutil
                    shutil.copy2(source_path, target_path)
            
            logger.info(f"장비 {device_id} {model_type} 모델 복원 완료")
            
        except Exception as e:
            logger.error(f"모델 복원 중 오류: {e}")


# 전역 모델 서비스 인스턴스
model_service = ModelService() 