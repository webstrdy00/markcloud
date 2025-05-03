from typing import List, TypeVar, Type, Optional
from pydantic import BaseModel

# 제네릭 타입 변수 정의
ModelT = TypeVar('ModelT')  # SQLAlchemy 모델 타입
SchemaT = TypeVar('SchemaT', bound=BaseModel)  # Pydantic 스키마 타입

def to_schema(model_obj: Optional[ModelT], schema_class: Type[SchemaT]) -> Optional[SchemaT]:
    """
    DB 모델 객체를 Pydantic 스키마로 변환
    
    Args:
        model_obj: SQLAlchemy 모델 객체
        schema_class: 변환할 Pydantic 스키마 클래스
        
    Returns:
        변환된 Pydantic 스키마 객체
    """
    if model_obj is None:
        return None
    return schema_class.model_validate(model_obj, from_attributes=True)

def to_schema_list(model_objs: Optional[List[ModelT]], schema_class: Type[SchemaT]) -> List[SchemaT]:
    """
    DB 모델 객체 리스트를 Pydantic 스키마 리스트로 변환
    
    Args:
        model_objs: SQLAlchemy 모델 객체 리스트
        schema_class: 변환할 Pydantic 스키마 클래스
        
    Returns:
        변환된 Pydantic 스키마 객체 리스트
    """
    if not model_objs:
        return []
    return [to_schema(obj, schema_class) for obj in model_objs]