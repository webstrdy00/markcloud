from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional, Dict, Any, Annotated
from datetime import date
from enum import Enum

# 날짜 타입 열거형 (검증 및 문서화 목적)
class DateFieldType(str, Enum):
    APPLICATION_DATE = "applicationDate"
    REGISTRATION_DATE = "registrationDate"
    PUBLICATION_DATE = "publicationDate"

class TrademarkSearchParams(BaseModel):
    """상표 검색 파라미터"""
    # alias 설정 - API 쿼리 파라미터 q를 내부 필드 query에 바인딩
    query: Optional[str] = Field(None, alias="q", description="검색어 (상표명, 출원번호 등)")
    status: Optional[str] = Field(None, description="등록 상태 필터 (등록, 출원, 거절 등)")
    product_code: Optional[str] = Field(None, description="상품 분류 코드 필터")
    
    # 날짜 필드
    from_date: Optional[str] = Field(None, description="시작 날짜 (YYYYMMDD)")
    to_date: Optional[str] = Field(None, description="종료 날짜 (YYYYMMDD)")
    date_type: DateFieldType = Field(DateFieldType.APPLICATION_DATE, description="날짜 필터 대상 필드")
    
    # 페이징 파라미터
    limit: int = Field(10, ge=1, le=100, description="페이지당 결과 수")
    offset: int = Field(0, ge=0, description="결과 오프셋")
    
    # 날짜 형식 검증
    @field_validator('from_date', 'to_date')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        import re
        if v is None:
            return None
        if not re.match(r'^\d{8}$', v):
            raise ValueError("날짜는 YYYYMMDD 형식이어야 합니다")
        return v
    
    # 날짜 범위 논리 검증
    @model_validator(mode='after')
    def validate_date_range(self) -> 'TrademarkSearchParams':
        if self.from_date and self.to_date:
            # 문자열을 날짜로 변환
            try:
                from_date = date(int(self.from_date[:4]), int(self.from_date[4:6]), int(self.from_date[6:8]))
                to_date = date(int(self.to_date[:4]), int(self.to_date[4:6]), int(self.to_date[6:8]))
                
                # 시작일이 종료일보다 나중이면 오류
                if from_date > to_date:
                    raise ValueError("시작 날짜는 종료 날짜보다 이전이어야 합니다")
            except ValueError as e:
                # 날짜 변환 오류는 이미 field_validator에서 검증됨
                if "날짜는 YYYYMMDD 형식이어야 합니다" not in str(e):
                    raise ValueError(f"잘못된 날짜 형식: {str(e)}")
        return self
    
    # 모델 설정
    model_config = ConfigDict(
        populate_by_name=True,  # 필드 이름과 alias 모두 허용
        arbitrary_types_allowed=True
    )

class SearchResult(BaseModel):
    """검색 결과 아이템"""
    applicationNumber: str
    productName: Optional[str] = None
    productNameEng: Optional[str] = None
    
    # 날짜 필드를 date 타입으로 사용
    applicationDate: Optional[date] = None
    registerStatus: Optional[str] = None
    
    # 명시적 리스트 필드 (필수지만 빈 배열 가능)
    registrationNumber: List[str] = Field(default_factory=list)
    registrationDate: List[date] = Field(default_factory=list)
    
    # 배열 필드
    asignProductMainCodeList: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_encoders = {
            # 날짜 필드 직렬화를 YYYYMMDD 형식으로 통일
            date: lambda v: v.strftime("%Y%m%d") if v else None,
        }
    )

class TrademarkSearchResponse(BaseModel):
    """상표 검색 응답"""
    total: int = Field(..., description="총 결과 수")
    offset: int = Field(..., description="현재 오프셋")
    limit: int = Field(..., description="페이지 크기")
    results: List[SearchResult] = Field(..., description="검색 결과 목록")

class TrademarkDetail(BaseModel):
    """상표 상세 정보"""
    productName: Optional[str] = Field(None, description="상표명(한글)")
    productNameEng: Optional[str] = Field(None, description="상표명(영문)")
    applicationNumber: str = Field(..., description="출원 번호")
    
    # 날짜 필드를 date 타입으로 수정
    applicationDate: Optional[date] = Field(None, description="출원일")
    registerStatus: Optional[str] = Field(None, description="등록 상태")
    publicationNumber: Optional[str] = Field(None, description="공고 번호")
    publicationDate: Optional[date] = Field(None, description="공고일")
    
    # 배열 타입으로 수정
    registrationNumber: Optional[List[str]] = Field(default_factory=list, description="등록 번호")
    registrationDate: Optional[List[date]] = Field(default_factory=list, description="등록일")
    
    # 추가 필드
    registrationPubNumber: Optional[str] = Field(None, description="등록공고 번호")
    registrationPubDate: Optional[date] = Field(None, description="등록공고일")
    
    # 배열 필드 - 명시적 기본값 설정
    internationalRegNumbers: Optional[List[str]] = Field(default_factory=list, description="국제 출원 번호")
    internationalRegDate: Optional[date] = Field(None, description="국제출원일")
    priorityClaimNumList: Optional[List[str]] = Field(default_factory=list, description="우선권 번호")
    priorityClaimDateList: Optional[List[date]] = Field(default_factory=list, description="우선권 일자")
    asignProductMainCodeList: Optional[List[str]] = Field(default_factory=list, description="상품 주 분류 코드")
    asignProductSubCodeList: Optional[List[str]] = Field(default_factory=list, description="상품 유사군 코드")
    viennaCodeList: Optional[List[str]] = Field(default_factory=list, description="비엔나 코드")

    model_config = ConfigDict(
        json_encoders = {
            # 날짜 필드 직렬화를 YYYYMMDD 형식으로 통일
            date: lambda v: v.strftime("%Y%m%d") if v else None,
        }
    )

# 모델 → 스키마 변환 헬퍼 함수
def to_schema(model_obj, schema_class):
    """
    DB 모델 객체를 Pydantic 스키마로 변환
    
    Args:
        model_obj: SQLAlchemy 모델 객체
        schema_class: 변환할 Pydantic 스키마 클래스
        
    Returns:
        변환된 Pydantic 스키마 객체
    """
    return schema_class.model_validate(model_obj, from_attributes=True)

def to_schema_list(model_objs, schema_class):
    """
    DB 모델 객체 리스트를 Pydantic 스키마 리스트로 변환
    
    Args:
        model_objs: SQLAlchemy 모델 객체 리스트
        schema_class: 변환할 Pydantic 스키마 클래스
        
    Returns:
        변환된 Pydantic 스키마 객체 리스트
    """
    return [to_schema(obj, schema_class) for obj in model_objs]