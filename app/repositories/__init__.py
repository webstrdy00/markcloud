# 인터페이스
from .trademark_repository import ITrademarkRepository

# 기본(PostgreSQL) 구현
from .postgresql.trademark_repository import PostgresTrademarkRepository

# 테스트 / 로컬 모킹용 구현
from .mock.trademark_repository import MockTrademarkRepository

# 팩터리 함수
from .factory import get_trademark_repository, RepositoryType