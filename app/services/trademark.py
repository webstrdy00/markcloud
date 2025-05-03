from typing import List, Dict, Tuple, Any, Optional
import logging
from sqlalchemy.orm import Session
from ..schemas import TrademarkSearchParams, SearchResult, TrademarkDetail
from ..repositories.trademark import TrademarkRepository

# 로거 설정
logger = logging.getLogger(__name__)

class TrademarkService:
    """
    상표 서비스 클래스
    
    비즈니스 로직을 담당하며, 저장소 레이어를 통해 데이터에 접근
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = TrademarkRepository(db)
    
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

    def get_trademark_by_id(self, trademark_id: str) -> Optional[TrademarkDetail]:
        """
        ID로 상표 상세 정보 조회
        
        Args:
            trademark_id: 조회할 상표 ID (applicationNumber)
            
        Returns:
            상표 상세 정보 또는 None
        """
        try:
            # 저장소를 통해 데이터 조회
            trademark = self.repository.find_by_id(trademark_id)
            
            if not trademark:
                logger.debug(f"상표 ID '{trademark_id}' 조회: 해당 상표를 찾을 수 없음")
                return None
            
            # DB 모델을 응답 스키마로 변환
            detail = TrademarkDetail(
                productName=trademark.productName,
                productNameEng=trademark.productNameEng,
                applicationNumber=trademark.applicationNumber,
                applicationDate=trademark.applicationDate,
                registerStatus=trademark.registerStatus,
                publicationNumber=trademark.publicationNumber,
                publicationDate=trademark.publicationDate,
                registrationNumber=trademark.registrationNumber,
                registrationDate=trademark.registrationDate,
                internationalRegNumbers=trademark.internationalRegNumbers,
                internationalRegDate=trademark.internationalRegDate,
                priorityClaimNumList=trademark.priorityClaimNumList,
                priorityClaimDateList=trademark.priorityClaimDateList,
                asignProductMainCodeList=trademark.asignProductMainCodeList,
                asignProductSubCodeList=trademark.asignProductSubCodeList,
                viennaCodeList=trademark.viennaCodeList
            )
            
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