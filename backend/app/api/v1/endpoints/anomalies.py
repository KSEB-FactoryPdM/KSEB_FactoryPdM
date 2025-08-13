"""
이상 탐지 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import numpy as np
import os
import tempfile
import shutil

from app.core.database import get_db, get_timescale_engine
from sqlalchemy import text
from app.ml.anomaly_detection import anomaly_model
from app.schemas.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyQuery,
    ModelTrainingRequest,
    ModelTrainingResponse
)
from app.core.monitoring import record_anomaly_detection
from app.services.notification_service import notification_service
from app.services.equipment_service import equipment_service

router = APIRouter()


@router.post("/detect", response_model=AnomalyDetectionResponse)
async def detect_anomaly(
    request: AnomalyDetectionRequest
):
    """실시간 이상 탐지"""
    try:
        start_time = datetime.now()
        
        # 센서 데이터를 numpy 배열로 변환
        sensor_values = []
        for data_point in request.sensor_data:
            # 진동, 온도, 전류 데이터 추출
            vibration = data_point.get('vibration', {}).get('value', 0)
            temperature = data_point.get('temperature', {}).get('value', 0)
            current = data_point.get('current', {}).get('value', 0)
            
            sensor_values.append([vibration, temperature, current])
        
        if not sensor_values:
            raise HTTPException(status_code=400, detail="센서 데이터가 없습니다")
        
        # 최신 데이터만 사용 (마지막 데이터 포인트)
        latest_data = np.array(sensor_values[-1])
        
        # 이상 탐지 수행
        is_anomaly, anomaly_score, model_results = anomaly_model.detect_anomaly_ensemble(latest_data)
        
        # 심각도 결정
        severity = "low"
        if anomaly_score > 0.8:
            severity = "critical"
        elif anomaly_score > 0.6:
            severity = "high"
        elif anomaly_score > 0.4:
            severity = "medium"
        
        # 이상 유형 결정 (예시)
        anomaly_type = None
        if is_anomaly:
            if latest_data[0] > 10:  # 진동이 높은 경우
                anomaly_type = "vibration_anomaly"
            elif latest_data[1] > 80:  # 온도가 높은 경우
                anomaly_type = "temperature_anomaly"
            elif latest_data[2] > 100:  # 전류가 높은 경우
                anomaly_type = "current_anomaly"
            else:
                anomaly_type = "general_anomaly"
        
        # 신뢰도 계산 (모델 결과 기반)
        confidence = 0.8  # 예시 값, 실제로는 모델 결과에서 계산
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 메트릭 기록
        record_anomaly_detection(request.device_id, severity)
        
        # 이상 탐지 시 알림 생성
        if is_anomaly:
            try:
                # 장비 및 센서 메타데이터 조회
                equipment = equipment_service.get_equipment(db, request.device_id)
                sensor = equipment_service.get_sensor(db, request.sensor_data[0].get('sensor_id', 'unknown'))
                
                # 알림 메시지 생성
                alert_type = "critical" if severity in ["critical", "high"] else "warning"
                device_name = equipment.name if equipment else request.device_id
                sensor_name = sensor.name if sensor else "unknown"
                
                message = f"{device_name} 장비에서 {anomaly_type} 이상이 탐지되었습니다. 심각도: {severity}"
                
                # 알림 생성
                notification_service.create_notification(
                    db=db,
                    device_id=request.device_id,
                    sensor_id=request.sensor_data[0].get('sensor_id', 'unknown'),
                    alert_type=alert_type,
                    anomaly_type=anomaly_type or "unknown",
                    severity=severity,
                    message=message,
                    sensor_value=float(latest_data[0]) if len(latest_data) > 0 else None,
                    threshold_value=None  # 실제 구현에서는 임계값 설정 필요
                )
            except Exception as e:
                # 알림 생성 실패 시에도 이상 탐지 결과는 반환
                print(f"알림 생성 실패: {e}")
        
        return AnomalyDetectionResponse(
            device_id=request.device_id,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            anomaly_type=anomaly_type,
            severity=severity,
            confidence=confidence,
            detected_at=datetime.now(),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이상 탐지 실패: {str(e)}")


@router.get("/events", response_model=dict)
async def get_anomaly_events(
    device_id: Optional[str] = Query(default=None, description="장비 ID"),
    severity: Optional[str] = Query(default=None, description="심각도"),
    start_time: Optional[datetime] = Query(default=None, description="시작 시간"),
    end_time: Optional[datetime] = Query(default=None, description="종료 시간"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    size: int = Query(default=50, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db)
):
    """이상 이벤트 조회"""
    try:
        engine = get_timescale_engine()
        conditions = []
        params = {}
        if device_id:
            conditions.append("equipment_id = :device_id")
            params["device_id"] = device_id
        # serve_ml_predictions 테이블에는 severity 컬럼이 없으므로 필터 제외
        if start_time:
            conditions.append("time >= :start_time")
            params["start_time"] = start_time
        if end_time:
            conditions.append("time <= :end_time")
            params["end_time"] = end_time

        where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"""
            SELECT time AS event_time, equipment_id AS device_id, is_anomaly, confidence,
                   scores, thresholds, modalities
            FROM serve_ml_predictions
            {where_sql}
            ORDER BY time DESC
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = size
        params["offset"] = (page - 1) * size
        with engine.connect() as conn:
            result = conn.execute(text(sql), params)
            cols = result.keys()
            rows = [dict(zip(cols, r)) for r in result.fetchall()]
        return {"events": rows, "total": len(rows), "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이상 이벤트 조회 실패: {str(e)}")


