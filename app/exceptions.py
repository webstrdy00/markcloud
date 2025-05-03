from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from .config import settings

# 로거 설정
logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """모든 미처리 예외를 위한 전역 핸들러"""
    # 개발 환경에서는 상세 스택 추적을 로깅
    logger.exception("처리되지 않은 예외 발생:", exc_info=exc)
    
    # 요청 정보 로깅 (중요도 낮춤)
    logger.debug(f"URL: {request.url}, 메서드: {request.method}")
    
    # 사용자에게는 일관된 오류 응답 제공
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "서버 내부 오류가 발생했습니다.",
            "type": type(exc).__name__,
            # 개발 환경에서만 상세 오류 메시지 포함 (직접 settings import)
            "message": str(exc) if settings.DEBUG else "관리자에게 문의하세요.",
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 데이터 검증 오류를 위한 핸들러"""
    logger.warning(f"요청 데이터 검증 오류: {exc.errors()}")
    
    # 사용자 친화적인 오류 메시지 생성
    error_messages = []
    for error in exc.errors():
        location = " -> ".join(str(loc) for loc in error["loc"])
        error_messages.append(f"{location}: {error['msg']}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "요청 데이터 검증에 실패했습니다.",
            "errors": error_messages
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러 - 로깅 목적으로 추가"""
    # 서버 오류 (500 계열)의 경우만 ERROR 레벨로 로깅
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} 오류: {exc.detail}")
    # 클라이언트 오류 (400 계열)의 경우 INFO 레벨로 로깅
    else:
        logger.info(f"HTTP {exc.status_code} 오류: {exc.detail}")
    
    # FastAPI의 기본 HTTPException 핸들러에 위임
    return await request.app.exception_handler(HTTPException)(request, exc)

def register_exception_handlers(app):
    """모든 예외 핸들러를 애플리케이션에 등록"""
    
    # 일반 예외 핸들러 등록
    app.add_exception_handler(Exception, global_exception_handler)
    
    # 검증 예외 핸들러 등록
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # HTTP 예외 핸들러 등록 (로깅 목적)
    app.add_exception_handler(HTTPException, http_exception_handler)