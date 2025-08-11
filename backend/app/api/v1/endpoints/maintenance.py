"""
정비(maintenance) 목록 조회 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db, get_timescale_engine


router = APIRouter()


@router.get("/", response_model=dict)
async def list_maintenance(
    device_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    start_time: Optional[str] = Query(default=None),
    end_time: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=1000),
):
    try:
        engine = get_timescale_engine()
        conditions = []
        params = {}
        if device_id:
            conditions.append("device_id = :device_id")
            params["device_id"] = device_id
        if status:
            conditions.append("status = :status")
            params["status"] = status
        if start_time:
            conditions.append("requested_at >= :start_time")
            params["start_time"] = start_time
        if end_time:
            conditions.append("requested_at <= :end_time")
            params["end_time"] = end_time
        where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sql = f"""
            SELECT id, device_id, requested_at, status, reason
            FROM maintenance_requests
            {where_sql}
            ORDER BY requested_at DESC
            LIMIT :limit OFFSET :offset
        """
        params["limit"] = size
        params["offset"] = (page - 1) * size
        with engine.connect() as conn:
            rows = [dict(r) for r in conn.execute(text(sql), params)]
        return {"items": rows, "total": len(rows), "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"정비 목록 조회 실패: {e}")


