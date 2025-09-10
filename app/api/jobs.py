from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import JobDescription, OAuth2Client, AccessToken
from app.schemas import JobDescriptionCreate, JobDescription as JobDescriptionSchema
from app.services.auth_service import OAuth2Service
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.shortlist_service import ShortlistService
from app.services.text_extractor import TextExtractor
import os
import tempfile

router = APIRouter()
shortlist_service = ShortlistService()
security = HTTPBearer()

def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[OAuth2Client, AccessToken]:
    """Get current OAuth2 client from Bearer token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    result = OAuth2Service.verify_access_token(token, db)
    
    if not result:
        raise credentials_exception
    
    db_token, client = result
    return client, db_token

def require_client():
    """Simple client authentication dependency"""
    def client_checker(
        client_data: tuple[OAuth2Client, AccessToken] = Depends(get_current_client)
    ) -> tuple[OAuth2Client, AccessToken]:
        return client_data
    return client_checker

@router.post("/", response_model=JobDescriptionSchema)
async def create_job_description(
    file: UploadFile = File(...),
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Create job description from uploaded file - requires 'write' scope"""
    client, token = client_data
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_extension = file.filename.lower().split('.')[-1]
    
    if f'.{file_extension}' not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        temp_path = tmp_file.name
    
    try:
        # Extract text content
        extractor = TextExtractor()
        content = extractor.extract_text(temp_path)
        
        if not content or len(content.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract meaningful content from the file"
            )
        
        # Process job description with AI
        job_details = await shortlist_service.process_job_description(content)
        
        # Create job description record
        job_description = JobDescription(
            client_id=client.client_id,
            title=job_details.get("title", "Untitled Position"),
            summary=job_details.get("summary", ""),
            key_requirements=job_details.get("key_requirements", []),
            content=content
        )
        
        db.add(job_description)
        db.commit()
        db.refresh(job_description)
        
        return job_description
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing job description: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/", response_model=List[JobDescriptionSchema])
def get_job_descriptions(
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Get all job descriptions for the authenticated client - requires 'read' scope"""
    client, token = client_data
    
    jobs = db.query(JobDescription).filter(
        JobDescription.client_id == client.client_id
    ).all()
    return jobs


@router.get("/{job_id}", response_model=JobDescriptionSchema)
def get_job_description(
    job_id: str,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Get specific job description by ID - requires 'read' scope"""
    client, token = client_data
    
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.client_id == client.client_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )
    
    return job


@router.delete("/{job_id}")
def delete_job_description(
    job_id: str,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Delete job description - requires 'write' scope"""
    client, token = client_data
    
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.client_id == client.client_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )
    
    db.delete(job)
    db.commit()
    
    return {"message": "Job description deleted successfully"}