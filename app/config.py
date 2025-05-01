import os
from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    """애플리케이션 설정"""
    # 앱 설정
    APP_NAME: str = os.getenv("APP_NAME", "상표 검색 API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    
    # 환경 설정
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, production, testing
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # API 설정
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # CORS 설정
    CORS_ORIGINS: List[str] = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")]
    
    # 데이터 파일 경로
    DATA_FILE_PATH: str = os.getenv("DATA_FILE_PATH", os.path.join(os.path.dirname(__file__), "data", "trademark_sample.json"))
    
    # 검색 설정
    DEFAULT_LIMIT: int = int(os.getenv("DEFAULT_LIMIT", "10"))
    MAX_LIMIT: int = int(os.getenv("MAX_LIMIT", "100"))
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://trademark_user:your_password@localhost:5432/db_name")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

# 설정 인스턴스 생성
settings = Settings()