from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    is_super_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    created_clients = relationship("OAuth2Client", back_populates="created_by_user")


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    client_id = Column(String, ForeignKey("oauth2_clients.client_id"), nullable=False)
    title = Column(String)
    summary = Column(Text)
    key_requirements = Column(JSON)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("OAuth2Client", foreign_keys=[client_id])
    shortlists = relationship("Shortlist", back_populates="job_description")


class CV(Base):
    __tablename__ = "cvs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    client_id = Column(String, ForeignKey("oauth2_clients.client_id"), nullable=False)
    filename = Column(String)
    candidate_name = Column(String)
    contact_info = Column(JSON)
    content = Column(Text)
    embedding = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("OAuth2Client", foreign_keys=[client_id])
    shortlist_results = relationship("ShortlistResult", back_populates="cv")


class Shortlist(Base):
    __tablename__ = "shortlists"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    client_id = Column(String, ForeignKey("oauth2_clients.client_id"), nullable=False)
    job_description_id = Column(String, ForeignKey("job_descriptions.id"))
    threshold = Column(Float, default=0.6)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    client = relationship("OAuth2Client", foreign_keys=[client_id])
    job_description = relationship("JobDescription", back_populates="shortlists")
    results = relationship("ShortlistResult", back_populates="shortlist")


class ShortlistResult(Base):
    __tablename__ = "shortlist_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    shortlist_id = Column(String, ForeignKey("shortlists.id"))
    cv_id = Column(String, ForeignKey("cvs.id"))
    score = Column(Float)
    match_summary = Column(Text)
    strengths = Column(JSON)
    gaps = Column(JSON)
    reasoning = Column(Text)
    recommendation = Column(String)
    
    shortlist = relationship("Shortlist", back_populates="results")
    cv = relationship("CV", back_populates="shortlist_results")


class OAuth2Client(Base):
    __tablename__ = "oauth2_clients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    client_id = Column(String, unique=True, index=True, nullable=False)
    client_secret = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True))
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    created_by_user = relationship("User", back_populates="created_clients")
    access_tokens = relationship("AccessToken", back_populates="client")
    job_descriptions = relationship("JobDescription", foreign_keys="JobDescription.client_id")
    cvs = relationship("CV", foreign_keys="CV.client_id")
    shortlists = relationship("Shortlist", foreign_keys="Shortlist.client_id")


class AccessToken(Base):
    __tablename__ = "access_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(String, ForeignKey("oauth2_clients.client_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # null for pure OAuth2
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))
    
    client = relationship("OAuth2Client", back_populates="access_tokens")


