from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, TypeVar, Generic, Type, Any
from sqlalchemy.orm import Session

# 제네릭 타입 변수 정의
ModelT = TypeVar('ModelT')  # 데이터베이스 모델 타입
ParamsT = TypeVar('ParamsT')  # 검색 파라미터 타입

class BaseRepository(Generic[ModelT, ParamsT], ABC):
    """
    리포지토리 인터페이스 (추상 클래스)
    
    모든 구체적인 리포지토리 클래스는 이 인터페이스를 구현해야 함
    """
    
    @abstractmethod
    def find_by_id(self, id: int) -> Optional[ModelT]:
        """
        ID로 단일 엔티티 조회
        
        Args:
            id: 엔티티 ID
            
        Returns:
            조회된 엔티티 또는 None
        """
        pass
    
    @abstractmethod
    def search(self, params: ParamsT) -> Tuple[List[ModelT], int]:
        """
        파라미터에 따른 엔티티 검색
        
        Args:
            params: 검색 파라미터
            
        Returns:
            검색된 엔티티 리스트와 총 결과 수
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[ModelT]:
        """
        모든 엔티티 조회
        
        Returns:
            모든 엔티티 리스트
        """
        pass
    
    @abstractmethod
    def create(self, entity: ModelT) -> ModelT:
        """
        엔티티 생성
        
        Args:
            entity: 생성할 엔티티
            
        Returns:
            생성된 엔티티
        """
        pass
    
    @abstractmethod
    def update(self, entity: ModelT) -> ModelT:
        """
        엔티티 업데이트
        
        Args:
            entity: 업데이트할 엔티티
            
        Returns:
            업데이트된 엔티티
        """
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        ID로 엔티티 삭제
        
        Args:
            id: 삭제할 엔티티 ID
            
        Returns:
            삭제 성공 여부
        """
        pass