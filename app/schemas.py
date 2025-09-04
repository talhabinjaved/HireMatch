from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
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
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CVBase(BaseModel):
    candidate_name: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None


class CVCreate(CVBase):
    pass


class CV(CVBase):
    id: int
    user_id: int
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
    cv_id: int


class ShortlistResult(ShortlistResultBase):
    id: int
    shortlist_id: int
    cv: CV
    
    class Config:
        from_attributes = True


class ShortlistBase(BaseModel):
    threshold: float = 0.6


class ShortlistCreate(ShortlistBase):
    job_description_id: int
    cv_ids: List[int]


class Shortlist(ShortlistBase):
    id: int
    user_id: int
    job_description_id: int
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
