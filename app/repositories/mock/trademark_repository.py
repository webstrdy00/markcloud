from typing import List, Tuple, Optional, Dict, Any
import logging
from ...models.trademark import Trademark
from ...schemas.trademark import TrademarkSearchParams
from ..trademark_repository import ITrademarkRepository

# 로깅 설정
logger = logging.getLogger(__name__)

class MockTrademarkRepository(ITrademarkRepository):
    """
    메모리 기반 Mock 상표 저장소 (테스트용)
    
    ITrademarkRepository 인터페이스 구현
    """
    
    def __init__(self):
        self.trademarks = {}  # 메모리에 상표 저장 
        self.register_statuses = ["등록", "출원", "거절", "실효"]
        self.product_codes = ["01", "02", "03", "05", "35", "42", "43"]
    
    def find_by_id(self, id: int) -> Optional[Trademark]:
        """
        ID로 상표 조회
        """
        return self.trademarks.get(id)
    
    def search(self, params: TrademarkSearchParams) -> Tuple[List[Trademark], int]:
        """
        검색 조건에 맞는 상표 검색
        """
        # 모든 상표 가져오기
        all_trademarks = list(self.trademarks.values())
        
        # 검색 조건 적용
        filtered_trademarks = []
        for trademark in all_trademarks:
            # 상태 필터
            if params.status and trademark.registerStatus != params.status:
                continue
            
            # 상품 코드 필터
            if params.product_code and (
                not trademark.asignProductMainCodeList or 
                params.product_code not in trademark.asignProductMainCodeList
            ):
                continue
            
            # 검색어 필터
            if params.query:
                query_lower = params.query.lower()
                product_name = trademark.productName or ""
                product_name_eng = trademark.productNameEng or ""
                application_number = trademark.applicationNumber or ""
                
                if (
                    query_lower not in product_name.lower() and
                    query_lower not in product_name_eng.lower() and
                    query_lower not in application_number.lower()
                ):
                    continue
            
            # 모든 필터 통과
            filtered_trademarks.append(trademark)
        
        # 총 결과 수
        total_count = len(filtered_trademarks)
        
        # 페이징 적용
        start = params.offset
        end = start + params.limit
        paged_trademarks = filtered_trademarks[start:end]
        
        return paged_trademarks, total_count
    
    def list_all(self) -> List[Trademark]:
        """
        모든 상표 조회
        """
        return list(self.trademarks.values())
    
    def create(self, entity: Trademark) -> Trademark:
        """
        상표 생성
        """
        # 이미 존재하는 ID면 오류
        if entity.id is not None and entity.id in self.trademarks:
            raise ValueError(f"id '{entity.id}'은(는) 이미 존재합니다")
        
        # 새 ID 생성 (없는 경우)
        if entity.id is None:
            entity.id = max(self.trademarks.keys(), default=0) + 1
        
        # 상표 저장
        self.trademarks[entity.id] = entity
        return entity
    
    def update(self, entity: Trademark) -> Trademark:
        """
        상표 업데이트
        """
        # ID 없으면 업데이트 불가
        if entity.id is None:
            raise ValueError("id는 필수 항목입니다")
        
        # 존재하지 않는 ID면 오류
        if entity.id not in self.trademarks:
            raise ValueError(f"id '{entity.id}'을(를) 찾을 수 없습니다")
        
        # 상표 업데이트
        self.trademarks[entity.id] = entity
        return entity
    
    def delete(self, id: int) -> bool:
        """
        ID로 상표 삭제
        """
        if id in self.trademarks:
            del self.trademarks[id]
            return True
        return False
    
    def get_register_statuses(self) -> List[str]:
        """
        등록 상태 목록 조회
        """
        return self.register_statuses
    
    def get_product_codes(self) -> List[str]:
        """
        상품 분류 코드 목록 조회
        """
        return self.product_codes