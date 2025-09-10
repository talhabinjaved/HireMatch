from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import CV, OAuth2Client, AccessToken
from app.schemas import CV as CVSchema
from app.services.auth_service import OAuth2Service
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.shortlist_service import ShortlistService

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

@router.post("/upload", response_model=CVSchema)
async def upload_cv(
    file: UploadFile = File(...),
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Upload CV - requires 'write' scope"""
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
    
    try:
        file_content = await file.read()
        cv = shortlist_service.process_cv_upload(
            file_content, file.filename, client.client_id, db
        )
        return cv
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CV: {str(e)}"
        )


@router.get("/", response_model=List[CVSchema])
def get_cvs(
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Get all CVs for the authenticated client - requires 'read' scope"""
    client, token = client_data
    
    cvs = db.query(CV).filter(CV.client_id == client.client_id).all()
    return cvs


@router.get("/{cv_id}", response_model=CVSchema)
def get_cv(
    cv_id: str,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Get specific CV by ID - requires 'read' scope"""
    client, token = client_data
    
    cv = db.query(CV).filter(
        CV.id == cv_id,
        CV.client_id == client.client_id
    ).first()
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    return cv


@router.delete("/{cv_id}")
def delete_cv(
    cv_id: str,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Delete CV - requires 'write' scope"""
    client, token = client_data
    
    cv = db.query(CV).filter(
        CV.id == cv_id,
        CV.client_id == client.client_id
    ).first()
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    db.delete(cv)
    db.commit()
    
    return {"message": "CV deleted successfully"}