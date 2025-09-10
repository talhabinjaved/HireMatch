from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str
    secret_key: str
    database_url: str = "sqlite:///./hire_match.db"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "hire-match-vectors"
    
    # OAuth2 Settings
    oauth2_access_token_expire_seconds: int = 3600  # 1 hour
    default_client_rate_limit: int = 1000  # requests per hour
    max_rate_limit: int = 10000  # maximum requests per hour for any client
    
    # Security Settings
    bcrypt_rounds: int = 12
    token_entropy_bytes: int = 32
    
    class Config:
        env_file = ".env"


settings = Settings()
