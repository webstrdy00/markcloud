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

-- 한글 초성 검색을 위한 함수
CREATE OR REPLACE FUNCTION extract_korean_initial(text) RETURNS text AS $$
DECLARE
    result text := '';
    curr_char text;
    curr_code int;
    chosung text[] := ARRAY['ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ','ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'];
BEGIN
    IF $1 IS NULL THEN
        RETURN NULL;
    END IF;
    
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

-- 문자열 유사도 계산 함수 (search.py의 calculate_similarity 구현)
CREATE OR REPLACE FUNCTION calculate_string_similarity(text1 text, text2 text) RETURNS float AS $$
BEGIN
    -- pg_trgm의 similarity 함수 활용
    IF text1 ILIKE '%' || text2 || '%' THEN
        RETURN 0.9;  -- 정확히 포함된 경우 높은 점수 부여
    ELSE
        RETURN similarity(text1, text2);
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 퍼지 매칭 함수 (search.py의 fuzzy_match 구현)
CREATE OR REPLACE FUNCTION fuzzy_match(text1 text, text2 text, threshold float DEFAULT 0.6) RETURNS boolean AS $$
BEGIN
    -- NULL 처리
    IF text1 IS NULL OR text2 IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- 정확히 포함된 경우
    IF text1 ILIKE '%' || text2 || '%' THEN
        RETURN TRUE;
    END IF;
    
    -- 초성 매칭 확인
    IF extract_korean_initial(text1) ILIKE '%' || text2 || '%' THEN
        RETURN TRUE;
    END IF;
    
    -- 유사도 계산 및 임계값 비교
    RETURN calculate_string_similarity(text1, text2) >= threshold;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 테이블 생성 후 트리거 추가 (참고용 - 애플리케이션에서 자동 생성됨)
/*
CREATE TRIGGER trademark_search_vector_update
BEFORE INSERT OR UPDATE ON trademarks
FOR EACH ROW EXECUTE FUNCTION trademark_search_vector_update();
*/