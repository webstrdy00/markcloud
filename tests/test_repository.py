import pytest
from datetime import date
from app.models.trademark import Trademark
from app.schemas.trademark import TrademarkSearchParams
from app.repositories.mock.trademark_repository import MockTrademarkRepository

class TestMockTrademarkRepository:
    """Mock 상표 저장소 테스트"""
    
    def test_find_by_id(self, mock_repository):
        """ID로 상표 조회 테스트"""
        # 존재하는 ID로 조회
        trademark = mock_repository.find_by_id("40-2023-0001")
        assert trademark is not None
        assert trademark.applicationNumber == "40-2023-0001"
        assert trademark.productName == "스타벅스"
        
        # 존재하지 않는 ID로 조회
        trademark = mock_repository.find_by_id("non-existent-id")
        assert trademark is None
    
    def test_search_with_query(self, mock_repository):
        """검색어를 이용한 상표 검색 테스트"""
        # 검색 파라미터 생성
        params = TrademarkSearchParams(
            query="스타벅스",
            limit=10,
            offset=0
        )
        
        # 검색 실행
        results, total = mock_repository.search(params)
        
        # 결과 검증
        assert total == 1
        assert len(results) == 1
        assert results[0].productName == "스타벅스"
    
    def test_search_with_status_filter(self, mock_repository):
        """상태 필터를 이용한 검색 테스트"""
        # 등록 상태 필터 검색
        params = TrademarkSearchParams(
            status="등록",
            limit=10,
            offset=0
        )
        
        # 검색 실행
        results, total = mock_repository.search(params)
        
        # 결과 검증
        assert total == 2  # 스타벅스, 삼성전자
        assert len(results) == 2
        assert results[0].registerStatus == "등록"
        assert results[1].registerStatus == "등록"
        
        # 출원 상태 필터 검색
        params = TrademarkSearchParams(
            status="출원",
            limit=10,
            offset=0
        )
        
        # 검색 실행
        results, total = mock_repository.search(params)
        
        # 결과 검증
        assert total == 1  # 커피빈
        assert len(results) == 1
        assert results[0].registerStatus == "출원"
    
    def test_search_with_product_code_filter(self, mock_repository):
        """상품 코드 필터를 이용한 검색 테스트"""
        # 43번 코드 (식음료) 필터 검색
        params = TrademarkSearchParams(
            product_code="43",
            limit=10,
            offset=0
        )
        
        # 검색 실행
        results, total = mock_repository.search(params)
        
        # 결과 검증
        assert total == 3  # 스타벅스, 커피빈, 삼성전자
        assert len(results) == 3
        assert "43" in results[0].asignProductMainCodeList
        assert "43" in results[1].asignProductMainCodeList
        assert "43" in results[2].asignProductMainCodeList
        
        # 09번 코드 (전자기기) 필터 검색
        params = TrademarkSearchParams(
            product_code="09",
            limit=10,
            offset=0
        )
        
        # 검색 실행
        results, total = mock_repository.search(params)
        
        # 결과 검증
        assert total == 1  # 삼성전자
        assert len(results) == 1
        assert "09" in results[0].asignProductMainCodeList
    
    def test_search_pagination(self, mock_repository):
        """페이징 테스트"""
        # 첫 페이지 (2개 제한)
        params = TrademarkSearchParams(
            limit=2,
            offset=0
        )
        
        # 검색 실행
        results, total = mock_repository.search(params)
        
        # 결과 검증
        assert total == 3  # 전체 3개
        assert len(results) == 2  # 페이지당 2개
        
        # 두 번째 페이지
        params = TrademarkSearchParams(
            limit=2,
            offset=2
        )
        
        # 검색 실행
        results, total = mock_repository.search(params)
        
        # 결과 검증
        assert total == 3  # 전체 3개
        assert len(results) == 1  # 마지막 페이지는 1개
    
    def test_create_and_update(self, mock_repository):
        """상표 생성 및 업데이트 테스트"""
        # 새 상표 생성
        new_trademark = Trademark(
            applicationNumber="40-2023-0004",
            productName="이디야커피",
            productNameEng="Ediya Coffee",
            applicationDate=date(2023, 4, 1),
            registerStatus="출원"
        )
        
        # 저장
        created = mock_repository.create(new_trademark)
        
        # 생성 결과 검증
        assert created.applicationNumber == "40-2023-0004"
        assert created.productName == "이디야커피"
        
        # ID로 조회
        retrieved = mock_repository.find_by_id("40-2023-0004")
        assert retrieved is not None
        assert retrieved.productName == "이디야커피"
        
        # 상표 업데이트
        retrieved.registerStatus = "등록"
        updated = mock_repository.update(retrieved)
        
        # 업데이트 결과 검증
        assert updated.registerStatus == "등록"
        
        # 다시 조회하여 확인
        after_update = mock_repository.find_by_id("40-2023-0004")
        assert after_update.registerStatus == "등록"
    
    def test_delete(self, mock_repository):
        """상표 삭제 테스트"""
        # 삭제 전 확인
        before_delete = mock_repository.find_by_id("40-2023-0001")
        assert before_delete is not None
        
        # 삭제 실행
        result = mock_repository.delete("40-2023-0001")
        
        # 삭제 결과 검증
        assert result == True
        
        # 삭제 후 확인
        after_delete = mock_repository.find_by_id("40-2023-0001")
        assert after_delete is None
        
        # 존재하지 않는 ID 삭제
        result = mock_repository.delete("non-existent-id")
        assert result == False
    
    def test_get_register_statuses(self, mock_repository):
        """등록 상태 목록 조회 테스트"""
        statuses = mock_repository.get_register_statuses()
        assert len(statuses) == 4
        assert "등록" in statuses
        assert "출원" in statuses
        assert "거절" in statuses
        assert "실효" in statuses
    
    def test_get_product_codes(self, mock_repository):
        """상품 분류 코드 목록 조회 테스트"""
        codes = mock_repository.get_product_codes()
        assert len(codes) == 7
        assert "01" in codes
        assert "42" in codes
        assert "43" in codes