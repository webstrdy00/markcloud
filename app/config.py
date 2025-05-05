import os
import json
from pydantic_settings import BaseSettings
from typing import List, Union
from dotenv import load_dotenv
from pydantic import field_validator

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    """애플리케이션 설정"""
    # 앱 설정
    APP_NAME: str = os.getenv("APP_NAME", "상표 검색 API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    
    # 환경 설정 (development, production, testing)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # API 설정
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # CORS 설정
    CORS_ORIGINS: Union[str, List[str]] = "*"  # 타입 확장
    
    # 데이터 파일 경로
    DATA_FILE_PATH: str = os.getenv("DATA_FILE_PATH", os.path.join(os.path.dirname(__file__), "data", "trademark_sample.json"))
    
    # 검색 설정
    DEFAULT_LIMIT: int = int(os.getenv("DEFAULT_LIMIT", "10"))
    MAX_LIMIT: int = int(os.getenv("MAX_LIMIT", "100"))
    
    # 로깅 설정 (가능한 값: DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://trademark_user:your_password@localhost:5432/db_name")
    
    # CORS_ORIGINS 필드에 대한 검증기 향상
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            # JSON 리스트 문자열 처리
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # 쉼표 구분 문자열 처리
            return [p.strip() for p in v.split(",") if p.strip()]
        raise TypeError("CORS_ORIGINS must be str or list")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

# 설정 인스턴스 생성
settings = Settings()