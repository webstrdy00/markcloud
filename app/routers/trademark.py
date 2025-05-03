from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
import re
import logging
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.trademark import (
    TrademarkSearchResponse,
    TrademarkDetail,
    TrademarkSearchParams,
    SearchResult
)
from ..services.trademark import TrademarkService
from ..config import settings

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/trademarks",
    tags=["trademarks"],
    responses={404: {"description": "Not found"}}
)

def get_trademark_service(db: Session = Depends(get_db)):
    return TrademarkService(db)

@router.get("/", response_model=TrademarkSearchResponse) 
async def search_trademarks(
    q: Optional[str] = Query(None, description="검색어 (상표명, 출원번호 등)"),
    status: Optional[str] = Query(None, description="등록 상태 (등록, 출원, 거절 등)"),
    product_code: Optional[str] = Query(None, description="상품 분류 코드"),
    from_date: Optional[str] = Query(None, description="시작 날짜 (YYYYMMDD)"),
    to_date: Optional[str] = Query(None, description="종료 날짜 (YYYYMMDD)"),
    date_type: Optional[str] = Query("applicationDate", description="날짜 타입 (applicationDate, registrationDate, publicationDate)"),
    limit: int = Query(settings.DEFAULT_LIMIT, ge=1, le=settings.MAX_LIMIT, description="페이지당 결과 수"),
    offset: int = Query(0, ge=0, description="결과 오프셋"),
    trademark_service: TrademarkService = Depends(get_trademark_service)
):
    """
    상표 검색 API 엔드포인트
    
    - **q**: 검색어 (상표명, 출원번호 등)
    - **status**: 등록 상태 필터 (등록, 출원, 거절 등)
    - **product_code**: 상품 분류 코드 필터
    - **from_date**: 시작 날짜 필터 (YYYYMMDD)
    - **to_date**: 종료 날짜 필터 (YYYYMMDD)
    - **date_type**: 날짜 필터의 대상 필드 (applicationDate, registrationDate, publicationDate)
    - **limit**: 페이지당 결과 수
    - **offset**: 결과 오프셋 (페이징용)
    """
    try:
        # 날짜 형식 검증
        if from_date and not re.match(r'^\d{8}$', from_date):
            raise HTTPException(status_code=400, detail="시작 날짜는 YYYYMMDD 형식이어야 합니다")
        
        if to_date and not re.match(r'^\d{8}$', to_date):
            raise HTTPException(status_code=400, detail="종료 날짜는 YYYYMMDD 형식이어야 합니다")
        
        # 검색 파라미터 설정
        search_params = TrademarkSearchParams(
            query=q,
            status=status,
            product_code=product_code,
            from_date=from_date,
            to_date=to_date,
            date_type=date_type,
            limit=limit,
            offset=offset
        )
        
        # 상표 서비스를 통해 검색 수행 (의존성 주입으로 변경됨)
        results, total_count = trademark_service.search_trademarks(search_params)
        
        # 검색 로그 기록
        logger.info(f"상표 검색 완료: 검색어='{q}', 필터=[상태='{status}', 상품코드='{product_code}', 날짜범위='{from_date}~{to_date}'], 결과={total_count}건")
        
        return TrademarkSearchResponse(  # 이름 수정: Tradmark -> Trademark
            total=total_count,
            offset=offset,
            limit=limit,
            results=results
        )
    except HTTPException:
        # 이미 처리된 HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        # 예상치 못한 오류 처리
        logger.error(f"상표 검색 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="상표 검색 중 서버 오류가 발생했습니다")

@router.get("/{trademark_id}", response_model=TrademarkDetail)  
async def get_trademark_detail(
    trademark_id: str,
    trademark_service: TrademarkService = Depends(get_trademark_service) 
):
    """
    상표 상세 정보 조회 API 엔드포인트
    
    - **trademark_id**: 조회할 상표 ID (applicationNumber)
    """
    try:
        trademark = trademark_service.get_trademark_by_id(trademark_id)
        
        if not trademark:
            logger.warning(f"상표 ID '{trademark_id}' 조회 실패: 해당 상표를 찾을 수 없음")
            raise HTTPException(status_code=404, detail="상표를 찾을 수 없습니다")
        
        logger.info(f"상표 ID '{trademark_id}' 조회 성공")
        return trademark
    except HTTPException:
        # 이미 처리된 HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        # 예상치 못한 오류 처리
        logger.error(f"상표 상세 정보 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="상표 상세 정보 조회 중 서버 오류가 발생했습니다")
    
@router.get("/meta/statuses", response_model=List[str])
async def get_register_statuses(
    trademark_service: TrademarkService = Depends(get_trademark_service) 
):
    """
    등록 상태 목록 조회 API 엔드포인트
    
    등록 가능한 모든 상태값(등록, 출원, 거절 등)의 목록을 반환합니다.
    """
    try:
        statuses = trademark_service.get_register_statuses()
        logger.info(f"등록 상태 목록 조회 성공: {len(statuses)}개 항목")
        return statuses
    except Exception as e:
        logger.error(f"등록 상태 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="등록 상태 목록 조회 중 서버 오류가 발생했습니다")
    
@router.get("/meta/product-codes", response_model=List[str])
async def get_product_codes(
    trademark_service: TrademarkService = Depends(get_trademark_service) 
):
    """
    상품 분류 코드 목록 조회 API 엔드포인트
    
    상표 분류에 사용되는 모든 상품 분류 코드 목록을 반환합니다.
    """
    try:
        codes = trademark_service.get_product_codes()
        logger.info(f"상품 분류 코드 목록 조회 성공: {len(codes)}개 항목")
        return codes
    except Exception as e:
        logger.error(f"상품 분류 코드 목록 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="상품 분류 코드 목록 조회 중 서버 오류가 발생했습니다")