from sqlalchemy import Column, String, Date, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR

# Base 클래스 생성
Base = declarative_base()

class Trademark(Base):
    """상표 데이터베이스 모델"""
    __tablename__ = "trademarks"

    # 기본 필드 - 길이 제한 추가 및 컬럼 타입 최적화
    applicationNumber = Column(String(20), primary_key=True, index=True, comment="출원 번호")
    productName = Column(String(255), nullable=True, comment="상표명(한글)")
    productNameEng = Column(String(255), nullable=True, comment="상표명(영문)")
    
    # 날짜 타입으로 변경 - 날짜 검색 및 정렬 효율화
    applicationDate = Column(Date, nullable=True, index=True, comment="출원일")
    registerStatus = Column(String(50), nullable=True, index=True, comment="등록 상태")
    publicationNumber = Column(String(20), nullable=True, comment="공고 번호")
    publicationDate = Column(Date, nullable=True, comment="공고일")
    
    # 배열 타입으로 수정 - 샘플 데이터 구조에 맞춤
    # 날짜도 Date 타입으로 통일 - 일관성 및 쿼리 효율화
    registrationNumber = Column(ARRAY(String(20)), nullable=True, comment="등록 번호")
    registrationDate = Column(ARRAY(Date), nullable=True, comment="등록일")
    
    # 샘플 데이터에 있는 추가 필드
    registrationPubNumber = Column(String(20), nullable=True, comment="등록공고 번호")
    registrationPubDate = Column(Date, nullable=True, comment="등록공고일")
    
    # 기존 필드 유지 (타입 설명 추가)
    internationalRegNumbers = Column(ARRAY(String(20)), nullable=True, comment="국제 출원 번호")
    internationalRegDate = Column(Date, nullable=True, comment="국제출원일")
    priorityClaimNumList = Column(ARRAY(String(20)), nullable=True, comment="우선권 번호")
    priorityClaimDateList = Column(ARRAY(Date), nullable=True, comment="우선권 일자")
    asignProductMainCodeList = Column(ARRAY(String(10)), nullable=True, comment="상품 주 분류 코드")
    asignProductSubCodeList = Column(ARRAY(String(10)), nullable=True, comment="상품 유사군 코드")
    viennaCodeList = Column(ARRAY(String(10)), nullable=True, comment="비엔나 코드")
    
    # 전문 검색을 위한 tsvector 필드 (트리거로 자동 갱신)
    search_vector = Column(TSVECTOR, nullable=True, comment="검색 벡터")

# PostgreSQL 인덱스 최적화
# gin_trgm_ops 연산자 클래스를 명시적으로 지정 (pg_trgm 확장 필요)
Index('idx_product_name_trgm', Trademark.productName, 
      postgresql_using='gin', 
      postgresql_ops={"productName": "gin_trgm_ops"})

Index('idx_product_name_eng_trgm', Trademark.productNameEng, 
      postgresql_using='gin', 
      postgresql_ops={"productNameEng": "gin_trgm_ops"})

# tsvector 인덱스는 그대로 유지 (이미 올바르게 설정됨)
Index('idx_search_vector', Trademark.search_vector, postgresql_using='gin')

# 배열 필드에 대한 GIN 인덱스 추가 - 다수 필드 검색 지원
Index('idx_product_main_code_array', Trademark.asignProductMainCodeList, postgresql_using='gin')
Index('idx_product_sub_code_array', Trademark.asignProductSubCodeList, postgresql_using='gin')
Index('idx_vienna_code_array', Trademark.viennaCodeList, postgresql_using='gin')

# 검색 벡터 자동 업데이트를 위한 트리거 정의
# PostgreSQL에서 실행할 DDL 스크립트
search_vector_trigger = DDL('''
-- pg_trgm 확장 설치
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 검색 벡터 갱신을 위한 트리거 함수
CREATE OR REPLACE FUNCTION trademark_search_vector_update() RETURNS trigger AS $
BEGIN
    NEW.search_vector = 
        setweight(to_tsvector('simple', coalesce(NEW.productName, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(NEW.productNameEng, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(NEW.applicationNumber, '')), 'C') ||
        setweight(to_tsvector('simple', coalesce(array_to_string(NEW.registrationNumber, ' '), '')), 'C');
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- 트리거 생성 (해당 테이블이 존재해야 함)
DROP TRIGGER IF EXISTS trademark_search_vector_update ON trademarks;
CREATE TRIGGER trademark_search_vector_update
BEFORE INSERT OR UPDATE ON trademarks
FOR EACH ROW EXECUTE FUNCTION trademark_search_vector_update();
''')

# 테이블 생성 후 트리거 생성 이벤트 리스너
event.listen(
    Trademark.__table__, 
    'after_create',
    search_vector_trigger
)