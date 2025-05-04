from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Annotated
import logging

from ..dependencies import TrademarkServiceDep
from ..schemas.trademark import (
    TrademarkSearchResponse,
    TrademarkDetail,
    TrademarkSearchParams
)

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/trademarks",
    tags=["trademarks"],
    responses={404: {"description": "Not found"}}
)

@router.get("/", response_model=TrademarkSearchResponse)
async def search_trademarks(
    # 모델을 직접 의존성으로 사용
    params: Annotated[TrademarkSearchParams, Depends()],  
    service: TrademarkServiceDep
):
    """
    상표 검색 API 엔드포인트
    
    검색어, 필터 및 페이징 기능을 제공합니다.
    """
    # 상표 서비스를 통해 검색 수행
    results, total_count = service.search_trademarks(params)
    
    # 검색 로그 기록
    logger.info(f"상표 검색 완료: 검색어='{params.query}', 필터=[상태='{params.status}', 상품코드='{params.product_code}', 날짜범위='{params.from_date}~{params.to_date}'], 결과={total_count}건")
    
    return TrademarkSearchResponse(
        total=total_count,
        offset=params.offset,
        limit=params.limit,
        results=results
    )

@router.get("/{trademark_id}", response_model=TrademarkDetail)
async def get_trademark_detail(
    trademark_id: str,
    service: TrademarkServiceDep
):
    """
    상표 상세 정보 조회 API 엔드포인트
    
    - **trademark_id**: 조회할 상표 ID
    """
    trademark = service.get_trademark_by_id(trademark_id)
    
    if not trademark:
        logger.warning(f"상표 ID '{trademark_id}' 조회 실패: 해당 상표를 찾을 수 없음")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="상표를 찾을 수 없습니다")
    
    logger.info(f"상표 ID '{trademark_id}' 조회 성공")
    return trademark

@router.get("/meta/statuses", response_model=List[str])
async def get_register_statuses(
    service: TrademarkServiceDep
):
    """
    등록 상태 목록 조회 API 엔드포인트
    
    등록 가능한 모든 상태값(등록, 출원, 거절 등)의 목록을 반환합니다.
    """
    statuses = service.get_register_statuses()
    logger.info(f"등록 상태 목록 조회 성공: {len(statuses)}개 항목")
    return statuses
    
@router.get("/meta/product-codes", response_model=List[str])
async def get_product_codes(
    service: TrademarkServiceDep
):
    """
    상품 분류 코드 목록 조회 API 엔드포인트
    
    상표 분류에 사용되는 모든 상품 분류 코드 목록을 반환합니다.
    """
    codes = service.get_product_codes()
    logger.info(f"상품 분류 코드 목록 조회 성공: {len(codes)}개 항목")
    return codes