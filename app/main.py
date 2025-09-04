from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.models import Base
from app.api import auth, cvs, jobs, shortlist

app = FastAPI(
    title="HireMatch AI",
    description="AI-powered CV shortlisting SaaS application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(cvs.router, prefix="/cvs", tags=["CV Management"])
app.include_router(jobs.router, prefix="/jobs", tags=["Job Descriptions"])
app.include_router(shortlist.router, prefix="/shortlist", tags=["Shortlisting"])


@app.get("/")
def read_root():
    return {
        "message": "Welcome to HireMatch AI",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
