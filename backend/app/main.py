"""
FastAPI 메인 애플리케이션
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.monitoring import setup_monitoring
from app.core.database import init_db
from app.core.scheduler import model_scheduler
from app.services.serve_ml_mqtt_infer import serve_ml_mqtt_infer


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("애플리케이션 시작 중...")
    
    # 모니터링 설정
    setup_monitoring()
    
    # 데이터베이스 초기화 (ORM 테이블 + Timescale hypertables)
    try:
        await init_db()
        logger.info("데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
    
    # 모델 스케줄러 시작
    try:
        model_scheduler.start_scheduler()
        logger.info("모델 재학습 스케줄러가 시작되었습니다.")
    except Exception as e:
        logger.error(f"스케줄러 시작 실패: {e}")

    # serve_ml MQTT 추론 리스너 시작
    try:
        serve_ml_mqtt_infer.start()
    except Exception as e:
        logger.error(f"serve_ml MQTT 리스너 시작 실패: {e}")
    
    yield
    
    # 종료 시 실행
    logger.info("애플리케이션 종료 중...")
    
    # 스케줄러 중지
    try:
        model_scheduler.stop_scheduler()
        logger.info("모델 재학습 스케줄러가 중지되었습니다.")
    except Exception as e:
        logger.error(f"스케줄러 중지 실패: {e}")

    # serve_ml MQTT 추론 리스너 중지
    try:
        serve_ml_mqtt_infer.stop()
    except Exception as e:
        logger.error(f"serve_ml MQTT 리스너 중지 실패: {e}")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="스마트팩토리용 설비 이상탐지 및 예지보전 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """요청 처리 시간 측정 미들웨어"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"전역 예외 발생: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "내부 서버 오류가 발생했습니다."}
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "스마트팩토리용 설비 이상탐지 및 예지보전 시스템 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 