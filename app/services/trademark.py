from typing import List, Dict, Tuple, Any, Optional
import logging
from sqlalchemy.orm import Session
from ..schemas import TrademarkSearchParams, SearchResult, TrademarkDetail
from ..repositories.trademark_repository import ITrademarkRepository
from ..repositories.factory import get_trademark_repository
from ..utils.dto import to_schema, to_schema_list
from ..utils.search import fuzzy_match, calculate_similarity

# 로거 설정
logger = logging.getLogger(__name__)

class TrademarkService:
    """
    상표 서비스 클래스
    
    비즈니스 로직을 담당하며, 저장소 레이어를 통해 데이터에 접근
    """
        
    def __init__(self, repository: ITrademarkRepository):
        # 저장소 인터페이스를 직접 주입 받음
        self.repository = repository
    
    def search_trademarks(self, params: TrademarkSearchParams) -> Tuple[List[SearchResult], int]:
        """
        상표 검색 기능
        
        Args:
            params: 검색 파라미터 (검색어, 필터, 페이징 등)
            
        Returns:
            검색 결과 리스트와 총 결과 수를 포함한 튜플
        """
        try:
            # 검색 파라미터 로깅
            logger.debug(f"상표 검색 요청: 검색어='{params.query}', 상태='{params.status}', 상품코드='{params.product_code}'")
            
            # 저장소를 통해 데이터 검색
            trademarks, total_count = self.repository.search(params)
            
            # 결과 변환 (DB 모델 -> 응답 스키마) - 헬퍼 함수 활용
            results = to_schema_list(trademarks, SearchResult)
            
            # 검색어가 있고 결과가 적은 경우(10개 이하), Python 퍼지 매칭으로 후처리
            # 대량 데이터에서는 이 로직이 무거울 수 있으므로 결과가 적을 때만 실행
            if params.query and len(results) <= 10:
                logger.debug(f"Python 퍼지 매칭 후처리 적용 - 결과 {len(results)}건")
                # 결과 정렬 - 유사도에 따라 재정렬
                if results:
                    # 상표명 유사도 계산 (None 체크 필요)
                    for result in results:
                        # productName이 None이면 빈 문자열로 대체
                        product_name = result.productName or ""
                        # 유사도 점수 계산 및 저장 (임시 필드)
                        result.similarity_score = calculate_similarity(product_name, params.query)
                    
                    # 유사도에 따라 내림차순 정렬
                    results.sort(key=lambda x: x.similarity_score, reverse=True)
                    
                    # 임시 필드 제거
                    for result in results:
                        if hasattr(result, 'similarity_score'):
                            delattr(result, 'similarity_score')
            
            logger.debug(f"상표 검색 결과: {total_count}건 중 {len(results)}건 반환")
            return results, total_count
            
        except Exception as e:
            logger.error(f"상표 검색 중 서비스 계층 오류: {str(e)}")
            raise

    def get_trademark_by_id(self, trademark_id: str) -> Optional[TrademarkDetail]:
        """
        ID로 상표 상세 정보 조회
        
        Args:
            trademark_id: 조회할 상표 ID
            
        Returns:
            상표 상세 정보 또는 None
        """
        try:
            # 문자열 ID를 정수로 변환
            try:
                id_value = int(trademark_id)
            except ValueError:
                logger.debug(f"상표 ID '{trademark_id}' 변환 실패: 정수로 변환할 수 없음")
                return None
                
            # 저장소를 통해 데이터 조회
            trademark = self.repository.find_by_id(id_value)
            
            if not trademark:
                logger.debug(f"상표 ID '{trademark_id}' 조회: 해당 상표를 찾을 수 없음")
                return None
            
            # DB 모델을 응답 스키마로 변환 - 헬퍼 함수 활용
            detail = to_schema(trademark, TrademarkDetail)
            
            logger.debug(f"상표 ID '{trademark_id}' 조회 성공: {trademark.productName}")
            return detail
            
        except Exception as e:
            logger.error(f"상표 상세 정보 조회 중 서비스 계층 오류: {str(e)}")
            raise

    def get_register_statuses(self) -> List[str]:
        """
        등록 상태 목록 조회
        
        Returns:
            중복 제거된 등록 상태 목록
        """
        try:
            statuses = self.repository.get_register_statuses()
            logger.debug(f"등록 상태 목록 조회: {len(statuses)}개 항목")
            return statuses
        except Exception as e:
            logger.error(f"등록 상태 목록 조회 중 서비스 계층 오류: {str(e)}")
            raise

    def get_product_codes(self) -> List[str]:
        """
        상품 분류 코드 목록 조회
        
        Returns:
            중복 제거된 상품 분류 코드 목록
        """
        try:
            codes = self.repository.get_product_codes()
            logger.debug(f"상품 분류 코드 목록 조회: {len(codes)}개 항목")
            return codes
        except Exception as e:
            logger.error(f"상품 분류 코드 목록 조회 중 서비스 계층 오류: {str(e)}")
            raise