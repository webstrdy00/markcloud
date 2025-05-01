from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from .config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

# 데이터베이스 URL 확인
if not settings.DATABASE_URL:
    DEFAULT_DB_URL = "postgresql://trademark_user:your_password@localhost:5432/trademark_db"
    logger.warning(f"DATABASE_URL이 설정되지 않아 기본 로컬 데이터베이스를 사용합니다: {DEFAULT_DB_URL}")
    DATABASE_URL = DEFAULT_DB_URL
else:
    DATABASE_URL = settings.DATABASE_URL

# 데이터베이스 연결 정보 로깅 (비밀번호 제외)
try:
    db_parts = DATABASE_URL.split("@")
    if len(db_parts) > 1:
        db_info = db_parts[1]
        logger.info(f"데이터베이스 연결 정보 (호스트:포트/DB): {db_info}")
    else:
        logger.warning("데이터베이스 연결 문자열 형식이 올바르지 않습니다.")
except Exception as e:
    logger.error(f"데이터베이스 연결 정보 파싱 오류: {str(e)}")

try:
    # 데이터베이스 엔진 생성
    engine = create_engine(
        DATABASE_URL,
        echo=(settings.LOG_LEVEL == "DEBUG"),  # 디버그 모드에서만 SQL 쿼리 로깅 활성화
        pool_pre_ping=True,  # 연결 확인
        pool_size=5,         # 연결 풀 크기
        max_overflow=10,     # 최대 추가 연결 수
        pool_recycle=3600,   # 연결 재활용 시간(초)
    )
    logger.info("데이터베이스 엔진 생성 성공")
except Exception as e:
    logger.error(f"데이터베이스 엔진 생성 실패: {str(e)}")
    # 메모리 데이터베이스 폴백
    logger.warning("메모리 데이터베이스로 대체합니다.")
    engine = create_engine("sqlite:///:memory:")

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

def init_db():
    """
    데이터베이스 테이블 초기화 함수
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"데이터베이스 테이블 생성 실패: {str(e)}")
        raise

def get_db():
    """
    API 엔드포인트에서 사용할 데이터베이스 세션 제공
    
    FastAPI의 의존성 주입 시스템에서 사용됨
    """
    db = SessionLocal()
    try:
        logger.debug("데이터베이스 세션 생성")
        yield db
    finally:
        db.close()
        logger.debug("데이터베이스 세션 종료")

def test_connection():
    """
    데이터베이스 연결 테스트 함수
    
    Returns:
        bool: 연결 성공 여부
    """
    try:
        # 간단한 쿼리 실행
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("데이터베이스 연결 테스트 성공!")
            return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 테스트 실패: {str(e)}")
        return False