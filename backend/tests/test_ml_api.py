"""
ML API 호출 테스트
"""
import pytest
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List


class TestMLAPI:
    """ML API 테스트 클래스"""
    
    BASE_URL = "http://localhost:8000"
    
    @pytest.fixture
    def auth_token(self):
        """인증 토큰 획득"""
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }
        
        response = requests.post(f"{self.BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            # 테스트용 토큰 (실제로는 인증 필요)
            return "test_token"
    
    @pytest.fixture
    def sample_sensor_data(self):
        """샘플 센서 데이터"""
        return {
            "device_id": "test_device_001",
            "sensor_type": "vibration",
            "value": 0.5,
            "unit": "g",
            "time": datetime.now().isoformat()
        }
    
    @pytest.fixture
    def sample_anomaly_data(self):
        """샘플 이상 탐지 데이터"""
        return {
            "device_id": "test_device_001",
            "sensor_data": {
                "vibration": {"value": 0.8, "unit": "g"},
                "temperature": {"value": 75.0, "unit": "°C"},
                "current": {"value": 15.5, "unit": "A"}
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @pytest.fixture
    def sample_rul_data(self):
        """샘플 RUL 예측 데이터"""
        return {
            "device_id": "test_device_001",
            "sensor_history": [
                {
                    "vibration": {"value": 0.3, "unit": "g"},
                    "temperature": {"value": 65.0, "unit": "°C"},
                    "current": {"value": 12.0, "unit": "A"},
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
                },
                {
                    "vibration": {"value": 0.4, "unit": "g"},
                    "temperature": {"value": 68.0, "unit": "°C"},
                    "current": {"value": 13.0, "unit": "A"},
                    "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat()
                },
                {
                    "vibration": {"value": 0.5, "unit": "g"},
                    "temperature": {"value": 70.0, "unit": "°C"},
                    "current": {"value": 14.0, "unit": "A"},
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
    
    def test_anomaly_detection_api(self, auth_token, sample_anomaly_data):
        """이상 탐지 API 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 이상 탐지 요청
        response = requests.post(
            f"{self.BASE_URL}/api/v1/anomalies/detect",
            json=sample_anomaly_data,
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "is_anomaly" in result
        assert "confidence" in result
        assert "score" in result
        assert "device_id" in result
        assert "timestamp" in result
        
        # 데이터 타입 확인
        assert isinstance(result["is_anomaly"], bool)
        assert isinstance(result["confidence"], (int, float))
        assert isinstance(result["score"], (int, float))
        
        print(f"이상 탐지 결과: {result}")
    
    def test_rul_prediction_api(self, auth_token, sample_rul_data):
        """RUL 예측 API 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # RUL 예측 요청
        response = requests.post(
            f"{self.BASE_URL}/api/v1/rul/predict",
            json=sample_rul_data,
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "rul_value" in result
        assert "confidence" in result
        assert "uncertainty" in result
        assert "device_id" in result
        assert "timestamp" in result
        
        # 데이터 타입 확인
        assert isinstance(result["rul_value"], (int, float))
        assert isinstance(result["confidence"], (int, float))
        assert isinstance(result["uncertainty"], (int, float))
        
        print(f"RUL 예측 결과: {result}")
    
    def test_model_performance_api(self, auth_token):
        """모델 성능 API 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 모델 성능 조회
        response = requests.get(
            f"{self.BASE_URL}/api/v1/models/performance",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "anomaly_models" in result
        assert "rul_models" in result
        
        print(f"모델 성능 결과: {result}")
    
    def test_model_retrain_api(self, auth_token):
        """모델 재학습 API 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        retrain_data = {
            "device_id": "test_device_001",
            "model_type": "anomaly",  # or "rul"
            "force_retrain": False
        }
        
        # 모델 재학습 요청
        response = requests.post(
            f"{self.BASE_URL}/api/v1/models/retrain",
            json=retrain_data,
            headers=headers
        )
        
        # 재학습은 시간이 오래 걸릴 수 있으므로 202 Accepted도 허용
        assert response.status_code in [200, 202]
        
        if response.status_code == 200:
            result = response.json()
            assert "success" in result
            assert "message" in result
            print(f"모델 재학습 결과: {result}")
        else:
            print("모델 재학습 요청이 수락되었습니다 (백그라운드에서 실행 중)")
    
    def test_drift_detection_api(self, auth_token):
        """드리프트 검출 API 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 드리프트 검출 요청
        response = requests.get(
            f"{self.BASE_URL}/api/v1/models/drift?device_id=test_device_001",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "device_id" in result
        assert "drift_score" in result
        assert "detected" in result
        assert "timestamp" in result
        
        # 데이터 타입 확인
        assert isinstance(result["drift_score"], (int, float))
        assert isinstance(result["detected"], bool)
        
        print(f"드리프트 검출 결과: {result}")
    
    def test_batch_prediction_api(self, auth_token):
        """배치 예측 API 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        batch_data = {
            "device_id": "test_device_001",
            "sensor_data_batch": [
                {
                    "vibration": {"value": 0.3, "unit": "g"},
                    "temperature": {"value": 65.0, "unit": "°C"},
                    "current": {"value": 12.0, "unit": "A"},
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "vibration": {"value": 0.8, "unit": "g"},
                    "temperature": {"value": 80.0, "unit": "°C"},
                    "current": {"value": 18.0, "unit": "A"},
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        # 배치 예측 요청
        response = requests.post(
            f"{self.BASE_URL}/api/v1/models/batch-predict",
            json=batch_data,
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "predictions" in result
        assert isinstance(result["predictions"], list)
        
        for prediction in result["predictions"]:
            assert "anomaly_detection" in prediction
            assert "rul_prediction" in prediction
            assert "timestamp" in prediction
        
        print(f"배치 예측 결과: {result}")
    
    def test_model_metrics_api(self, auth_token):
        """모델 메트릭 API 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 모델 메트릭 조회
        response = requests.get(
            f"{self.BASE_URL}/api/v1/models/metrics?device_id=test_device_001",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "anomaly_metrics" in result
        assert "rul_metrics" in result
        
        if result["anomaly_metrics"]:
            anomaly_metrics = result["anomaly_metrics"]
            assert "accuracy" in anomaly_metrics
            assert "precision" in anomaly_metrics
            assert "recall" in anomaly_metrics
        
        if result["rul_metrics"]:
            rul_metrics = result["rul_metrics"]
            assert "mae" in rul_metrics
            assert "rmse" in rul_metrics
            assert "r2" in rul_metrics
        
        print(f"모델 메트릭 결과: {result}")
    
    def test_api_error_handling(self, auth_token):
        """API 오류 처리 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 잘못된 데이터로 테스트
        invalid_data = {
            "device_id": "invalid_device",
            "sensor_data": "invalid_format"
        }
        
        # 이상 탐지 API 오류 테스트
        response = requests.post(
            f"{self.BASE_URL}/api/v1/anomalies/detect",
            json=invalid_data,
            headers=headers
        )
        
        # 400 Bad Request 또는 422 Unprocessable Entity 예상
        assert response.status_code in [400, 422]
        
        error_result = response.json()
        assert "detail" in error_result
        
        print(f"오류 처리 결과: {error_result}")
    
    def test_api_authentication(self):
        """API 인증 테스트"""
        # 인증 없이 요청
        response = requests.get(f"{self.BASE_URL}/api/v1/models/performance")
        
        # 401 Unauthorized 예상
        assert response.status_code == 401
        
        print("인증 테스트 통과: 인증되지 않은 요청이 올바르게 거부됨")


if __name__ == "__main__":
    # 테스트 실행
    pytest.main([__file__, "-v"]) 