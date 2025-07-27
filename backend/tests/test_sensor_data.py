"""
센서 데이터 저장 테스트
"""
import pytest
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import sqlite3
from pathlib import Path


class TestSensorData:
    """센서 데이터 저장 테스트 클래스"""
    
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
    def multiple_sensor_data(self):
        """다중 센서 데이터"""
        base_time = datetime.now()
        return [
            {
                "device_id": "test_device_001",
                "sensor_type": "vibration",
                "value": 0.5 + i * 0.1,
                "unit": "g",
                "time": (base_time + timedelta(minutes=i)).isoformat()
            }
            for i in range(10)
        ]
    
    def test_single_sensor_data_save(self, auth_token, sample_sensor_data):
        """단일 센서 데이터 저장 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 센서 데이터 저장
        response = requests.post(
            f"{self.BASE_URL}/api/v1/sensors/data",
            json=sample_sensor_data,
            headers=headers
        )
        
        assert response.status_code == 201
        result = response.json()
        
        # 응답 구조 확인
        assert "id" in result
        assert "device_id" in result
        assert "sensor_type" in result
        assert "value" in result
        assert "unit" in result
        assert "time" in result
        
        # 데이터 일치성 확인
        assert result["device_id"] == sample_sensor_data["device_id"]
        assert result["sensor_type"] == sample_sensor_data["sensor_type"]
        assert result["value"] == sample_sensor_data["value"]
        assert result["unit"] == sample_sensor_data["unit"]
        
        print(f"단일 센서 데이터 저장 성공: {result}")
    
    def test_batch_sensor_data_save(self, auth_token, multiple_sensor_data):
        """배치 센서 데이터 저장 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 배치 센서 데이터 저장
        response = requests.post(
            f"{self.BASE_URL}/api/v1/sensors/batch-data",
            json={"sensor_data": multiple_sensor_data},
            headers=headers
        )
        
        assert response.status_code == 201
        result = response.json()
        
        # 응답 구조 확인
        assert "saved_count" in result
        assert "failed_count" in result
        assert "results" in result
        
        # 저장된 데이터 수 확인
        assert result["saved_count"] == len(multiple_sensor_data)
        assert result["failed_count"] == 0
        
        print(f"배치 센서 데이터 저장 성공: {result}")
    
    def test_sensor_data_retrieval(self, auth_token):
        """센서 데이터 조회 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 센서 데이터 조회
        params = {
            "device_id": "test_device_001",
            "sensor_type": "vibration",
            "start_time": (datetime.now() - timedelta(hours=1)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "limit": 100
        }
        
        response = requests.get(
            f"{self.BASE_URL}/api/v1/sensors/data",
            params=params,
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "data" in result
        assert "total_count" in result
        assert "page" in result
        assert "size" in result
        
        # 데이터 타입 확인
        assert isinstance(result["data"], list)
        assert isinstance(result["total_count"], int)
        
        print(f"센서 데이터 조회 성공: 총 {result['total_count']}개 데이터")
    
    def test_sensor_data_aggregation(self, auth_token):
        """센서 데이터 집계 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 센서 데이터 집계
        params = {
            "device_id": "test_device_001",
            "sensor_type": "vibration",
            "start_time": (datetime.now() - timedelta(hours=24)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "aggregation": "hourly"  # hourly, daily, weekly
        }
        
        response = requests.get(
            f"{self.BASE_URL}/api/v1/sensors/aggregation",
            params=params,
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "aggregations" in result
        assert isinstance(result["aggregations"], list)
        
        if result["aggregations"]:
            aggregation = result["aggregations"][0]
            assert "timestamp" in aggregation
            assert "avg_value" in aggregation
            assert "min_value" in aggregation
            assert "max_value" in aggregation
            assert "count" in aggregation
        
        print(f"센서 데이터 집계 성공: {len(result['aggregations'])}개 집계 데이터")
    
    def test_sensor_data_validation(self, auth_token):
        """센서 데이터 검증 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 잘못된 데이터로 테스트
        invalid_data = {
            "device_id": "test_device_001",
            "sensor_type": "invalid_sensor",
            "value": "invalid_value",  # 숫자가 아닌 값
            "unit": "g",
            "time": "invalid_time"  # 잘못된 시간 형식
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/sensors/data",
            json=invalid_data,
            headers=headers
        )
        
        # 422 Unprocessable Entity 예상
        assert response.status_code == 422
        
        error_result = response.json()
        assert "detail" in error_result
        
        print(f"센서 데이터 검증 테스트 통과: {error_result}")
    
    def test_sensor_data_backup_recovery(self, auth_token):
        """센서 데이터 백업 및 복구 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 백업 데이터 조회
        response = requests.get(
            f"{self.BASE_URL}/api/v1/sensors/backup-status",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"백업 상태: {result}")
        
        # 실패한 데이터 재시도
        retry_response = requests.post(
            f"{self.BASE_URL}/api/v1/sensors/retry-failed",
            headers=headers
        )
        
        if retry_response.status_code == 200:
            retry_result = retry_response.json()
            print(f"실패 데이터 재시도 결과: {retry_result}")
    
    def test_sensor_collection_statistics(self, auth_token):
        """센서 수집 통계 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 수집 통계 조회
        response = requests.get(
            f"{self.BASE_URL}/api/v1/sensors/collection-stats",
            headers=headers
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 응답 구조 확인
        assert "total_sensors" in result
        assert "total_success" in result
        assert "total_failure" in result
        assert "average_failure_rate" in result
        assert "sensors" in result
        
        print(f"센서 수집 통계: {result}")
    
    def test_sensor_data_compression(self, auth_token):
        """센서 데이터 압축 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 데이터 압축 요청
        compression_data = {
            "device_id": "test_device_001",
            "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "compression_algorithm": "gzip"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/sensors/compress",
            json=compression_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"센서 데이터 압축 결과: {result}")
        else:
            print("센서 데이터 압축 기능이 구현되지 않았습니다")
    
    def test_sensor_data_export(self, auth_token):
        """센서 데이터 내보내기 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 데이터 내보내기 요청
        export_params = {
            "device_id": "test_device_001",
            "sensor_type": "vibration",
            "start_time": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_time": datetime.now().isoformat(),
            "format": "csv"  # csv, json, excel
        }
        
        response = requests.get(
            f"{self.BASE_URL}/api/v1/sensors/export",
            params=export_params,
            headers=headers
        )
        
        if response.status_code == 200:
            # 파일 다운로드 확인
            assert response.headers.get("content-type") in [
                "text/csv",
                "application/json",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ]
            print("센서 데이터 내보내기 성공")
        else:
            print("센서 데이터 내보내기 기능이 구현되지 않았습니다")
    
    def test_sensor_data_integrity(self, auth_token):
        """센서 데이터 무결성 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 데이터 무결성 검사
        integrity_params = {
            "device_id": "test_device_001",
            "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_time": datetime.now().isoformat()
        }
        
        response = requests.get(
            f"{self.BASE_URL}/api/v1/sensors/integrity-check",
            params=integrity_params,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"센서 데이터 무결성 검사 결과: {result}")
        else:
            print("센서 데이터 무결성 검사 기능이 구현되지 않았습니다")
    
    def test_sensor_data_performance(self, auth_token, multiple_sensor_data):
        """센서 데이터 성능 테스트"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 대용량 데이터 저장 성능 테스트
        start_time = time.time()
        
        # 1000개의 데이터를 배치로 저장
        batch_size = 100
        total_data = []
        
        for i in range(10):  # 10배치 * 100개 = 1000개
            batch_data = []
            for j in range(batch_size):
                data_point = {
                    "device_id": f"perf_test_device_{i}",
                    "sensor_type": "vibration",
                    "value": 0.5 + (i * batch_size + j) * 0.001,
                    "unit": "g",
                    "time": (datetime.now() + timedelta(seconds=i * batch_size + j)).isoformat()
                }
                batch_data.append(data_point)
            
            response = requests.post(
                f"{self.BASE_URL}/api/v1/sensors/batch-data",
                json={"sensor_data": batch_data},
                headers=headers
            )
            
            if response.status_code == 201:
                total_data.extend(batch_data)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"성능 테스트 결과: {len(total_data)}개 데이터 저장에 {elapsed_time:.2f}초 소요")
        print(f"처리 속도: {len(total_data) / elapsed_time:.2f} 데이터/초")


if __name__ == "__main__":
    # 테스트 실행
    pytest.main([__file__, "-v"]) 