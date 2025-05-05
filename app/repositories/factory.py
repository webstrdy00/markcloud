from typing import Literal
from sqlalchemy.orm import Session

from .trademark_repository import ITrademarkRepository
from .postgresql.trademark_repository import PostgresTrademarkRepository
from .mock.trademark_repository import MockTrademarkRepository

RepositoryType = Literal["postgres", "mock"]

def get_trademark_repository(
    repo_type: RepositoryType = "postgres", 
    db: Session = None
) -> ITrademarkRepository:
    """
    상표 저장소 구현체 팩토리 함수
    
    Args:
        repo_type: 저장소 타입 ("postgres" 또는 "mock")
        db: 데이터베이스 세션 (postgres 타입인 경우 필수)
        
    Returns:
        ITrademarkRepository 구현체
    """
    if repo_type == "postgres":
        if db is None:
            raise ValueError("PostgreSQL 저장소를 사용하려면 db 세션이 필요합니다")
        return PostgresTrademarkRepository(db)
    
    elif repo_type == "mock":
        return MockTrademarkRepository()
    
    else:
        raise ValueError(f"지원되지 않는 저장소 타입: {repo_type}")