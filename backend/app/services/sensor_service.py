"""
센서 데이터 관리 서비스
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import logging
from datetime import datetime
import time

from app.schemas.sensor import SensorDataCreate, SensorDataResponse, SensorDataQuery
from app.core.database import get_timescale_engine
from app.core.monitoring import record_sensor_data, record_database_query

logger = logging.getLogger(__name__)


class SensorService:
    """센서 데이터 관리 서비스"""
    
    @staticmethod
    def save_sensor_data(db: Session, sensor_data: SensorDataCreate) -> bool:
        """센서 데이터 저장"""
        try:
            start_time = time.time()
            
            # TimescaleDB에 데이터 저장
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
            
            # 메트릭 기록
            record_sensor_data(sensor_data.device_id, sensor_data.sensor_type)
            record_database_query("insert_sensor_data", time.time() - start_time)
            
            logger.debug(f"센서 데이터 저장 완료: {sensor_data.device_id} - {sensor_data.sensor_type}")
            return True
            
        except Exception as e:
            logger.error(f"센서 데이터 저장 실패: {e}")
            raise
    
    @staticmethod
    def save_sensor_data_batch(db: Session, device_id: str, sensor_data_list: List[SensorDataCreate]) -> bool:
        """센서 데이터 배치 저장"""
        try:
            start_time = time.time()
            
            engine = get_timescale_engine()
            with engine.connect() as conn:
                # 배치 삽입을 위한 데이터 준비
                data_to_insert = []
                for sensor_data in sensor_data_list:
                    data_to_insert.append({
                        "time": sensor_data.time,
                        "device_id": device_id,
                        "sensor_type": sensor_data.sensor_type,
                        "value": sensor_data.value,
                        "unit": sensor_data.unit
                    })
                
                # 배치 삽입
                query = text("""
                    INSERT INTO sensor_data (time, device_id, sensor_type, value, unit)
                    VALUES (:time, :device_id, :sensor_type, :value, :unit)
                """)
                
                conn.execute(query, data_to_insert)
                conn.commit()
            
            # 메트릭 기록
            for sensor_data in sensor_data_list:
                record_sensor_data(device_id, sensor_data.sensor_type)
            record_database_query("batch_insert_sensor_data", time.time() - start_time)
            
            logger.info(f"센서 데이터 배치 저장 완료: {device_id} - {len(sensor_data_list)}개")
            return True
            
        except Exception as e:
            logger.error(f"센서 데이터 배치 저장 실패: {e}")
            raise
    
    @staticmethod
    def get_sensor_data(query: SensorDataQuery) -> List[SensorDataResponse]:
        """센서 데이터 조회"""
        try:
            start_time = time.time()
            
            engine = get_timescale_engine()
            with engine.connect() as conn:
                # 기본 쿼리
                sql_query = """
                    SELECT time, device_id, sensor_type, value, unit, created_at
                    FROM sensor_data
                    WHERE device_id = :device_id
                """
                params = {"device_id": query.device_id}
                
                # 센서 타입 필터
                if query.sensor_type:
                    sql_query += " AND sensor_type = :sensor_type"
                    params["sensor_type"] = query.sensor_type
                
                # 시간 범위 필터
                if query.start_time:
                    sql_query += " AND time >= :start_time"
                    params["start_time"] = query.start_time
                
                if query.end_time:
                    sql_query += " AND time <= :end_time"
                    params["end_time"] = query.end_time
                
                # 정렬 및 제한
                sql_query += " ORDER BY time DESC LIMIT :limit OFFSET :offset"
                params["limit"] = query.limit
                params["offset"] = query.offset
                
                result = conn.execute(text(sql_query), params)
                
                # 결과 변환
                sensor_data_list = []
                for row in result:
                    sensor_data = SensorDataResponse(
                        time=row.time,
                        device_id=row.device_id,
                        sensor_type=row.sensor_type,
                        value=row.value,
                        unit=row.unit,
                        created_at=row.created_at
                    )
                    sensor_data_list.append(sensor_data)
            
            record_database_query("select_sensor_data", time.time() - start_time)
            
            logger.debug(f"센서 데이터 조회 완료: {query.device_id} - {len(sensor_data_list)}개")
            return sensor_data_list
            
        except Exception as e:
            logger.error(f"센서 데이터 조회 실패: {e}")
            raise
    
    @staticmethod
    def get_latest_sensor_data(device_id: str, sensor_type: Optional[str] = None) -> Optional[SensorDataResponse]:
        """최신 센서 데이터 조회"""
        try:
            engine = get_timescale_engine()
            with engine.connect() as conn:
                sql_query = """
                    SELECT time, device_id, sensor_type, value, unit, created_at
                    FROM sensor_data
                    WHERE device_id = :device_id
                """
                params = {"device_id": device_id}
                
                if sensor_type:
                    sql_query += " AND sensor_type = :sensor_type"
                    params["sensor_type"] = sensor_type
                
                sql_query += " ORDER BY time DESC LIMIT 1"
                
                result = conn.execute(text(sql_query), params)
                row = result.fetchone()
                
                if row:
                    return SensorDataResponse(
                        time=row.time,
                        device_id=row.device_id,
                        sensor_type=row.sensor_type,
                        value=row.value,
                        unit=row.unit,
                        created_at=row.created_at
                    )
                return None
                
        except Exception as e:
            logger.error(f"최신 센서 데이터 조회 실패: {e}")
            raise
    
    @staticmethod
    def get_sensor_data_count(device_id: str, sensor_type: Optional[str] = None) -> int:
        """센서 데이터 개수 조회"""
        try:
            engine = get_timescale_engine()
            with engine.connect() as conn:
                sql_query = "SELECT COUNT(*) FROM sensor_data WHERE device_id = :device_id"
                params = {"device_id": device_id}
                
                if sensor_type:
                    sql_query += " AND sensor_type = :sensor_type"
                    params["sensor_type"] = sensor_type
                
                result = conn.execute(text(sql_query), params)
                return result.scalar()
                
        except Exception as e:
            logger.error(f"센서 데이터 개수 조회 실패: {e}")
            raise 