@router.get("/stats")
async def get_anomaly_stats(
    device_id: Optional[str] = Query(default=None, description="장비 ID"),
    start_time: Optional[datetime] = Query(default=None, description="시작 시간"),
    end_time: Optional[datetime] = Query(default=None, description="종료 시간"),
    db: Session = Depends(get_db)
):
    """이상 탐지 통계"""
    try:
        # 실제 구현에서는 데이터베이스에서 통계를 계산
        # 여기서는 예시 응답을 반환
        return {
            "total_anomalies": 0,
            "critical_anomalies": 0,
            "high_anomalies": 0,
            "medium_anomalies": 0,
            "low_anomalies": 0,
            "anomaly_rate": 0.0,
            "message": "이상 탐지 통계 기능은 구현 예정입니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이상 탐지 통계 조회 실패: {str(e)}")


@router.post("/train-with-data", response_model=ModelTrainingResponse)
async def train_model_with_sensor_data(
    request: ModelTrainingRequest,
    db: Session = Depends(get_db)
):
    """센서 데이터를 사용한 모델 훈련"""
    try:
        logger.info(f"센서 데이터 기반 모델 훈련 시작: {request.device_id}")
        
        # 데이터 파일 경로 검증
        if not request.normal_current_files or not request.normal_vibration_files:
            raise HTTPException(status_code=400, detail="정상 데이터 파일이 필요합니다")
        
        if not request.abnormal_current_files or not request.abnormal_vibration_files:
            raise HTTPException(status_code=400, detail="이상 데이터 파일이 필요합니다")
        
        # 파일 존재 여부 확인
        all_files = (request.normal_current_files + request.normal_vibration_files + 
                    request.abnormal_current_files + request.abnormal_vibration_files)
        
        for file_path in all_files:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=400, detail=f"파일을 찾을 수 없습니다: {file_path}")
        
        # 모델 훈련 수행
        training_results = anomaly_model.train_with_sensor_data(
            normal_current_files=request.normal_current_files,
            normal_vibration_files=request.normal_vibration_files,
            abnormal_current_files=request.abnormal_current_files,
            abnormal_vibration_files=request.abnormal_vibration_files
        )
        
        return ModelTrainingResponse(
            device_id=request.device_id,
            model_type=request.model_type,
            status="completed",
            accuracy=training_results.get('accuracy', 0.0),
            precision=training_results.get('precision', 0.0),
            recall=training_results.get('recall', 0.0),
            f1_score=training_results.get('f1_score', 0.0),
            training_time=training_results.get('training_time', 0.0),
            message="모델 훈련이 성공적으로 완료되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"모델 훈련 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 훈련 실패: {str(e)}")


@router.post("/upload-and-train")
async def upload_and_train_model(
    device_id: str = Query(..., description="장비 ID"),
    model_type: str = Query(default="xgboost", description="모델 유형"),
    normal_current_files: List[UploadFile] = File(..., description="정상 전류 데이터 파일"),
    normal_vibration_files: List[UploadFile] = File(..., description="정상 진동 데이터 파일"),
    abnormal_current_files: List[UploadFile] = File(..., description="이상 전류 데이터 파일"),
    abnormal_vibration_files: List[UploadFile] = File(..., description="이상 진동 데이터 파일"),
    db: Session = Depends(get_db)
):
    """파일 업로드 및 모델 훈련"""
    try:
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 파일 저장 경로
            normal_current_paths = []
            normal_vibration_paths = []
            abnormal_current_paths = []
            abnormal_vibration_paths = []
            
            # 정상 전류 파일 저장
            for i, file in enumerate(normal_current_files):
                file_path = os.path.join(temp_dir, f"normal_current_{i}.csv")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                normal_current_paths.append(file_path)
            
            # 정상 진동 파일 저장
            for i, file in enumerate(normal_vibration_files):
                file_path = os.path.join(temp_dir, f"normal_vibration_{i}.csv")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                normal_vibration_paths.append(file_path)
            
            # 이상 전류 파일 저장
            for i, file in enumerate(abnormal_current_files):
                file_path = os.path.join(temp_dir, f"abnormal_current_{i}.csv")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                abnormal_current_paths.append(file_path)
            
            # 이상 진동 파일 저장
            for i, file in enumerate(abnormal_vibration_files):
                file_path = os.path.join(temp_dir, f"abnormal_vibration_{i}.csv")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                abnormal_vibration_paths.append(file_path)
            
            # 모델 훈련 수행
            training_results = anomaly_model.train_with_sensor_data(
                normal_current_files=normal_current_paths,
                normal_vibration_files=normal_vibration_paths,
                abnormal_current_files=abnormal_current_paths,
                abnormal_vibration_files=abnormal_vibration_paths
            )
            
            return {
                "device_id": device_id,
                "model_type": model_type,
                "status": "completed",
                "accuracy": training_results.get('accuracy', 0.0),
                "precision": training_results.get('precision', 0.0),
                "recall": training_results.get('recall', 0.0),
                "f1_score": training_results.get('f1_score', 0.0),
                "message": "파일 업로드 및 모델 훈련이 성공적으로 완료되었습니다"
            }
            
        finally:
            # 임시 디렉토리 정리
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"파일 업로드 및 모델 훈련 실패: {e}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 및 모델 훈련 실패: {str(e)}")


@router.get("/model-performance")
async def get_model_performance(
    device_id: str = Query(..., description="장비 ID"),
    db: Session = Depends(get_db)
):
    """모델 성능 조회"""
    try:
        # 실제 구현에서는 데이터베이스에서 모델 성능 정보를 조회
        # 여기서는 예시 응답을 반환
        return {
            "device_id": device_id,
            "model_type": "xgboost",
            "accuracy": 0.95,
            "precision": 0.94,
            "recall": 0.96,
            "f1_score": 0.95,
            "last_training": "2024-01-15T10:30:00Z",
            "total_predictions": 1000,
            "anomaly_detections": 50,
            "message": "모델 성능 정보"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모델 성능 조회 실패: {str(e)}") 