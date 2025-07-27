"""
이상 탐지 모델 관리
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Dict, Tuple, Optional
import logging
import time
import joblib
import os

from app.core.config import settings
from app.core.monitoring import record_model_prediction
from app.ml.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class Autoencoder(nn.Module):
    """Autoencoder 신경망 모델"""
    
    def __init__(self, input_dim: int, encoding_dim: int = 32):
        super(Autoencoder, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, encoding_dim),
            nn.ReLU()
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 128),
            nn.ReLU(),
            nn.Linear(128, input_dim),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def encode(self, x):
        return self.encoder(x)


class AnomalyDetectionModel:
    """이상 탐지 모델 관리 클래스"""
    
    def __init__(self):
        self.isolation_forest = None
        self.autoencoder = None
        self.xgboost_model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = settings.MODEL_PATH
        self.data_processor = DataProcessor()
        
        # 모델 디렉토리 생성
        os.makedirs(self.model_path, exist_ok=True)
    
    def train_isolation_forest(self, data: np.ndarray) -> bool:
        """Isolation Forest 모델 훈련"""
        try:
            start_time = time.time()
            
            # 데이터 전처리
            scaled_data = self.scaler.fit_transform(data)
            
            # Isolation Forest 모델 훈련
            self.isolation_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            self.isolation_forest.fit(scaled_data)
            
            # 모델 저장
            model_file = os.path.join(self.model_path, "isolation_forest.joblib")
            joblib.dump(self.isolation_forest, model_file)
            
            scaler_file = os.path.join(self.model_path, "scaler.joblib")
            joblib.dump(self.scaler, scaler_file)
            
            self.is_trained = True
            
            training_time = time.time() - start_time
            logger.info(f"Isolation Forest 모델 훈련 완료: {training_time:.2f}초")
            
            return True
            
        except Exception as e:
            logger.error(f"Isolation Forest 모델 훈련 실패: {e}")
            return False
    
    def train_autoencoder(self, data: np.ndarray, epochs: int = 100) -> bool:
        """Autoencoder 모델 훈련"""
        try:
            start_time = time.time()
            
            # 데이터 전처리
            scaled_data = self.scaler.fit_transform(data)
            tensor_data = torch.FloatTensor(scaled_data)
            
            # 모델 초기화
            input_dim = data.shape[1]
            self.autoencoder = Autoencoder(input_dim=input_dim)
            
            # 손실 함수 및 옵티마이저
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.autoencoder.parameters(), lr=0.001)
            
            # 훈련
            self.autoencoder.train()
            for epoch in range(epochs):
                optimizer.zero_grad()
                outputs = self.autoencoder(tensor_data)
                loss = criterion(outputs, tensor_data)
                loss.backward()
                optimizer.step()
                
                if epoch % 20 == 0:
                    logger.debug(f"Epoch {epoch}, Loss: {loss.item():.6f}")
            
            # 모델 저장
            model_file = os.path.join(self.model_path, "autoencoder.pth")
            torch.save(self.autoencoder.state_dict(), model_file)
            
            scaler_file = os.path.join(self.model_path, "autoencoder_scaler.joblib")
            joblib.dump(self.scaler, scaler_file)
            
            self.is_trained = True
            
            training_time = time.time() - start_time
            logger.info(f"Autoencoder 모델 훈련 완료: {training_time:.2f}초")
            
            return True
            
        except Exception as e:
            logger.error(f"Autoencoder 모델 훈련 실패: {e}")
            return False
    
    def train_with_sensor_data(self, 
                              normal_current_files: List[str],
                              normal_vibration_files: List[str],
                              abnormal_current_files: List[str],
                              abnormal_vibration_files: List[str]) -> Dict:
        """
        센서 데이터를 사용한 모델 훈련
        
        Args:
            normal_current_files: 정상 전류 데이터 파일 경로
            normal_vibration_files: 정상 진동 데이터 파일 경로
            abnormal_current_files: 이상 전류 데이터 파일 경로
            abnormal_vibration_files: 이상 진동 데이터 파일 경로
            
        Returns:
            훈련 결과
        """
        try:
            logger.info("센서 데이터를 사용한 모델 훈련 시작")
            
            # 데이터 로드
            normal_data = self.data_processor.load_sensor_data(
                normal_current_files, normal_vibration_files, label=0
            )
            abnormal_data = self.data_processor.load_sensor_data(
                abnormal_current_files, abnormal_vibration_files, label=1
            )
            
            # 훈련 데이터 준비
            X, y = self.data_processor.prepare_training_data(normal_data, abnormal_data)
            
            # XGBoost 모델 훈련
            results = self.data_processor.train_xgboost_model(X, y)
            self.xgboost_model = self.data_processor.model
            self.scaler = self.data_processor.scaler
            
            # 모델 저장
            self.data_processor.save_model(self.model_path)
            
            self.is_trained = True
            logger.info("센서 데이터 기반 모델 훈련 완료")
            
            return results
            
        except Exception as e:
            logger.error(f"센서 데이터 기반 모델 훈련 실패: {e}")
            raise
    
    def load_models(self) -> bool:
        """저장된 모델 로드"""
        try:
            # 기존 모델들 로드
            isolation_forest_file = os.path.join(self.model_path, "isolation_forest.joblib")
            if os.path.exists(isolation_forest_file):
                self.isolation_forest = joblib.load(isolation_forest_file)
                logger.info("Isolation Forest 모델 로드 완료")
            
            autoencoder_file = os.path.join(self.model_path, "autoencoder.pth")
            if os.path.exists(autoencoder_file):
                self.autoencoder = Autoencoder(input_dim=3)
                self.autoencoder.load_state_dict(torch.load(autoencoder_file))
                self.autoencoder.eval()
                logger.info("Autoencoder 모델 로드 완료")
            
            # XGBoost 모델 로드
            xgb_file = os.path.join(self.model_path, "xgboost_model.joblib")
            if os.path.exists(xgb_file):
                self.xgboost_model = joblib.load(xgb_file)
                logger.info("XGBoost 모델 로드 완료")
            
            # Scaler 로드
            scaler_file = os.path.join(self.model_path, "scaler.joblib")
            if os.path.exists(scaler_file):
                self.scaler = joblib.load(scaler_file)
            
            self.is_trained = True
            return True
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return False
    
    def detect_anomaly_isolation_forest(self, data: np.ndarray) -> Tuple[bool, float]:
        """Isolation Forest를 사용한 이상 탐지"""
        try:
            start_time = time.time()
            
            if self.isolation_forest is None:
                raise ValueError("Isolation Forest 모델이 로드되지 않았습니다")
            
            # 데이터 전처리
            scaled_data = self.scaler.transform(data.reshape(1, -1))
            
            # 이상 탐지
            prediction = self.isolation_forest.predict(scaled_data)
            score = self.isolation_forest.score_samples(scaled_data)[0]
            
            # 예측 결과 (1: 정상, -1: 이상)
            is_anomaly = prediction[0] == -1
            
            # 점수를 0-1 범위로 변환 (높을수록 이상)
            anomaly_score = 1 - (score + 0.5)  # Isolation Forest 점수를 이상 점수로 변환
            
            processing_time = time.time() - start_time
            record_model_prediction("isolation_forest", processing_time)
            
            return is_anomaly, anomaly_score
            
        except Exception as e:
            logger.error(f"Isolation Forest 이상 탐지 실패: {e}")
            raise
    
    def detect_anomaly_autoencoder(self, data: np.ndarray) -> Tuple[bool, float]:
        """Autoencoder를 사용한 이상 탐지"""
        try:
            start_time = time.time()
            
            if self.autoencoder is None:
                raise ValueError("Autoencoder 모델이 로드되지 않았습니다")
            
            # 데이터 전처리
            scaled_data = self.scaler.transform(data.reshape(1, -1))
            tensor_data = torch.FloatTensor(scaled_data)
            
            # 재구성 오차 계산
            self.autoencoder.eval()
            with torch.no_grad():
                reconstructed = self.autoencoder(tensor_data)
                reconstruction_error = torch.mean((tensor_data - reconstructed) ** 2).item()
            
            # 임계값 기반 이상 탐지 (임계값은 훈련 데이터로부터 결정)
            threshold = 0.1  # 예시 임계값, 실제로는 훈련 데이터로부터 계산
            is_anomaly = reconstruction_error > threshold
            
            # 이상 점수 계산 (재구성 오차를 0-1 범위로 정규화)
            anomaly_score = min(reconstruction_error / threshold, 1.0)
            
            processing_time = time.time() - start_time
            record_model_prediction("autoencoder", processing_time)
            
            return is_anomaly, anomaly_score
            
        except Exception as e:
            logger.error(f"Autoencoder 이상 탐지 실패: {e}")
            raise
    
    def detect_anomaly_xgboost(self, data: np.ndarray) -> Tuple[bool, float]:
        """XGBoost 모델을 사용한 이상 탐지"""
        try:
            start_time = time.time()
            
            if self.xgboost_model is None:
                raise ValueError("XGBoost 모델이 로드되지 않았습니다")
            
            # 데이터 전처리
            scaled_data = self.scaler.transform(data.reshape(1, -1))
            
            # 이상 탐지
            prediction = self.xgboost_model.predict(scaled_data)[0]
            probability = self.xgboost_model.predict_proba(scaled_data)[0]
            confidence = max(probability)
            
            # 예측 결과 (0: 정상, 1: 이상)
            is_anomaly = prediction == 1
            
            processing_time = time.time() - start_time
            
            # 모니터링 기록
            record_model_prediction(
                model_type="xgboost_anomaly",
                prediction=is_anomaly,
                confidence=confidence,
                processing_time=processing_time
            )
            
            logger.info(f"XGBoost 이상 탐지: {is_anomaly}, 신뢰도: {confidence:.4f}")
            
            return is_anomaly, confidence
            
        except Exception as e:
            logger.error(f"XGBoost 이상 탐지 실패: {e}")
            raise
    
    def detect_anomaly_ensemble(self, data: np.ndarray) -> Tuple[bool, float, Dict]:
        """앙상블 이상 탐지 (여러 모델 조합)"""
        try:
            start_time = time.time()
            
            results = {}
            predictions = []
            confidences = []
            
            # XGBoost 모델 사용
            if self.xgboost_model is not None:
                is_anomaly_xgb, confidence_xgb = self.detect_anomaly_xgboost(data)
                predictions.append(is_anomaly_xgb)
                confidences.append(confidence_xgb)
                results['xgboost'] = {
                    'is_anomaly': is_anomaly_xgb,
                    'confidence': confidence_xgb
                }
            
            # Isolation Forest 모델 사용
            if self.isolation_forest is not None:
                is_anomaly_if, confidence_if = self.detect_anomaly_isolation_forest(data)
                predictions.append(is_anomaly_if)
                confidences.append(confidence_if)
                results['isolation_forest'] = {
                    'is_anomaly': is_anomaly_if,
                    'confidence': confidence_if
                }
            
            # Autoencoder 모델 사용
            if self.autoencoder is not None:
                is_anomaly_ae, confidence_ae = self.detect_anomaly_autoencoder(data)
                predictions.append(is_anomaly_ae)
                confidences.append(confidence_ae)
                results['autoencoder'] = {
                    'is_anomaly': is_anomaly_ae,
                    'confidence': confidence_ae
                }
            
            # 앙상블 결과 계산 (다수결)
            if predictions:
                final_prediction = sum(predictions) > len(predictions) / 2
                final_confidence = np.mean(confidences)
            else:
                raise ValueError("사용 가능한 모델이 없습니다")
            
            processing_time = time.time() - start_time
            
            # 모니터링 기록
            record_model_prediction(
                model_type="ensemble_anomaly",
                prediction=final_prediction,
                confidence=final_confidence,
                processing_time=processing_time
            )
            
            logger.info(f"앙상블 이상 탐지: {final_prediction}, 신뢰도: {final_confidence:.4f}")
            
            return final_prediction, final_confidence, results
            
        except Exception as e:
            logger.error(f"앙상블 이상 탐지 실패: {e}")
            raise


# 전역 모델 인스턴스
anomaly_model = AnomalyDetectionModel() 