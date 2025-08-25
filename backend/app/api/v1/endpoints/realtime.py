"""
실시간 WebSocket 엔드포인트 (/ws/stream, /ws/devices/{id})
프론트의 Monitoring 및 Device 상세 페이지에서 소비할 형식으로 전송
"""
import asyncio
import json
import time
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import text

from app.core.database import get_timescale_engine


router = APIRouter()


@router.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        engine = get_timescale_engine()
        while True:
            now_ts = int(time.time())
            total = 0
            size50 = 0.0
            size90 = 0.0
            size99 = 0.0
            try:
                with engine.connect() as conn:
                    total_sql = text(
                        """
                        SELECT COUNT(*)::int AS total
                        FROM serve_ml_predictions
                        WHERE time >= NOW() - INTERVAL '10 seconds' AND is_anomaly = TRUE
                        """
                    )
                    total = conn.execute(total_sql).scalar() or 0

                    avg_sql = text(
                        """
                        SELECT AVG(value) as avg_val
                        FROM sensor_data
                        WHERE time >= NOW() - INTERVAL '10 seconds'
                        """
                    )
                    avg_val = conn.execute(avg_sql).scalar()
                    if avg_val is not None:
                        size50 = float(avg_val)
                        size90 = float(avg_val)
                        size99 = float(avg_val)
            except Exception:
                # DB 오류 시 기본값 유지
                pass

            point = {
                "time": now_ts,
                "total": total,
                "A": 0,
                "AAAA": 0,
                "PTR": 0,
                "SOA": 0,
                "SRV": 0,
                "TXT": 0,
                "zone1": 0,
                "zone2": 0,
                "zone3": 0,
                "rul": 0,
                "size50": size50,
                "size90": size90,
                "size99": size99,
            }
            await websocket.send_text(json.dumps([point]))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return


@router.websocket("/ws/devices/{device_id}")
async def ws_device_series(websocket: WebSocket, device_id: str):
    await websocket.accept()
    try:
        engine = get_timescale_engine()
        while True:
            rows: List[dict] = []
            try:
                with engine.connect() as conn:
                    sql = text(
                    """
                        SELECT EXTRACT(EPOCH FROM time)::int AS ts, value
                        FROM sensor_data
                        WHERE device = :device AND sensor_type = 'vibe'
                        ORDER BY time DESC
                        LIMIT 50
                        """
                    )
                    data = list(conn.execute(sql, {"device": device_id}))
                    # 최신이 먼저이므로 역순으로 정렬
                    data.reverse()
                    rows = [{"time": int(r[0]), "value": float(r[1])} for r in data]
            except Exception:
                rows = []
            await websocket.send_text(json.dumps(rows))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return


