from fastapi import Depends
from typing import Annotated, Generator
from sqlalchemy.orm import Session
import logging

from .database import get_db
from .repositories.trademark_repository import ITrademarkRepository
from .repositories.factory import get_trademark_repository
from .services.trademark import TrademarkService

# 로거 설정
logger = logging.getLogger(__name__)

# 저장소 의존성 - yield 패턴 적용 (동기 함수로 변경)
def get_trademark_repository_dependency(
    db: Session = Depends(get_db)
) -> Generator[ITrademarkRepository, None, None]:
    """
    상표 저장소 의존성 제공
    
    Args:
        db: 데이터베이스 세션 (의존성 주입)
        
    Yields:
        상표 저장소 인터페이스 구현체
    """
    repository = get_trademark_repository("postgres", db)
    try:
        logger.debug("상표 저장소 생성")
        yield repository
    finally:
        # 저장소 정리 작업 (필요한 경우)
        logger.debug("상표 저장소 정리")

# 서비스 의존성 - yield 패턴 적용 (동기 함수로 변경)
def get_trademark_service_dependency(
    repository: ITrademarkRepository = Depends(get_trademark_repository_dependency)
) -> Generator[TrademarkService, None, None]:
    """
    상표 서비스 의존성 제공
    
    Args:
        repository: 상표 저장소 (의존성 주입)
        
    Yields:
        상표 서비스 인스턴스
    """
    service = TrademarkService(repository)
    try:
        logger.debug("상표 서비스 생성")
        yield service
    finally:
        # 서비스 정리 작업 (필요한 경우)
        logger.debug("상표 서비스 정리")

# 타입 별칭 추가 (라우터에서 사용)
TrademarkServiceDep = Annotated[TrademarkService, Depends(get_trademark_service_dependency)]