"""
serve_ml 기반 추론/상태 API
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy import text

from app.services.serve_ml_loader import serve_ml_registry
from app.core.database import get_timescale_engine


router = APIRouter()


class ServeMLPredictRequest(BaseModel):
    equipment_id: str = Field(..., description="장비 ID (serve_ml/<equipment_id>/...)")
    power: Optional[str] = Field(None, description="전력 버킷 (예: 15kW). 미지정 시 자동 선택")
    model_version: Optional[str] = Field(None, description="모델 버전 디렉토리명. 미지정 시 최신 사용")
    features: Dict[str, Any] = Field(..., description="feature_spec.yaml에 정의된 키-값 쌍")


@router.post("/predict")
async def serve_ml_predict(req: ServeMLPredictRequest):
    try:
        # power 자동 선택 레이어 (요청에 power 생략 시)
        selected_power = req.power
        if selected_power is None:
            try:
                selected_power = serve_ml_registry.select_power_by_rule(req.equipment_id, req.features)
            except Exception:
                selected_power = None

        bundle = serve_ml_registry.resolve_bundle(req.equipment_id, selected_power, req.model_version)
        result = bundle.infer(req.features)

        # 결과 저장 (Timescale)
        engine = get_timescale_engine()
        with engine.connect() as conn:
            query = text(
                """
                INSERT INTO serve_ml_predictions (
                    time, equipment_id, power, model_version,
                    is_anomaly, confidence, scores, thresholds, modalities,
                    features, bundle_path
                ) VALUES (
                    :time, :equipment_id, :power, :model_version,
                    :is_anomaly, :confidence, CAST(:scores AS JSONB), CAST(:thresholds AS JSONB), CAST(:modalities AS JSONB),
                    CAST(:features AS JSONB), :bundle_path
                )
                """
            )
            import json as _json
            payload = {
                "time": datetime.utcnow(),
                "equipment_id": req.equipment_id,
                "power": selected_power or "auto",
                "model_version": req.model_version or bundle.bundle_dir.name,
                "is_anomaly": result["is_anomaly"],
                "confidence": float(result.get("confidence", 0.0)),
                "scores": _json.dumps(result.get("scores")),
                "thresholds": _json.dumps(result.get("thresholds")),
                "modalities": _json.dumps(result.get("modalities")),
                "features": _json.dumps(result.get("used_features")),
                "bundle_path": str(bundle.bundle_dir),
            }
            conn.execute(query, payload)
            conn.commit()

        return {
            "equipment_id": req.equipment_id,
            "power": selected_power or "auto",
            "model_version": req.model_version or bundle.bundle_dir.name,
            "result": result,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서빙 오류: {e}")


@router.get("/bundles")
async def list_bundles(equipment_id: Optional[str] = Query(None), power: Optional[str] = Query(None)):
    try:
        if equipment_id is None:
            return {"equipment": serve_ml_registry.list_equipment()}
        if power is None:
            return {"powers": serve_ml_registry.list_powers(equipment_id)}
        return {"versions": serve_ml_registry.list_versions(equipment_id, power)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"목록 조회 오류: {e}")


@router.post("/sync")
async def sync_registry():
    try:
        count = serve_ml_registry.sync_to_db()
        return {"upserts": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"동기화 실패: {e}")


