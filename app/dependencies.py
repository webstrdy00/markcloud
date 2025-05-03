from fastapi import Depends
from typing import Annotated
from sqlalchemy.orm import Session

from .database import get_db
from .repositories.trademark_repository import ITrademarkRepository
from .repositories.factory import get_trademark_repository
from .services.trademark import TrademarkService

# 저장소 의존성
def get_trademark_repository_dependency(db: Session = Depends(get_db)) -> ITrademarkRepository:
    return get_trademark_repository("postgres", db)

# 서비스 의존성
def get_trademark_service(
    repository: ITrademarkRepository = Depends(get_trademark_repository_dependency)
) -> TrademarkService:
    # 수정된 서비스 생성자 (저장소를 직접 주입)
    service = TrademarkService(repository)
    return service

# 타입 별칭 추가 (라우터에서 사용)
TrademarkServiceDep = Annotated[TrademarkService, Depends(get_trademark_service)]