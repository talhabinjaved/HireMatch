from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    job_descriptions = relationship("JobDescription", back_populates="user")
    cvs = relationship("CV", back_populates="user")
    shortlists = relationship("Shortlist", back_populates="user")


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    summary = Column(Text)
    key_requirements = Column(JSON)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="job_descriptions")
    shortlists = relationship("Shortlist", back_populates="job_description")


class CV(Base):
    __tablename__ = "cvs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    candidate_name = Column(String)
    contact_info = Column(JSON)
    content = Column(Text)
    embedding = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="cvs")
    shortlist_results = relationship("ShortlistResult", back_populates="cv")


class Shortlist(Base):
    __tablename__ = "shortlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"))
    threshold = Column(Float, default=0.6)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="shortlists")
    job_description = relationship("JobDescription", back_populates="shortlists")
    results = relationship("ShortlistResult", back_populates="shortlist")


class ShortlistResult(Base):
    __tablename__ = "shortlist_results"
    
    id = Column(Integer, primary_key=True, index=True)
    shortlist_id = Column(Integer, ForeignKey("shortlists.id"))
    cv_id = Column(Integer, ForeignKey("cvs.id"))
    score = Column(Float)
    match_summary = Column(Text)
    strengths = Column(JSON)
    gaps = Column(JSON)
    reasoning = Column(Text)
    recommendation = Column(String)
    
    shortlist = relationship("Shortlist", back_populates="results")
    cv = relationship("CV", back_populates="shortlist_results")
