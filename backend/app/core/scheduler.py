"""
자동 재학습 스케줄러
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import time
from threading import Thread

from app.core.config import settings
from app.services.model_service import ModelService
from app.services.data_service import DataService
from app.core.monitoring import record_model_training

logger = logging.getLogger(__name__)


class ModelScheduler:
    """모델 재학습 스케줄러"""
    
    def __init__(self):
        self.model_service = ModelService()
        self.data_service = DataService()
        self.is_running = False
        self.scheduler_thread = None
        
    def start_scheduler(self):
        """스케줄러 시작"""
        if self.is_running:
            logger.warning("스케줄러가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("모델 재학습 스케줄러가 시작되었습니다.")
    
    def stop_scheduler(self):
        """스케줄러 중지"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("모델 재학습 스케줄러가 중지되었습니다.")
    
    def _run_scheduler(self):
        """스케줄러 실행"""
        # 매주 일요일 새벽 2시에 재학습 수행
        schedule.every().sunday.at("02:00").do(self._retrain_models)
        
        # 매일 새벽 3시에 모델 성능 검증
        schedule.every().day.at("03:00").do(self._validate_models)
        
        # 매시간 모델 드리프트 검사
        schedule.every().hour.do(self._check_model_drift)
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 스케줄 확인
    
    def _retrain_models(self):
        """모델 재학습 수행"""
        try:
            logger.info("모델 재학습을 시작합니다.")
            
            # 최근 30일간의 데이터 수집
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # 각 장비별로 재학습 수행
            devices = self.data_service.get_active_devices()
            
            for device in devices:
                try:
                    # 센서 데이터 수집
                    sensor_data = self.data_service.get_sensor_data_for_training(
                        device_id=device.id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if len(sensor_data) < 1000:  # 최소 데이터 수 확인
                        logger.warning(f"장비 {device.id}의 데이터가 부족합니다: {len(sensor_data)}개")
                        continue
                    
                    # 이상 탐지 모델 재학습
                    anomaly_success = self.model_service.retrain_anomaly_model(
                        device_id=device.id,
                        sensor_data=sensor_data
                    )
                    
                    # RUL 예측 모델 재학습
                    rul_success = self.model_service.retrain_rul_model(
                        device_id=device.id,
                        sensor_data=sensor_data
                    )
                    
                    if anomaly_success and rul_success:
                        logger.info(f"장비 {device.id} 모델 재학습 완료")
                        record_model_training(device.id, "retrain", True)
                    else:
                        logger.error(f"장비 {device.id} 모델 재학습 실패")
                        record_model_training(device.id, "retrain", False)
                        
                except Exception as e:
                    logger.error(f"장비 {device.id} 재학습 중 오류: {e}")
                    record_model_training(device.id, "retrain", False)
            
            logger.info("모델 재학습이 완료되었습니다.")
            
        except Exception as e:
            logger.error(f"모델 재학습 중 오류: {e}")
    
    def _validate_models(self):
        """모델 성능 검증"""
        try:
            logger.info("모델 성능 검증을 시작합니다.")
            
            devices = self.data_service.get_active_devices()
            
            for device in devices:
                try:
                    # 최근 7일간의 데이터로 성능 검증
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=7)
                    
                    validation_data = self.data_service.get_sensor_data_for_validation(
                        device_id=device.id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if len(validation_data) < 100:
                        continue
                    
                    # 모델 성능 평가
                    anomaly_performance = self.model_service.evaluate_anomaly_model(
                        device_id=device.id,
                        test_data=validation_data
                    )
                    
                    rul_performance = self.model_service.evaluate_rul_model(
                        device_id=device.id,
                        test_data=validation_data
                    )
                    
                    # 성능 임계값 확인
                    if (anomaly_performance['accuracy'] < 0.8 or 
                        rul_performance['mae'] > 50):
                        logger.warning(f"장비 {device.id} 모델 성능 저하 감지")
                        self._trigger_emergency_retrain(device.id)
                    
                    logger.info(f"장비 {device.id} 성능 검증 완료")
                    
                except Exception as e:
                    logger.error(f"장비 {device.id} 성능 검증 중 오류: {e}")
            
        except Exception as e:
            logger.error(f"모델 성능 검증 중 오류: {e}")
    
    def _check_model_drift(self):
        """모델 드리프트 검사"""
        try:
            logger.info("모델 드리프트 검사를 시작합니다.")
            
            devices = self.data_service.get_active_devices()
            
            for device in devices:
                try:
                    # 최근 24시간 데이터로 드리프트 검사
                    end_date = datetime.now()
                    start_date = end_date - timedelta(hours=24)
                    
                    recent_data = self.data_service.get_sensor_data_for_drift_check(
                        device_id=device.id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if len(recent_data) < 50:
                        continue
                    
                    # 데이터 분포 변화 검사
                    drift_score = self.model_service.calculate_drift_score(
                        device_id=device.id,
                        recent_data=recent_data
                    )
                    
                    if drift_score > 0.3:  # 드리프트 임계값
                        logger.warning(f"장비 {device.id} 모델 드리프트 감지: {drift_score}")
                        self._trigger_emergency_retrain(device.id)
                    
                except Exception as e:
                    logger.error(f"장비 {device.id} 드리프트 검사 중 오류: {e}")
            
        except Exception as e:
            logger.error(f"모델 드리프트 검사 중 오류: {e}")
    
    def _trigger_emergency_retrain(self, device_id: str):
        """긴급 재학습 트리거"""
        try:
            logger.info(f"장비 {device_id} 긴급 재학습을 시작합니다.")
            
            # 최근 7일간의 데이터로 긴급 재학습
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            sensor_data = self.data_service.get_sensor_data_for_training(
                device_id=device_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if len(sensor_data) >= 500:
                self.model_service.emergency_retrain_models(
                    device_id=device_id,
                    sensor_data=sensor_data
                )
                logger.info(f"장비 {device_id} 긴급 재학습 완료")
            else:
                logger.warning(f"장비 {device_id} 긴급 재학습 데이터 부족")
                
        except Exception as e:
            logger.error(f"장비 {device_id} 긴급 재학습 중 오류: {e}")


# 전역 스케줄러 인스턴스
model_scheduler = ModelScheduler() 