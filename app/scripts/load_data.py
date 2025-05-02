import json
import os
import sys
import logging
import datetime
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

# 상위 디렉토리를 import path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_db
from models.tradmark import Tradmark
from config import settings

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def convert_date_string(date_str):
    """YYYYMMDD 형식의 문자열을 datetime.date 객체로 변환"""
    if not date_str or date_str == "null" or len(date_str) != 8:
        return None
    
    try:
        return datetime.date(
            year=int(date_str[:4]),
            month=int(date_str[4:6]),
            day=int(date_str[6:8])
        )
    except (ValueError, TypeError):
        logger.warning(f"잘못된 날짜 형식: {date_str}")
        return None

def preprocess_trademark_data(data):
    """상표 데이터 전처리 함수"""
    processed_data = {}
    
    # 기본 필드 처리
    for key, value in data.items():
        # null 값 처리
        if value == "null" or value == "":
            processed_data[key] = None
        else:
            processed_data[key] = value
    
    # 날짜 필드를 Date 타입으로 변환
    date_fields = ["applicationDate", "publicationDate"]
    for field in date_fields:
        if field in processed_data and processed_data[field]:
            processed_data[field] = convert_date_string(processed_data[field])
    
    # 리스트 필드 처리
    list_fields = [
        "registrationNumber",  # 샘플에서 배열로 제공됨
        "registrationDate",    # 샘플에서 배열로 제공됨
        "internationalRegNumbers", 
        "priorityClaimNumList", 
        "priorityClaimDateList", 
        "asignProductMainCodeList", 
        "asignProductSubCodeList", 
        "viennaCodeList"
    ]
    
    for field in list_fields:
        if field in processed_data:
            # 이미 리스트인 경우
            if isinstance(processed_data[field], list):
                continue
                
            # 문자열을 리스트로 변환 (쉼표로 구분)
            elif isinstance(processed_data[field], str):
                processed_data[field] = [item.strip() for item in processed_data[field].split(',') if item.strip()]
                
            # None인 경우 빈 리스트로 변환
            elif processed_data[field] is None:
                processed_data[field] = []
                
            # 기타 타입은 단일 요소 리스트로 변환
            else:
                processed_data[field] = [processed_data[field]]
    
    return processed_data

def load_json_to_db(json_file_path):
    """JSON 파일을 PostgreSQL 데이터베이스에 로드"""
    try:
        # 데이터베이스 초기화 (테이블 생성)
        init_db()
        
        # JSON 파일 로드
        logger.info(f"데이터 로드 중: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as file:
            trademarks_data = json.load(file)
        
        logger.info(f"총 {len(trademarks_data)}개의 상표 데이터를 찾았습니다.")
        
        # 세션 생성
        db = SessionLocal()
        
        try:
            # 데이터 카운터
            count = 0
            batch_size = 100
            
            # 배치 처리를 위한 리스트
            batch = []
            
            # 각 상표 데이터 처리
            for trademark_data in trademarks_data:
                # 데이터 전처리
                processed_data = preprocess_trademark_data(trademark_data)
                
                # 배치에 추가
                batch.append(processed_data)
                count += 1
                
                # 배치 크기에 도달하면 데이터베이스에 삽입
                if len(batch) >= batch_size:
                    # upsert 작업 (on conflict do update)
                    db.execute(insert(Tradmark).values(batch).on_conflict_do_update(
                        index_elements=['applicationNumber'],
                        set_={k: insert(Tradmark).excluded[k] for k in processed_data.keys() if k != 'applicationNumber'}
                    ))
                    db.commit()
                    logger.info(f"{count}개 데이터 처리 완료")
                    batch = []
            
            # 남은 배치 처리
            if batch:
                db.execute(insert(Tradmark).values(batch).on_conflict_do_update(
                    index_elements=['applicationNumber'],
                    set_={k: insert(Tradmark).excluded[k] for k in processed_data.keys() if k != 'applicationNumber'}
                ))
                db.commit()
                logger.info(f"{count}개 데이터 처리 완료 (마지막 배치)")
            
            # 전문 검색 벡터 업데이트
            logger.info("검색 벡터 업데이트 중...")
            db.execute(text("""
                UPDATE trademarks 
                SET search_vector = 
                    setweight(to_tsvector('simple', coalesce(productName, '')), 'A') ||
                    setweight(to_tsvector('simple', coalesce(productNameEng, '')), 'B') ||
                    setweight(to_tsvector('simple', coalesce(applicationNumber, '')), 'C') ||
                    setweight(to_tsvector('simple', coalesce(array_to_string(registrationNumber, ' '), '')), 'C')
            """))
            db.commit()
            
            # 트리거 생성/확인 (전문 검색 벡터 자동 업데이트용)
            try:
                db.execute(text("""
                    CREATE OR REPLACE FUNCTION trademark_search_vector_update() RETURNS trigger AS $$
                    BEGIN
                        NEW.search_vector = 
                            setweight(to_tsvector('simple', coalesce(NEW.productName, '')), 'A') ||
                            setweight(to_tsvector('simple', coalesce(NEW.productNameEng, '')), 'B') ||
                            setweight(to_tsvector('simple', coalesce(NEW.applicationNumber, '')), 'C') ||
                            setweight(to_tsvector('simple', coalesce(array_to_string(NEW.registrationNumber, ' '), '')), 'C');
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                    
                    DROP TRIGGER IF EXISTS trademark_search_vector_update ON trademarks;
                    
                    CREATE TRIGGER trademark_search_vector_update
                    BEFORE INSERT OR UPDATE ON trademarks
                    FOR EACH ROW EXECUTE FUNCTION trademark_search_vector_update();
                """))
                db.commit()
                logger.info("검색 벡터 자동 업데이트 트리거 생성 완료")
            except Exception as e:
                db.rollback()
                logger.warning(f"트리거 생성 실패: {str(e)}")
            
            logger.info(f"데이터베이스 로드 완료: 총 {count}개 상표 데이터")
            
        except Exception as e:
            db.rollback()
            logger.error(f"데이터 로드 중 오류 발생: {str(e)}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"치명적 오류: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 커맨드 라인 인자로 JSON 파일 경로를 받거나 환경변수 또는 기본 경로 사용
    if len(sys.argv) > 1:
        json_file_path = sys.argv[1]
    else:
        json_file_path = settings.DATA_FILE_PATH
    
    load_json_to_db(json_file_path)