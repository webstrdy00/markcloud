import pytest
from fastapi.testclient import TestClient

class TestTrademarkAPI:
    """상표 API 엔드포인트 테스트"""
    
    def test_search_trademarks(self, client: TestClient):
        """상표 검색 API 테스트"""
        # 기본 검색
        response = client.get("/api/v1/trademarks")
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "results" in data
        assert data["total"] == 4  # 모의 데이터 4개
        
        # 검색어를 이용한 검색
        response = client.get("/api/v1/trademarks?q=스타벅스")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["productName"] == "스타벅스"
        
        # 상태 필터를 이용한 검색
        response = client.get("/api/v1/trademarks?status=등록")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["registerStatus"] == "등록"
        assert data["results"][1]["registerStatus"] == "등록"
        
        # 페이징 테스트
        response = client.get("/api/v1/trademarks?limit=1&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 4
        assert len(data["results"]) == 1
        assert data["limit"] == 1
        assert data["offset"] == 0
    
    def test_get_trademark_detail(self, client: TestClient):
        """상표 상세 정보 조회 API 테스트"""
        # 존재하는 ID로 조회
        response = client.get("/api/v1/trademarks/1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["applicationNumber"] == "40-2023-0001"
        assert data["productName"] == "스타벅스"
        
        # 존재하지 않는 ID로 조회
        response = client.get("/api/v1/trademarks/999")
        assert response.status_code == 404
    
    def test_get_register_statuses(self, client: TestClient):
        """등록 상태 목록 조회 API 테스트"""
        response = client.get("/api/v1/trademarks/meta/statuses")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert "등록" in data
        assert "출원" in data
    
    def test_get_product_codes(self, client: TestClient):
        """상품 분류 코드 목록 조회 API 테스트"""
        response = client.get("/api/v1/trademarks/meta/product-codes")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # 최소한 필수 코드들은 포함되어 있는지 확인
        required_codes = ["01", "02", "03", "05", "35", "42", "43"]
        for code in required_codes:
            assert code in data