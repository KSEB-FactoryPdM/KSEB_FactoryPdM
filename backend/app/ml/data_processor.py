"""
데이터 가공 및 전처리 모듈
"""
import pandas as pd
import numpy as np
import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class DataProcessor:
    """데이터 가공 및 전처리 클래스"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self.scaler = StandardScaler()
        self.model = None
        self.is_trained = False
        
    def load_sensor_data(self, 
                         current_files: List[str], 
                         vibration_files: List[str],
                         label: int = 0) -> pd.DataFrame:
        """
        센서 데이터 로드 및 병합
        
        Args:
            current_files: 전류 데이터 파일 경로 리스트
            vibration_files: 진동 데이터 파일 경로 리스트
            label: 데이터 라벨 (0: 정상, 1: 이상)
            
        Returns:
            병합된 데이터프레임
        """
        try:
            assert len(current_files) == len(vibration_files), "current와 vibration 파일 수가 다릅니다."
            
            all_data = []
            
            for cur_path, vib_path in zip(current_files, vibration_files):
                # 파일 읽기
                cur_df = pd.read_csv(cur_path, skiprows=9, header=None, 
                                   names=["Time", "x", "y", "z", 'extra'], engine="python")
                vib_df = pd.read_csv(vib_path, skiprows=9, header=None, 
                                   names=["Time", "vibration", 'extra'], engine="python")
                
                # 불필요한 컬럼 제거
                cur_df = cur_df.drop(columns=["extra"])
                vib_df = vib_df.drop(columns=["extra"])
                
                # 시간 범위 공통 구간만 추출
                start_time = max(cur_df["Time"].min(), vib_df["Time"].min())
                end_time = min(cur_df["Time"].max(), vib_df["Time"].max())
                
                cur_sync = cur_df[(cur_df["Time"] >= start_time) & (cur_df["Time"] <= end_time)].copy()
                vib_sync = vib_df[(vib_df["Time"] >= start_time) & (vib_df["Time"] <= end_time)].copy()
                
                # 시간 기준으로 병합 (nearest 기준)
                cur_sync = cur_sync.sort_values("Time")
                vib_sync = vib_sync.sort_values("Time")
                
                merged = pd.merge_asof(cur_sync, vib_sync, on="Time", direction="nearest")
                
                # 라벨 추가
                merged["label"] = label
                
                all_data.append(merged)
            
            # 모든 데이터 합치기
            final_df = pd.concat(all_data, ignore_index=True)
            
            logger.info(f"데이터 로드 완료: {len(final_df)} 행, 라벨: {label}")
            return final_df
            
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            raise
    
    def prepare_training_data(self, 
                            normal_data: pd.DataFrame, 
                            abnormal_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        훈련 데이터 준비
        
        Args:
            normal_data: 정상 데이터
            abnormal_data: 이상 데이터
            
        Returns:
            특성 데이터와 라벨 데이터
        """
        try:
            # 데이터 통합
            combined_df = pd.concat([normal_data, abnormal_data], ignore_index=True)
            
            # 특성과 라벨 분리
            feature_columns = ['x', 'y', 'z', 'vibration']
            X = combined_df[feature_columns].values
            y = combined_df['label'].values
            
            logger.info(f"훈련 데이터 준비 완료: {len(X)} 샘플, 특성: {X.shape[1]}")
            return X, y
            
        except Exception as e:
            logger.error(f"훈련 데이터 준비 실패: {e}")
            raise
    
    def train_xgboost_model(self, X: np.ndarray, y: np.ndarray, 
                           test_size: float = 0.2, random_state: int = 42) -> Dict:
        """
        XGBoost 모델 훈련
        
        Args:
            X: 특성 데이터
            y: 라벨 데이터
            test_size: 테스트 데이터 비율
            random_state: 랜덤 시드
            
        Returns:
            훈련 결과 딕셔너리
        """
        try:
            # 데이터 스케일링
            X_scaled = self.scaler.fit_transform(X)
            
            # Train/Test 분할
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=test_size, random_state=random_state
            )
            
            # XGBoost 모델 정의 및 학습
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=random_state,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            
            self.model.fit(X_train, y_train)
            
            # 예측 및 평가
            y_pred = self.model.predict(X_test)
            
            # 성능 메트릭 계산
            cm = confusion_matrix(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
            
            self.is_trained = True
            
            results = {
                'confusion_matrix': cm,
                'classification_report': report,
                'accuracy': report['accuracy'],
                'precision': report['weighted avg']['precision'],
                'recall': report['weighted avg']['recall'],
                'f1_score': report['weighted avg']['f1-score']
            }
            
            logger.info(f"XGBoost 모델 훈련 완료: 정확도 {results['accuracy']:.4f}")
            return results
            
        except Exception as e:
            logger.error(f"XGBoost 모델 훈련 실패: {e}")
            raise
    
    def train_isolation_forest(self, X: np.ndarray, contamination: float = 0.1) -> bool:
        """
        Isolation Forest 모델 훈련
        
        Args:
            X: 특성 데이터
            contamination: 이상 비율
            
        Returns:
            훈련 성공 여부
        """
        try:
            # 정상 데이터만 사용 (라벨이 0인 데이터)
            normal_indices = np.where(X[:, -1] == 0)[0]  # 마지막 컬럼이 라벨이라고 가정
            normal_data = X[normal_indices, :-1]  # 라벨 제외
            
            # 데이터 스케일링
            X_scaled = self.scaler.fit_transform(normal_data)
            
            # Isolation Forest 모델 훈련
            self.isolation_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            self.isolation_forest.fit(X_scaled)
            
            self.is_trained = True
            logger.info("Isolation Forest 모델 훈련 완료")
            return True
            
        except Exception as e:
            logger.error(f"Isolation Forest 모델 훈련 실패: {e}")
            return False
    
    def predict_anomaly(self, data: np.ndarray) -> Tuple[bool, float]:
        """
        이상 탐지 예측
        
        Args:
            data: 예측할 데이터
            
        Returns:
            (이상 여부, 신뢰도 점수)
        """
        try:
            if not self.is_trained:
                raise ValueError("모델이 훈련되지 않았습니다")
            
            # 데이터 스케일링
            scaled_data = self.scaler.transform(data.reshape(1, -1))
            
            if hasattr(self, 'model') and self.model is not None:
                # XGBoost 모델 사용
                prediction = self.model.predict(scaled_data)[0]
                probability = self.model.predict_proba(scaled_data)[0]
                confidence = max(probability)
                
                is_anomaly = prediction == 1
                
            elif hasattr(self, 'isolation_forest') and self.isolation_forest is not None:
                # Isolation Forest 모델 사용
                prediction = self.isolation_forest.predict(scaled_data)[0]
                score = self.isolation_forest.score_samples(scaled_data)[0]
                
                is_anomaly = prediction == -1
                confidence = 1 - (score + 0.5)  # 점수를 0-1 범위로 변환
                
            else:
                raise ValueError("사용 가능한 모델이 없습니다")
            
            return is_anomaly, confidence
            
        except Exception as e:
            logger.error(f"이상 탐지 예측 실패: {e}")
            raise
    
    def save_model(self, model_path: str):
        """모델 저장"""
        try:
            os.makedirs(model_path, exist_ok=True)
            
            if hasattr(self, 'model') and self.model is not None:
                model_file = os.path.join(model_path, "xgboost_model.joblib")
                import joblib
                joblib.dump(self.model, model_file)
                
            if hasattr(self, 'isolation_forest') and self.isolation_forest is not None:
                model_file = os.path.join(model_path, "isolation_forest.joblib")
                import joblib
                joblib.dump(self.isolation_forest, model_file)
            
            # Scaler 저장
            scaler_file = os.path.join(model_path, "scaler.joblib")
            import joblib
            joblib.dump(self.scaler, scaler_file)
            
            logger.info(f"모델 저장 완료: {model_path}")
            
        except Exception as e:
            logger.error(f"모델 저장 실패: {e}")
            raise
    
    def load_model(self, model_path: str):
        """모델 로드"""
        try:
            import joblib
            
            # XGBoost 모델 로드
            xgb_file = os.path.join(model_path, "xgboost_model.joblib")
            if os.path.exists(xgb_file):
                self.model = joblib.load(xgb_file)
                logger.info("XGBoost 모델 로드 완료")
            
            # Isolation Forest 모델 로드
            if_file = os.path.join(model_path, "isolation_forest.joblib")
            if os.path.exists(if_file):
                self.isolation_forest = joblib.load(if_file)
                logger.info("Isolation Forest 모델 로드 완료")
            
            # Scaler 로드
            scaler_file = os.path.join(model_path, "scaler.joblib")
            if os.path.exists(scaler_file):
                self.scaler = joblib.load(scaler_file)
            
            self.is_trained = True
            logger.info("모델 로드 완료")
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise


def create_sample_data_processor():
    """샘플 데이터 프로세서 생성 (테스트용)"""
    
    # 정상 데이터 파일 경로 (예시)
    normal_current_files = [
        "data/current/normal/sample1.csv",
        "data/current/normal/sample2.csv",
        "data/current/normal/sample3.csv"
    ]
    
    normal_vibration_files = [
        "data/vibration/normal/sample1.csv",
        "data/vibration/normal/sample2.csv",
        "data/vibration/normal/sample3.csv"
    ]
    
    # 이상 데이터 파일 경로 (예시)
    abnormal_current_files = [
        "data/current/abnormal/sample1.csv",
        "data/current/abnormal/sample2.csv",
        "data/current/abnormal/sample3.csv"
    ]
    
    abnormal_vibration_files = [
        "data/vibration/abnormal/sample1.csv",
        "data/vibration/abnormal/sample2.csv",
        "data/vibration/abnormal/sample3.csv"
    ]
    
    processor = DataProcessor()
    
    # 데이터 로드
    normal_data = processor.load_sensor_data(normal_current_files, normal_vibration_files, label=0)
    abnormal_data = processor.load_sensor_data(abnormal_current_files, abnormal_vibration_files, label=1)
    
    # 훈련 데이터 준비
    X, y = processor.prepare_training_data(normal_data, abnormal_data)
    
    # 모델 훈련
    results = processor.train_xgboost_model(X, y)
    
    return processor, results 