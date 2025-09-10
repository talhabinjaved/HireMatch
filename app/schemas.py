from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: str
    is_admin: bool = False
    is_super_admin: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class JobDescriptionBase(BaseModel):
    title: str
    summary: str
    key_requirements: List[str]
    content: str


class JobDescriptionCreate(BaseModel):
    pass


class JobDescription(JobDescriptionBase):
    id: str
    user_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CVBase(BaseModel):
    candidate_name: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None


class CVCreate(CVBase):
    pass


class CV(CVBase):
    id: str
    user_id: str
    filename: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ShortlistResultBase(BaseModel):
    score: float
    match_summary: str
    strengths: List[str]
    gaps: List[str]
    reasoning: str
    recommendation: str


class ShortlistResultCreate(ShortlistResultBase):
    cv_id: str


class ShortlistResult(ShortlistResultBase):
    id: str
    shortlist_id: str
    cv: CV
    
    class Config:
        from_attributes = True


class ShortlistBase(BaseModel):
    threshold: float = 0.6


class ShortlistCreate(ShortlistBase):
    job_description_id: str
    cv_ids: List[str]


class Shortlist(ShortlistBase):
    id: str
    user_id: str
    job_description_id: str
    created_at: datetime
    results: List[ShortlistResult]
    
    class Config:
        from_attributes = True


class ShortlistReport(BaseModel):
    job_description: JobDescription
    shortlisted: List[ShortlistResult]
    rejected: List[ShortlistResult]
    threshold: float
    total_candidates: int
    shortlisted_count: int
    rejected_count: int


class UserCreateAdmin(BaseModel):
    email: EmailStr
    username: str
    password: str
    is_admin: bool = False
    is_super_admin: bool = False


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_admin: Optional[bool] = None
    is_super_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class OAuth2ClientBase(BaseModel):
    name: str
    description: Optional[str] = None
    client_type: str = "confidential"  # confidential or public
    allowed_scopes: List[str] = ["read", "write"]
    redirect_uris: List[str] = []
    rate_limit_per_hour: int = 1000


class OAuth2ClientCreate(OAuth2ClientBase):
    pass


class OAuth2ClientUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_scopes: Optional[List[str]] = None
    redirect_uris: Optional[List[str]] = None
    rate_limit_per_hour: Optional[int] = None
    is_active: Optional[bool] = None


class OAuth2Client(OAuth2ClientBase):
    id: str
    client_id: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OAuth2ClientResponse(OAuth2Client):
    client_secret: str


class ClientCredentialsToken(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str


class APIUsageStats(BaseModel):
    client_id: str
    total_requests: int
    requests_last_24h: int
    requests_last_hour: int
    average_response_time: float
    error_rate: float


class AccessTokenInfo(BaseModel):
    id: str
    client_id: str
    scopes: List[str]
    is_active: bool
    expires_at: datetime
    created_at: datetime
    last_used_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
