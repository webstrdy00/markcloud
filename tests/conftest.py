import os
import sys
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, List

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("CORS_ORIGINS", "*")

# 앱 임포트
from app.main import app
from app.models.trademark import Trademark, Base
from app.repositories.mock.trademark_repository import MockTrademarkRepository
from app.repositories.trademark_repository import ITrademarkRepository
from app.services.trademark import TrademarkService
from app.dependencies import get_trademark_repository_dependency, get_trademark_service_dependency


# 테스트용 인메모리 SQLite 데이터베이스 설정
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 테스트 클라이언트
@pytest.fixture
def client() -> TestClient:
    """FastAPI 테스트 클라이언트를 반환합니다."""
    return TestClient(app)

# 테스트용 데이터베이스 세션
@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """테스트용 데이터베이스 세션을 생성합니다."""
    # 데이터베이스 스키마 생성
    Base.metadata.create_all(bind=engine)
    
    # 세션 생성
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
    
    # 테스트 후 스키마 삭제
    Base.metadata.drop_all(bind=engine)

# Mock 저장소
@pytest.fixture
def mock_repository() -> MockTrademarkRepository:
    """테스트용 Mock 저장소를 생성합니다."""
    repo = MockTrademarkRepository()
    
    # 테스트 데이터 추가
    # 예시 데이터 1: 스타벅스
    starbucks = Trademark(
        applicationNumber="40-2023-0001",
        productName="스타벅스",
        productNameEng="Starbucks",
        applicationDate=date(2023, 1, 1),
        registerStatus="등록",
        registrationNumber=["42-12345"],
        registrationDate=[date(2023, 12, 1)],
        asignProductMainCodeList=["43", "35"]
    )
    
    # 예시 데이터 2: 커피빈
    coffeebean = Trademark(
        applicationNumber="40-2023-0002",
        productName="커피빈",
        productNameEng="Coffee Bean",
        applicationDate=date(2023, 2, 1),
        registerStatus="출원",
        asignProductMainCodeList=["43"]
    )
    
    # 예시 데이터 3: 삼성전자
    samsung = Trademark(
        applicationNumber="40-2023-0003",
        productName="삼성전자",
        productNameEng="Samsung Electronics",
        applicationDate=date(2023, 3, 1),
        registerStatus="등록",
        registrationNumber=["42-54321"],
        registrationDate=[date(2023, 11, 1)],
        asignProductMainCodeList=["09", "42", "43"]
    )
    
    # 저장소에 데이터 추가
    repo.create(starbucks)
    repo.create(coffeebean)
    repo.create(samsung)
    
    return repo

# 서비스 레이어
@pytest.fixture
def trademark_service(mock_repository: MockTrademarkRepository) -> TrademarkService:
    """Mock 저장소를 사용하는 서비스 인스턴스를 생성합니다."""
    return TrademarkService(mock_repository)

# 의존성 오버라이드 (API 테스트용)
@pytest.fixture(autouse=True)
def override_dependencies():
    """테스트에서 사용할 의존성 오버라이드"""
    # 의존성 백업
    app.dependency_overrides = {}
    
    # 테스트 시작 전
    mock_repo = MockTrademarkRepository()
    
    # 예시 데이터 추가
    starbucks = Trademark(
        applicationNumber="40-2023-0001",
        productName="스타벅스",
        productNameEng="Starbucks",
        applicationDate=date(2023, 1, 1),
        registerStatus="등록",
        registrationNumber=["42-12345"],
        registrationDate=[date(2023, 12, 1)],
        asignProductMainCodeList=["43", "35"]
    )
    
    coffeebean = Trademark(
        applicationNumber="40-2023-0002",
        productName="커피빈",
        productNameEng="Coffee Bean",
        applicationDate=date(2023, 2, 1),
        registerStatus="출원",
        asignProductMainCodeList=["43"]
    )
    
    # 삼성전자 데이터 추가
    samsung = Trademark(
        applicationNumber="40-2023-0003",
        productName="삼성전자",
        productNameEng="Samsung Electronics",
        applicationDate=date(2023, 3, 1),
        registerStatus="등록",
        registrationNumber=["42-54321"],
        registrationDate=[date(2023, 11, 1)],
        asignProductMainCodeList=["09", "42", "43"] 
    )
    
    # 추가 더미 데이터 (필요한 모든 코드 포함)
    dummy = Trademark(
        applicationNumber="40-2023-0004",
        productName="테스트상표",
        productNameEng="Test Mark",
        applicationDate=date(2023, 4, 1),
        registerStatus="거절",
        asignProductMainCodeList=["02", "03", "05"]
    )
    
    mock_repo.create(starbucks)
    mock_repo.create(coffeebean)
    mock_repo.create(samsung)
    mock_repo.create(dummy)
    
    # 저장소 의존성 오버라이드
    def get_mock_repo():
        return mock_repo
    
    # 서비스 의존성 오버라이드
    def get_mock_service():
        service = TrademarkService(mock_repo)
        yield service
    
    app.dependency_overrides[get_trademark_repository_dependency] = get_mock_repo
    app.dependency_overrides[get_trademark_service_dependency] = get_mock_service
    
    # 테스트 실행
    yield
    
    # 테스트 종료 후 정리
    app.dependency_overrides = {}