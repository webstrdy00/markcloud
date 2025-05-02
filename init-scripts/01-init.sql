-- PostgreSQL 초기화 스크립트
-- 컨테이너 첫 실행 시 자동으로 실행됩니다

-- 확장 기능 설치
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- 트리그램 검색 지원
CREATE EXTENSION IF NOT EXISTS btree_gin;  -- GIN 인덱스 지원

-- 사용자에게 필요한 권한 부여
ALTER USER trademark_user WITH SUPERUSER;

-- 데이터 변환 함수 (YYYYMMDD 문자열 -> Date 타입)
CREATE OR REPLACE FUNCTION str_to_date(date_str text)
RETURNS date AS $$
BEGIN
    IF date_str IS NULL OR date_str = '' THEN
        RETURN NULL;
    END IF;
    
    RETURN to_date(date_str, 'YYYYMMDD');
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 전문 검색을 위한 트리거 함수 생성
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

-- 테이블 생성 후 트리거 추가 (참고용 - 애플리케이션에서 자동 생성됨)
/*
CREATE TRIGGER trademark_search_vector_update
BEFORE INSERT OR UPDATE ON trademarks
FOR EACH ROW EXECUTE FUNCTION trademark_search_vector_update();
*/

-- 한글 초성 검색을 위한 함수 (선택 사항)
CREATE OR REPLACE FUNCTION extract_korean_initial(text) RETURNS text AS $$
DECLARE
    result text := '';
    curr_char text;
    curr_code int;
    chosung text[] := ARRAY['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
BEGIN
    FOR i IN 1..length($1) LOOP
        curr_char := substring($1 from i for 1);
        curr_code := ascii(curr_char);
        
        -- 한글 유니코드 범위 확인 (가-힣)
        IF curr_code >= 44032 AND curr_code <= 55203 THEN
            -- 초성 인덱스 계산
            result := result || chosung[((curr_code - 44032) / 588)::int + 1];
        ELSE
            result := result || curr_char;
        END IF;
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 필요한 추가 설정이 있다면 여기에 작성하세요
