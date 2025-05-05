from typing import List, Tuple, Optional
from abc import ABC, abstractmethod
from .base import BaseRepository
from ..models.trademark import Trademark
from ..schemas.trademark import TrademarkSearchParams

class ITrademarkRepository(BaseRepository[Trademark, TrademarkSearchParams], ABC):
    """
    상표 저장소 인터페이스
    
    BaseRepository 기본 메서드 외에 상표 특화 메서드를 추가 정의
    """
    
    @abstractmethod
    def get_register_statuses(self) -> List[str]:
        """
        등록 상태 목록 조회
        
        Returns:
            중복 제거된 등록 상태 목록
        """
        pass
    
    @abstractmethod
    def get_product_codes(self) -> List[str]:
        """
        상품 분류 코드 목록 조회
        
        Returns:
            중복 제거된 상품 분류 코드 목록
        """
        pass