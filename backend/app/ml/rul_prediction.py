"""
RUL 예측 모델 관리
"""
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import List, Tuple, Optional
import logging
import time
import joblib
import os
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.core.monitoring import record_model_prediction

logger = logging.getLogger(__name__)


class SensorDataset(Dataset):
    """센서 데이터셋"""
    
    def __init__(self, data: np.ndarray, targets: np.ndarray, sequence_length: int = 50):
        self.data = data
        self.targets = targets
        self.sequence_length = sequence_length
    
    def __len__(self):
        return len(self.data) - self.sequence_length
    
    def __getitem__(self, idx):
        sequence = self.data[idx:idx + self.sequence_length]
        target = self.targets[idx + self.sequence_length]
        return torch.FloatTensor(sequence), torch.FloatTensor([target])


class LSTMModel(nn.Module):
    """LSTM 기반 RUL 예측 모델"""
    
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2):
        super(LSTMModel, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1)
        )
    
    def forward(self, x):
        # LSTM 출력
        lstm_out, _ = self.lstm(x)
        
        # 마지막 시퀀스의 출력 사용
        last_output = lstm_out[:, -1, :]
        
        # 완전연결층
        output = self.fc(last_output)
        return output


class RULPredictionModel:
    """RUL 예측 모델 관리 클래스"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.target_scaler = StandardScaler()
        self.is_trained = False
        self.model_path = settings.MODEL_PATH
        self.sequence_length = 50
        
        # 모델 디렉토리 생성
        os.makedirs(self.model_path, exist_ok=True)
    
    def prepare_data(self, sensor_data: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
        """센서 데이터를 모델 입력 형태로 변환"""
        try:
            # 데이터 정렬
            df = pd.DataFrame(sensor_data)
            df = df.sort_values('time')
            
            # 특성 추출 (진동, 온도, 전류)
            features = []
            for _, row in df.iterrows():
                feature_vector = []
                
                # 진동 데이터 (RMS, 피크, 주파수 특성 등)
                if 'vibration' in row:
                    vibration = row['vibration']
                    feature_vector.extend([
                        vibration.get('rms', 0),
                        vibration.get('peak', 0),
                        vibration.get('kurtosis', 0),
                        vibration.get('skewness', 0)
                    ])
                else:
                    feature_vector.extend([0, 0, 0, 0])
                
                # 온도 데이터
                if 'temperature' in row:
                    feature_vector.append(row['temperature'].get('value', 0))
                else:
                    feature_vector.append(0)
                
                # 전류 데이터
                if 'current' in row:
                    feature_vector.append(row['current'].get('value', 0))
                else:
                    feature_vector.append(0)
                
                features.append(feature_vector)
            
            features = np.array(features)
            
            # RUL 타겟 생성 (예시: 장비 수명을 1000시간으로 가정)
            max_life = 1000
            rul_targets = np.array([max_life - i for i in range(len(features))])
            rul_targets = np.clip(rul_targets, 0, max_life)
            
            return features, rul_targets
            
        except Exception as e:
            logger.error(f"데이터 준비 실패: {e}")
            raise
    
    def train_model(self, sensor_data: List[dict], epochs: int = 100) -> bool:
        """RUL 예측 모델 훈련"""
        try:
            start_time = time.time()
            
            # 데이터 준비
            features, targets = self.prepare_data(sensor_data)
            
            # 데이터 정규화
            scaled_features = self.scaler.fit_transform(features)
            scaled_targets = self.target_scaler.fit_transform(targets.reshape(-1, 1)).flatten()
            
            # 데이터셋 생성
            dataset = SensorDataset(scaled_features, scaled_targets, self.sequence_length)
            dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
            
            # 모델 초기화
            input_size = features.shape[1]
            self.model = LSTMModel(input_size=input_size)
            
            # 손실 함수 및 옵티마이저
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.model.parameters(), lr=0.001)
            
            # 훈련
            self.model.train()
            for epoch in range(epochs):
                total_loss = 0
                for batch_features, batch_targets in dataloader:
                    optimizer.zero_grad()
                    outputs = self.model(batch_features)
                    loss = criterion(outputs, batch_targets)
                    loss.backward()
                    optimizer.step()
                    total_loss += loss.item()
                
                if epoch % 20 == 0:
                    avg_loss = total_loss / len(dataloader)
                    logger.debug(f"Epoch {epoch}, Loss: {avg_loss:.6f}")
            
            # 모델 저장
            model_file = os.path.join(self.model_path, "rul_lstm.pth")
            torch.save(self.model.state_dict(), model_file)
            
            # Scaler 저장
            scaler_file = os.path.join(self.model_path, "rul_scaler.joblib")
            joblib.dump(self.scaler, scaler_file)
            
            target_scaler_file = os.path.join(self.model_path, "rul_target_scaler.joblib")
            joblib.dump(self.target_scaler, target_scaler_file)
            
            self.is_trained = True
            
            training_time = time.time() - start_time
            logger.info(f"RUL 예측 모델 훈련 완료: {training_time:.2f}초")
            
            return True
            
        except Exception as e:
            logger.error(f"RUL 예측 모델 훈련 실패: {e}")
            return False
    
    def load_model(self) -> bool:
        """저장된 모델 로드"""
        try:
            # 모델 로드
            model_file = os.path.join(self.model_path, "rul_lstm.pth")
            if os.path.exists(model_file):
                # 모델 구조는 훈련 시 결정되므로 기본값 사용
                self.model = LSTMModel(input_size=6)  # 기본값
                self.model.load_state_dict(torch.load(model_file))
                self.model.eval()
                logger.info("RUL 예측 모델 로드 완료")
            
            # Scaler 로드
            scaler_file = os.path.join(self.model_path, "rul_scaler.joblib")
            if os.path.exists(scaler_file):
                self.scaler = joblib.load(scaler_file)
            
            target_scaler_file = os.path.join(self.model_path, "rul_target_scaler.joblib")
            if os.path.exists(target_scaler_file):
                self.target_scaler = joblib.load(target_scaler_file)
            
            self.is_trained = True
            return True
            
        except Exception as e:
            logger.error(f"RUL 예측 모델 로드 실패: {e}")
            return False
    
    def predict_rul(self, sensor_data: List[dict]) -> Tuple[float, float, float]:
        """RUL 예측"""
        try:
            start_time = time.time()
            
            if self.model is None:
                raise ValueError("RUL 예측 모델이 로드되지 않았습니다")
            
            # 데이터 준비
            features, _ = self.prepare_data(sensor_data)
            
            # 최근 시퀀스만 사용
            if len(features) < self.sequence_length:
                # 패딩으로 시퀀스 길이 맞추기
                padding = np.zeros((self.sequence_length - len(features), features.shape[1]))
                features = np.vstack([padding, features])
            else:
                features = features[-self.sequence_length:]
            
            # 데이터 정규화
            scaled_features = self.scaler.transform(features)
            
            # 예측
            self.model.eval()
            with torch.no_grad():
                input_tensor = torch.FloatTensor(scaled_features).unsqueeze(0)
                prediction = self.model(input_tensor)
                
                # 역정규화
                rul_value = self.target_scaler.inverse_transform(prediction.numpy())[0][0]
                rul_value = max(0, rul_value)  # 음수 방지
            
            # 신뢰도 계산 (예시: 예측값의 분산 기반)
            confidence = 0.8  # 예시 값, 실제로는 모델의 불확실성 추정
            uncertainty = 0.1  # 예시 값, 실제로는 모델의 불확실성 추정
            
            processing_time = time.time() - start_time
            record_model_prediction("rul_lstm", processing_time)
            
            return rul_value, confidence, uncertainty
            
        except Exception as e:
            logger.error(f"RUL 예측 실패: {e}")
            raise
    
    def get_health_status(self, rul_value: float, confidence: float) -> str:
        """건강 상태 판단"""
        if rul_value > 200:  # 200시간 이상 남음
            return "good"
        elif rul_value > 50:  # 50-200시간 남음
            return "warning"
        else:  # 50시간 이하 남음
            return "critical"


# 전역 모델 인스턴스
rul_model = RULPredictionModel() 