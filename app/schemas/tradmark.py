from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date
from typing import Annotated

class TrademarkSearchParams(BaseModel):
    """상표 검색 파라미터"""
    query: Optional[str] = None
    status: Optional[str] = None
    product_code: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    date_type: str = "applicationDate"
    limit: int = 10
    offset: int = 0

class SearchResult(BaseModel):
    """검색 결과 아이템"""
    applicationNumber: str
    productName: Optional[str] = None
    productNameEng: Optional[str] = None
    
    # 날짜 필드를 date 타입으로 수정 (선택사항)
    # 문자열 형식으로 유지하려면 이 부분 주석 처리
    applicationDate: Optional[date] = None
    registerStatus: Optional[str] = None
    
    # 명시적 리스트 필드 (필수지만 빈 배열 가능)
    # 빈 리스트와 null을 구분해야 하는 경우
    registrationNumber: List[str] = Field(default_factory=list)
    registrationDate: List[date] = Field(default_factory=list)
    
    # 배열 필드
    asignProductMainCodeList: List[str] = Field(default_factory=list)

    class Config:
        # 날짜 필드에 대한 직렬화 설정
        json_encoders = {
            date: lambda v: v.strftime("%Y%m%d") if v else None,
        }
        # 빈 리스트는 null로 변환하지 않음
        # 빈 리스트와 null을 구분해야 할 경우 주석 처리
        # list: lambda v: v if v else None

class TrademarkSearchResponse(BaseModel):
    """상표 검색 응답"""
    total: int
    offset: int
    limit: int
    results: List[SearchResult]

class TrademarkDetail(BaseModel):
    """상표 상세 정보"""
    productName: Optional[str] = None
    productNameEng: Optional[str] = None
    applicationNumber: str
    
    # 날짜 필드를 date 타입으로 수정 (선택사항)
    applicationDate: Optional[date] = None
    registerStatus: Optional[str] = None
    publicationNumber: Optional[str] = None
    publicationDate: Optional[date] = None
    
    # 배열 타입으로 수정 - null 항목을 가질 수 있음
    # Optional[List[str]] = None: 필드 자체가 null일 수 있음 (추천)
    # List[Optional[str]] = []: 리스트 내 요소가 null일 수 있음 
    registrationNumber: Optional[List[str]] = Field(default_factory=list)
    registrationDate: Optional[List[date]] = Field(default_factory=list)
    
    # 추가 필드
    registrationPubNumber: Optional[str] = None
    registrationPubDate: Optional[date] = None
    
    # 배열 필드 - 명시적 기본값 설정
    internationalRegNumbers: Optional[List[str]] = Field(default_factory=list)
    internationalRegDate: Optional[date] = None
    priorityClaimNumList: Optional[List[str]] = Field(default_factory=list)
    priorityClaimDateList: Optional[List[date]] = Field(default_factory=list)
    asignProductMainCodeList: Optional[List[str]] = Field(default_factory=list)
    asignProductSubCodeList: Optional[List[str]] = Field(default_factory=list)
    viennaCodeList: Optional[List[str]] = Field(default_factory=list)

    class Config:
        # 날짜 필드를 YYYYMMDD 형식으로 직렬화
        json_encoders = {
            date: lambda v: v.strftime("%Y%m%d") if v else None,
        }
        # exclude_none=True  # null 값을 가진 필드 제외 (선택적)