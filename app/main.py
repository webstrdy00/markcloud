from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

from .config import settings
from .database import Base, engine, test_connection
from .routers import trademark
from .exceptions import register_exception_handlers

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 테스트
logger.info("애플리케이션 시작: 데이터베이스 연결 테스트 중...")
db_connected = test_connection()
if not db_connected:
    logger.warning("데이터베이스 연결에 실패했습니다. 일부 기능이 작동하지 않을 수 있습니다.")
else:
    logger.info("데이터베이스 연결이 정상적으로 확인되었습니다.")

try:
    # DB 테이블 생성
    logger.info("데이터베이스 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    logger.info("데이터베이스 테이블 생성 완료")
except Exception as e:
    logger.error(f"데이터베이스 테이블 생성 실패: {str(e)}")

app = FastAPI(
    title=settings.APP_NAME,
    description="상표 데이터를 검색하고 필터링하는 API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 전역 예외 핸들러 등록
register_exception_handlers(app)

# CORS 설정
logger.info(f"CORS 허용 도메인: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Set-Cookie"],
    expose_headers=["Authorization", "Set-Cookie"],
    max_age=3600,  # preflight 요청 캐싱 시간(초)
)

# 라우터 등록
app.include_router(trademark.router, prefix="/api/v1")

@app.get("/")
def read_root():
    """루트 엔드포인트"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_url": settings.API_PREFIX
    }

@app.get("/health")
def health_check():
    """서버 상태 확인 엔드포인트"""
    # 데이터베이스 연결 상태 확인
    db_status = "connected" if test_connection() else "disconnected"
    return {
        "status": "ok", 
        "message": "서버가 정상적으로 실행 중입니다.",
        "database": db_status,
        "environment": settings.ENVIRONMENT
    }