from typing import List, Dict, Tuple, Any, Optional
import logging
from sqlalchemy.orm import Session
from ..schemas import TradmarkSearchParams, SearchResult, TradmarkDetail
from ..repositories.tradmark import TradmarkRepository

# 로거 설정
logger = logging.getLogger(__name__)

class TradmarkService:
    """
    상표 서비스 클래스
    
    비즈니스 로직을 담당하며, 저장소 레이어를 통해 데이터에 접근
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = TradmarkRepository(db)
    
    def search_trademarks(self, params: TradmarkSearchParams) -> Tuple[List[SearchResult], int]:
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
            
            # 결과 변환 (DB 모델 -> 응답 스키마)
            results = []
            for trademark in trademarks:
                results.append(SearchResult(
                    applicationNumber=trademark.applicationNumber,
                    productName=trademark.productName,
                    productNameEng=trademark.productNameEng,
                    applicationDate=trademark.applicationDate,
                    registerStatus=trademark.registerStatus,
                    registrationNumber=trademark.registrationNumber,
                    registrationDate=trademark.registrationDate,
                    asignProductMainCodeList=trademark.asignProductMainCodeList
                ))
            
            logger.debug(f"상표 검색 결과: {total_count}건 중 {len(results)}건 반환")
            return results, total_count
            
        except Exception as e:
            logger.error(f"상표 검색 중 서비스 계층 오류: {str(e)}")
            raise