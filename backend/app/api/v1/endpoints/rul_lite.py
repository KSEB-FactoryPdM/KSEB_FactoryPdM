"""
RUL-lite API

POST /rul/ingest  : 2초 주기 입력 수집(시뮬레이터/수집기)
GET  /rul/status  : 장비별 RUL% 폴링
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Optional

from app.services.rul_lite import get_engine


router = APIRouter()


class IngestRequest(BaseModel):
    equipment_id: str = Field(..., description="설비 ID")
    power: str = Field(..., description="전원/상태 키 (예: ON/OFF)")
    x: float = Field(..., description="가속도 X")
    y: float = Field(..., description="가속도 Y")
    z: float = Field(..., description="가속도 Z")
    vibe: float = Field(..., description="진동 스칼라")


@router.post("/ingest", response_model=Dict)
async def ingest_rul(req: IngestRequest):
    try:
        eng = get_engine()
        out = eng.step(req.equipment_id, req.power, req.x, req.y, req.z, req.vibe)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RUL-lite ingest 실패: {e}")


@router.get("/status", response_model=Dict)
async def get_status(
    equipment_id: str = Query(..., description="설비 ID"),
    power: str = Query(..., description="전원/상태 키 (예: ON/OFF)"),
):
    try:
        eng = get_engine()
        return eng.status(equipment_id, power)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RUL-lite status 실패: {e}")


