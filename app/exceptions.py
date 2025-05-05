import traceback
import logging
from typing import Callable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from .config import settings
"""
애플리케이션 전체 예외 처리 모듈
"""

# 로거 설정
logger = logging.getLogger(__name__)

# 일반 예외 핸들러
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    일반 예외 처리 핸들러
    
    모든 처리되지 않은 예외를 로깅하고 적절한 응답을 반환
    """
    # 예외 상세 정보 로깅
    logger.error("처리되지 않은 예외 발생:")
    logger.error(traceback.format_exc())
    logger.debug(f"URL: {request.url}, 메서드: {request.method}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "내부 서버 오류가 발생했습니다.",
            "error": str(exc)
        }
    )
    
# 재귀 예외 핸들러
async def recursion_error_handler(request: Request, exc: RecursionError) -> JSONResponse:
    """
    재귀 호출 예외 처리 핸들러
    
    무한 재귀 호출 오류 처리
    """
    # 예외 상세 정보 로깅
    logger.error("재귀 호출 한계 초과 오류 발생:")
    logger.error(traceback.format_exc())
    logger.debug(f"URL: {request.url}, 메서드: {request.method}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "서버 내부 오류가 발생했습니다. 관리자에게 문의하세요."
        }
    )
    
# 유효성 검사 예외 핸들러
async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    유효성 검사 예외 처리 핸들러
    
    요청 바디, 쿼리 파라미터, 경로 파라미터 등의 유효성 검사 실패 처리
    """
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        error_messages.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    
    logger.warning(f"유효성 검사 오류: {error_messages}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "요청 데이터 검증에 실패했습니다.",
            "errors": error_messages
        }
    )

# HTTP 예외 핸들러
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP 예외 처리 핸들러
    
    명시적으로 발생시킨 HTTP 예외 처리 (404, 403 등)
    """
    logger.info(f"HTTP {exc.status_code} 오류: {exc.detail}")
    
    # 직접 JSONResponse를 생성하여 반환
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

def register_exception_handlers(app):
    """모든 예외 핸들러를 애플리케이션에 등록"""
    
    # 일반 예외 핸들러 등록
    app.add_exception_handler(Exception, generic_exception_handler)
    
    # 재귀 예외 핸들러 등록
    app.add_exception_handler(RecursionError, recursion_error_handler)
    
    # 검증 예외 핸들러 등록
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # HTTP 예외 핸들러 등록 (로깅 목적)
    app.add_exception_handler(HTTPException, http_exception_handler)