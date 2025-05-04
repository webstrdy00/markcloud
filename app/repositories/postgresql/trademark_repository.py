from typing import List, Tuple, Optional, Dict, Any
import logging
import datetime
from sqlalchemy import select, func, or_, and_, text, cast, String, insert
from sqlalchemy.sql.expression import literal_column
from sqlalchemy.orm import Session

from ...models.trademark import Trademark
from ...schemas.trademark import TrademarkSearchParams
from ..trademark_repository import ITrademarkRepository
from ...utils.search import is_korean, matches_initial_consonants, extract_initial_consonants

# 로깅 설정
logger = logging.getLogger(__name__)

class PostgresTrademarkRepository(ITrademarkRepository):
    """
    PostgreSQL 기반 상표 저장소 구현체
    
    ITrademarkRepository 인터페이스 구현
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_id(self, id: int) -> Optional[Trademark]:
        """
        ID로 상표 정보 조회
        
        Args:
            id: 상표 ID
            
        Returns:
            상표 모델 객체 또는 None
        """
        try:
            query = select(Trademark).where(Trademark.id == id)
            result = self.db.execute(query).first()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"상표 ID 조회 중 오류: {str(e)}")
            raise
    
    def search(self, params: TrademarkSearchParams) -> Tuple[List[Trademark], int]:
        """
        검색 조건에 맞는 상표 정보 검색
        
        Args:
            params: 검색 파라미터
            
        Returns:
            상표 모델 객체 리스트와 총 결과 수
        """
        try:
            # 기본 쿼리 생성
            query = select(Trademark)
            
            # 필터 조건 적용
            query = self._apply_filters(query, params)
            
            # 검색어가 있는 경우 검색 조건 적용
            initial_search_term = None
            if params.query:
                query = self._apply_search_conditions(query, params.query)
                # 초성 검색 여부 확인
                if hasattr(query, '_initial_search_term'):
                    initial_search_term = getattr(query, '_initial_search_term')
                    delattr(query, '_initial_search_term')
            
            # 총 결과 수 계산을 위한 카운트 쿼리 (초성 검색이면 나중에 수정)
            count_query = query.with_only_columns(func.count()).order_by(None)
            
            # 결과 조회
            results = self.db.execute(query).scalars().all()
            
            # 초성 검색인 경우 Python에서 필터링
            if initial_search_term:
                from ...utils.search import matches_initial_consonants, extract_initial_consonants
                # 초성 검색 필터링 - 로깅 추가
                filtered_results = []
                logger.debug(f"초성 검색 필터링 시작: 검색어='{initial_search_term}', 결과 수={len(results)}")
                
                for trademark in results:
                    # productName이 있고 초성과 일치하는지 확인
                    product_name = trademark.productName or ""
                    if product_name and initial_search_term in extract_initial_consonants(product_name):
                        filtered_results.append(trademark)
                        if len(filtered_results) <= 5:  # 처음 5개만 로깅
                            logger.debug(f"초성 일치: 상표명='{product_name}', 초성='{extract_initial_consonants(product_name)}'")
                
                # 필터링된 결과로 대체
                logger.debug(f"초성 검색 필터링 완료: 검색어='{initial_search_term}', 필터링 전={len(results)}, 필터링 후={len(filtered_results)}")
                results = filtered_results
                total_count = len(results)
                
                # 페이징 적용 (Python에서)
                start = params.offset
                end = start + params.limit
                results = results[start:end]
            else:
                # 기본 페이징 및 카운트
                total_count = self.db.execute(count_query).scalar()
                
                # 페이징 적용
                query = query.offset(params.offset).limit(params.limit)
                results = self.db.execute(query).scalars().all()
            
            return results, total_count
        
        except Exception as e:
            logger.error(f"상표 검색 중 오류: {str(e)}")
            raise
    
    def list_all(self) -> List[Trademark]:
        """
        모든 상표 조회 (주의: 대량 데이터의 경우 사용 지양)
        
        Returns:
            모든 상표 리스트
        """
        try:
            query = select(Trademark)
            results = self.db.execute(query).scalars().all()
            return list(results)
        except Exception as e:
            logger.error(f"모든 상표 조회 중 오류: {str(e)}")
            raise
    
    def create(self, entity: Trademark) -> Trademark:
        """
        상표 생성
        
        Args:
            entity: 생성할 상표 엔티티
            
        Returns:
            생성된 상표 엔티티
        """
        try:
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except Exception as e:
            self.db.rollback()
            logger.error(f"상표 생성 중 오류: {str(e)}")
            raise
    
    def update(self, entity: Trademark) -> Trademark:
        """
        상표 업데이트
        
        Args:
            entity: 업데이트할 상표 엔티티
            
        Returns:
            업데이트된 상표 엔티티
        """
        try:
            self.db.merge(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except Exception as e:
            self.db.rollback()
            logger.error(f"상표 업데이트 중 오류: {str(e)}")
            raise
    
    def delete(self, id: int) -> bool:
        """
        ID로 상표 삭제
        
        Args:
            id: 삭제할 상표 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            entity = self.find_by_id(id)
            if entity:
                self.db.delete(entity)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"상표 삭제 중 오류: {str(e)}")
            raise
    
    def get_register_statuses(self) -> List[str]:
        """
        등록 상태 목록 조회
        
        Returns:
            중복 제거된 등록 상태 목록
        """
        try:
            query = select(Trademark.registerStatus).distinct().where(Trademark.registerStatus != None)
            results = self.db.execute(query).scalars().all()
            return [status for status in results if status]
        except Exception as e:
            logger.error(f"등록 상태 목록 조회 중 오류: {str(e)}")
            raise

    def get_product_codes(self) -> List[str]:
        """
        상품 분류 코드 목록 조회
        
        Returns:
            중복 제거된 상품 분류 코드 목록
        """
        try:
            # PostgreSQL의 unnest 함수를 사용하여 배열 요소를 행으로 변환 후 중복 제거
            query = text('SELECT DISTINCT unnest("asignProductMainCodeList") as code FROM trademarks WHERE "asignProductMainCodeList" IS NOT NULL ORDER BY code')
            results = self.db.execute(query).scalars().all()
            return [code for code in results if code]
        except Exception as e:
            logger.error(f"상품 분류 코드 목록 조회 중 오류: {str(e)}")
            raise
    
    # 헬퍼 메서드 - 공통 필터 적용
    def _apply_filters(self, query, params: TrademarkSearchParams):
        """
        검색 파라미터에 따라 필터 조건 적용
        
        Args:
            query: 기존 쿼리
            params: 검색 파라미터
            
        Returns:
            필터가 적용된 쿼리
        """
        # 등록 상태 필터
        if params.status:
            query = query.where(Trademark.registerStatus == params.status)
        
        # 상품 코드 필터
        if params.product_code:
            query = query.where(Trademark.asignProductMainCodeList.any(params.product_code))
        
        # 날짜 범위 필터 - Date 타입 처리 개선
        if params.from_date or params.to_date:
            date_column = getattr(Trademark, params.date_type)
            
            # 날짜 형식 변환 (문자열 -> 날짜)
            if params.from_date:
                try:
                    from_date = datetime.date(
                        year=int(params.from_date[:4]),
                        month=int(params.from_date[4:6]),
                        day=int(params.from_date[6:8])
                    )
                    query = query.where(date_column >= from_date)
                except (ValueError, TypeError, IndexError):
                    logger.warning(f"잘못된 시작 날짜 형식: {params.from_date}")
            
            if params.to_date:
                try:
                    to_date = datetime.date(
                        year=int(params.to_date[:4]),
                        month=int(params.to_date[4:6]),
                        day=int(params.to_date[6:8])
                    )
                    query = query.where(date_column <= to_date)
                except (ValueError, TypeError, IndexError):
                    logger.warning(f"잘못된 종료 날짜 형식: {params.to_date}")
        
        return query
    
    # 헬퍼 메서드 - 검색 조건 적용
    def _apply_search_conditions(self, query, search_term: str):
        """
        검색어 기반 검색 및 정렬 적용
        
        Args:
            query: 기존 쿼리
            search_term: 검색어
            
        Returns:
            검색이 적용된 쿼리
        """
        # 검색어 준비
        search_term = search_term.strip()
        
        # 한글 초성 검색인지 확인
        is_initial_search = matches_initial_consonants(search_term, search_term)
        
        if is_initial_search:
            logger.debug(f"한글 초성 검색 패턴 감지: {search_term}")
            # 한글 초성 검색 - Python 구현 함수 활용 (데이터베이스 함수 사용 안함)
            try:
                # 기본 필터링을 최소화하고 모든 결과를 가져온 다음 Python에서 필터링합니다
                # 초성 검색을 위한 플래그 설정
                setattr(query, '_initial_search_term', search_term)
                
                # 검색어가 하나 이상일 경우, 첫 글자로만 약간의 필터링 수행
                if len(search_term) > 1:
                    # 약한 필터링 - DB에서 필터링을 최소화하고 Python에서 정확히 필터링
                    search_condition = Trademark.id > 0  # 항상 True 조건
                    query = query.where(search_condition)
                    logger.debug(f"한글 초성 검색을 위한 최소 필터 적용: {search_term}")
                else:
                    # 검색어가 한 글자인 경우 필터링 없이 진행
                    logger.debug(f"한글 초성 검색 - 필터 없이 전체 데이터 대상 검색: {search_term}")
            except Exception as e:
                logger.warning(f"한글 초성 검색 필터 설정 실패, 일반 검색으로 대체: {str(e)}")
                # 실패시 일반 검색으로 대체
                search_condition = or_(
                    Trademark.productName.ilike(f"%{search_term}%"),
                    Trademark.productNameEng.ilike(f"%{search_term}%"),
                    Trademark.applicationNumber.ilike(f"%{search_term}%")
                )
                query = query.where(search_condition)
        else:
            # 한글 검색인지 확인 - is_korean 함수 활용하여 가독성 개선
            has_korean = is_korean(search_term)
            logger.debug(f"검색어 분석: 한글포함={has_korean}, 검색어='{search_term}'")
            
            # 일반 검색 - 트리그램 유사도 활용
            
            # 1. tsvector 기반 전문 검색
            # 검색어를 토큰화하고 각 토큰에 :* 접미사 추가 (접두사 검색)
            tsquery_tokens = [f"{token}:*" for token in search_term.split()]
            tsquery_text = " & ".join(tsquery_tokens)
            tsquery = func.to_tsquery('simple', tsquery_text)
            
            # 2. 트리그램 유사도 기반 퍼지 검색
            # similarity 함수가 0.3 이상이면 유사하다고 판단
            similarity_threshold = 0.3
            similarity_conditions = [
                func.similarity(Trademark.productName, search_term) > similarity_threshold,
                func.similarity(Trademark.productNameEng, search_term) > similarity_threshold,
                Trademark.applicationNumber.ilike(f"%{search_term}%"),
                # 배열 필드 검색을 위한 조건
                func.array_to_string(Trademark.registrationNumber, ',').ilike(f"%{search_term}%")
            ]
            
            # 검색 조건 적용
            search_condition = or_(
                Trademark.search_vector.op('@@')(tsquery),
                *similarity_conditions
            )
            
            query = query.where(search_condition)
            
            # 유사도 기반 정렬
            similarity_order = (
                func.greatest(
                    func.similarity(Trademark.productName, search_term),
                    func.similarity(Trademark.productNameEng, search_term),
                    func.similarity(cast(Trademark.applicationNumber, String), search_term),
                    # 배열에서는 첫 번째 요소만 비교 (단순화)
                    func.coalesce(func.similarity(func.array_to_string(Trademark.registrationNumber, ','), search_term), 0)
                ).desc()
            )
            
            query = query.order_by(similarity_order)
        
        return query

    def batch_insert(self, batch: List[Dict[str, Any]], batch_size: int):
        """
        Batch insert 작업을 수행합니다.
        
        Args:
            batch: 삽입할 데이터 배치
            batch_size: 배치 크기
        """
        try:
            # 배치 크기에 도달하면 데이터베이스에 삽입
            if len(batch) >= batch_size:
                # upsert 작업 (on conflict do update)
                self.db.execute(insert(Trademark).values(batch).on_conflict_do_update(
                    index_elements=['id'],
                    set_={k: insert(Trademark).excluded[k] for k in batch[0].keys() if k != 'id'}
                ))
                self.db.commit()
                logger.info(f"{len(batch)}개 데이터 처리 완료")
                batch = []
        except Exception as e:
            logger.error(f"Batch insert 중 오류: {str(e)}")
            raise