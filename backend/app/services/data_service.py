"""
데이터 수집 및 관리 서비스
"""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
from pathlib import Path

from app.core.database import get_timescale_engine
from app.models.device import Device
from app.schemas.sensor import SensorDataCreate
from app.core.monitoring import record_sensor_data

logger = logging.getLogger(__name__)


class DataService:
    """데이터 수집 및 관리 서비스"""
    
    def __init__(self):
        self.backup_dir = Path("./data_backup")
        self.backup_dir.mkdir(exist_ok=True)
        self.failed_data_file = self.backup_dir / "failed_data.jsonl"
        self.collection_log_file = self.backup_dir / "collection_log.db"
        self._init_collection_log()
    
    def _init_collection_log(self):
        """수집 로그 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.collection_log_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_collection_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sensor_id VARCHAR(50) NOT NULL,
                    device_id VARCHAR(50) NOT NULL,
                    collection_interval INTEGER NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_collection_time TIMESTAMP,
                    last_success_time TIMESTAMP,
                    last_failure_time TIMESTAMP,
                    failure_rate REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("센서 수집 로그 데이터베이스 초기화 완료")
            
        except Exception as e:
            logger.error(f"센서 수집 로그 초기화 실패: {e}")
    
    def save_sensor_data_with_backup(self, sensor_data: SensorDataCreate) -> bool:
        """센서 데이터 저장 (백업 포함)"""
        try:
            # 1차 저장 시도 (TimescaleDB)
            success = self._save_to_timescaledb(sensor_data)
            
            if success:
                # 성공 시 로그 업데이트
                self._update_collection_log(sensor_data.device_id, sensor_data.sensor_type, True)
                record_sensor_data(sensor_data.device_id, sensor_data.sensor_type)
                return True
            else:
                # 실패 시 백업 저장
                self._save_to_backup(sensor_data)
                self._update_collection_log(sensor_data.device_id, sensor_data.sensor_type, False)
                return False
                
        except Exception as e:
            logger.error(f"센서 데이터 저장 중 오류: {e}")
            self._save_to_backup(sensor_data)
            self._update_collection_log(sensor_data.device_id, sensor_data.sensor_type, False)
            return False
    
    def _save_to_timescaledb(self, sensor_data: SensorDataCreate) -> bool:
        """TimescaleDB에 데이터 저장"""
        try:
            from sqlalchemy import text
            
            engine = get_timescale_engine()
            with engine.connect() as conn:
                query = text("""
                    INSERT INTO sensor_data (time, device_id, sensor_type, value, unit)
                    VALUES (:time, :device_id, :sensor_type, :value, :unit)
                """)
                
                conn.execute(query, {
                    "time": sensor_data.time,
                    "device_id": sensor_data.device_id,
                    "sensor_type": sensor_data.sensor_type,
                    "value": sensor_data.value,
                    "unit": sensor_data.unit
                })
                conn.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"TimescaleDB 저장 실패: {e}")
            return False
    
    def _save_to_backup(self, sensor_data: SensorDataCreate):
        """백업 파일에 데이터 저장"""
        try:
            backup_data = {
                "time": sensor_data.time.isoformat(),
                "device_id": sensor_data.device_id,
                "sensor_type": sensor_data.sensor_type,
                "value": sensor_data.value,
                "unit": sensor_data.unit,
                "backup_time": datetime.now().isoformat()
            }
            
            with open(self.failed_data_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(backup_data, ensure_ascii=False) + "\n")
            
            logger.info(f"센서 데이터 백업 저장: {sensor_data.device_id}")
            
        except Exception as e:
            logger.error(f"백업 저장 실패: {e}")
    
    def retry_failed_data(self) -> int:
        """실패한 데이터 재시도"""
        try:
            if not self.failed_data_file.exists():
                return 0
            
            retry_count = 0
            temp_file = self.failed_data_file.with_suffix(".tmp")
            
            with open(self.failed_data_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        backup_data = json.loads(line.strip())
                        
                        # SensorDataCreate 객체로 변환
                        sensor_data = SensorDataCreate(
                            device_id=backup_data["device_id"],
                            sensor_type=backup_data["sensor_type"],
                            value=backup_data["value"],
                            unit=backup_data["unit"],
                            time=datetime.fromisoformat(backup_data["time"])
                        )
                        
                        # 재시도
                        success = self._save_to_timescaledb(sensor_data)
                        
                        if success:
                            retry_count += 1
                            logger.info(f"실패 데이터 재시도 성공: {sensor_data.device_id}")
                        else:
                            # 실패한 데이터는 임시 파일에 다시 저장
                            with open(temp_file, "a", encoding="utf-8") as tf:
                                tf.write(line)
                    
                    except Exception as e:
                        logger.error(f"실패 데이터 재시도 중 오류: {e}")
                        # 오류가 있는 데이터는 임시 파일에 저장
                        with open(temp_file, "a", encoding="utf-8") as tf:
                            tf.write(line)
            
            # 임시 파일로 교체
            if temp_file.exists():
                self.failed_data_file.unlink()
                temp_file.rename(self.failed_data_file)
            
            logger.info(f"실패 데이터 재시도 완료: {retry_count}개 성공")
            return retry_count
            
        except Exception as e:
            logger.error(f"실패 데이터 재시도 중 오류: {e}")
            return 0
    
    def _update_collection_log(self, device_id: str, sensor_type: str, success: bool):
        """수집 로그 업데이트"""
        try:
            conn = sqlite3.connect(self.collection_log_file)
            cursor = conn.cursor()
            
            sensor_id = f"{device_id}_{sensor_type}"
            now = datetime.now()
            
            # 기존 로그 확인
            cursor.execute("""
                SELECT success_count, failure_count, last_collection_time, last_success_time, last_failure_time
                FROM sensor_collection_log 
                WHERE sensor_id = ?
            """, (sensor_id,))
            
            result = cursor.fetchone()
            
            if result:
                # 기존 로그 업데이트
                success_count, failure_count, last_collection, last_success, last_failure = result
                
                if success:
                    success_count += 1
                    last_success = now
                else:
                    failure_count += 1
                    last_failure = now
                
                total_count = success_count + failure_count
                failure_rate = failure_count / total_count if total_count > 0 else 0.0
                
                cursor.execute("""
                    UPDATE sensor_collection_log 
                    SET success_count = ?, failure_count = ?, last_collection_time = ?, 
                        last_success_time = ?, last_failure_time = ?, failure_rate = ?, updated_at = ?
                    WHERE sensor_id = ?
                """, (success_count, failure_count, now, last_success, last_failure, failure_rate, now, sensor_id))
            else:
                # 새 로그 생성
                if success:
                    success_count, failure_count = 1, 0
                    last_success, last_failure = now, None
                else:
                    success_count, failure_count = 0, 1
                    last_success, last_failure = None, now
                
                failure_rate = failure_count / (success_count + failure_count)
                
                cursor.execute("""
                    INSERT INTO sensor_collection_log 
                    (sensor_id, device_id, collection_interval, success_count, failure_count,
                     last_collection_time, last_success_time, last_failure_time, failure_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sensor_id, device_id, 60, success_count, failure_count, 
                      now, last_success, last_failure, failure_rate))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"수집 로그 업데이트 실패: {e}")
    
    def get_active_devices(self) -> List[Device]:
        """활성 장비 목록 조회"""
        try:
            from sqlalchemy.orm import Session
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            devices = db.query(Device).filter(Device.status == "active").all()
            db.close()
            
            return devices
            
        except Exception as e:
            logger.error(f"활성 장비 조회 실패: {e}")
            return []
    
    def get_sensor_data_for_training(self, device_id: str, start_date: datetime, end_date: datetime) -> List[dict]:
        """훈련용 센서 데이터 조회"""
        try:
            from sqlalchemy import text
            
            engine = get_timescale_engine()
            with engine.connect() as conn:
                query = text("""
                    SELECT time, device_id, sensor_type, value, unit
                    FROM sensor_data
                    WHERE device_id = :device_id 
                    AND time BETWEEN :start_date AND :end_date
                    ORDER BY time
                """)
                
                result = conn.execute(query, {
                    "device_id": device_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                sensor_data = []
                for row in result:
                    sensor_data.append({
                        "time": row.time,
                        "device_id": row.device_id,
                        "sensor_type": row.sensor_type,
                        "value": row.value,
                        "unit": row.unit
                    })
                
                return sensor_data
                
        except Exception as e:
            logger.error(f"훈련용 센서 데이터 조회 실패: {e}")
            return []
    
    def get_sensor_data_for_validation(self, device_id: str, start_date: datetime, end_date: datetime) -> List[dict]:
        """검증용 센서 데이터 조회"""
        return self.get_sensor_data_for_training(device_id, start_date, end_date)
    
    def get_sensor_data_for_drift_check(self, device_id: str, start_date: datetime, end_date: datetime) -> List[dict]:
        """드리프트 검사용 센서 데이터 조회"""
        return self.get_sensor_data_for_training(device_id, start_date, end_date)
    
    def get_collection_statistics(self, device_id: Optional[str] = None) -> Dict:
        """수집 통계 조회"""
        try:
            conn = sqlite3.connect(self.collection_log_file)
            cursor = conn.cursor()
            
            if device_id:
                cursor.execute("""
                    SELECT sensor_id, success_count, failure_count, failure_rate, last_collection_time
                    FROM sensor_collection_log 
                    WHERE device_id = ?
                    ORDER BY last_collection_time DESC
                """, (device_id,))
            else:
                cursor.execute("""
                    SELECT sensor_id, success_count, failure_count, failure_rate, last_collection_time
                    FROM sensor_collection_log 
                    ORDER BY last_collection_time DESC
                """)
            
            results = cursor.fetchall()
            conn.close()
            
            statistics = {
                "total_sensors": len(results),
                "total_success": sum(r[1] for r in results),
                "total_failure": sum(r[2] for r in results),
                "average_failure_rate": sum(r[3] for r in results) / len(results) if results else 0.0,
                "sensors": [
                    {
                        "sensor_id": r[0],
                        "success_count": r[1],
                        "failure_count": r[2],
                        "failure_rate": r[3],
                        "last_collection": r[4]
                    }
                    for r in results
                ]
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"수집 통계 조회 실패: {e}")
            return {}


# 전역 데이터 서비스 인스턴스
data_service = DataService() 