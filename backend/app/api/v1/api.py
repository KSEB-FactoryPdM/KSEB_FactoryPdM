"""
API v1 라우터
"""
from fastapi import APIRouter

from app.api.v1.endpoints import devices, sensors, anomalies, rul, auth, notifications, equipment, serve_ml, alerts, realtime, maintenance, rul_lite

api_router = APIRouter()

# 엔드포인트 라우터 등록
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["sensors"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(rul.router, prefix="/rul", tags=["rul"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(equipment.router, prefix="/equipment", tags=["equipment"]) 
api_router.include_router(serve_ml.router, prefix="/serve-ml", tags=["serve-ml"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"]) 
api_router.include_router(realtime.router, prefix="", tags=["realtime"]) 
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"]) 
api_router.include_router(rul_lite.router, prefix="/rul", tags=["rul-lite"])