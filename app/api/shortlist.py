from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Shortlist, OAuth2Client, AccessToken, JobDescription, CV
from app.schemas import ShortlistCreate, Shortlist as ShortlistSchema, ShortlistReport
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

@router.post("/", response_model=ShortlistReport)
def create_shortlist(
    shortlist_data: ShortlistCreate,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Create shortlist evaluation - requires 'write' scope"""
    client, token = client_data
    
    # Verify job description belongs to this client
    job = db.query(JobDescription).filter(
        JobDescription.id == shortlist_data.job_description_id,
        JobDescription.client_id == client.client_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found or not accessible"
        )
    
    # Verify all CVs belong to this client
    client_cv_ids = db.query(CV.id).filter(
        CV.client_id == client.client_id,
        CV.id.in_(shortlist_data.cv_ids)
    ).all()
    
    client_cv_ids = [cv.id for cv in client_cv_ids]
    
    # Check if any requested CVs don't belong to this client
    invalid_cv_ids = set(shortlist_data.cv_ids) - set(client_cv_ids)
    if invalid_cv_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CVs not found or not accessible: {list(invalid_cv_ids)}"
        )
    
    try:
        report = shortlist_service.run_shortlisting(
            client.client_id,
            shortlist_data.job_description_id,
            shortlist_data.cv_ids,
            shortlist_data.threshold,
            db
        )
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating shortlist: {str(e)}"
        )


@router.get("/", response_model=List[ShortlistSchema])
def get_shortlists(
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Get all shortlists for the authenticated client - requires 'read' scope"""
    client, token = client_data
    
    shortlists = db.query(Shortlist).filter(
        Shortlist.client_id == client.client_id
    ).all()
    return shortlists


@router.get("/{shortlist_id}", response_model=ShortlistSchema)
def get_shortlist(
    shortlist_id: str,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Get specific shortlist by ID - requires 'read' scope"""
    client, token = client_data
    
    shortlist = db.query(Shortlist).filter(
        Shortlist.id == shortlist_id,
        Shortlist.client_id == client.client_id
    ).first()
    
    if not shortlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist not found"
        )
    
    return shortlist


@router.get("/{shortlist_id}/report", response_model=ShortlistReport)
def get_shortlist_report(
    shortlist_id: str,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Get detailed shortlist report - requires 'read' scope"""
    client, token = client_data
    
    shortlist = db.query(Shortlist).filter(
        Shortlist.id == shortlist_id,
        Shortlist.client_id == client.client_id
    ).first()
    
    if not shortlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist not found"
        )
    
    try:
        report = shortlist_service.generate_shortlist_report(shortlist, db)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@router.delete("/{shortlist_id}")
def delete_shortlist(
    shortlist_id: str,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(require_client()),
    db: Session = Depends(get_db)
):
    """Delete shortlist - requires 'write' scope"""
    client, token = client_data
    
    shortlist = db.query(Shortlist).filter(
        Shortlist.id == shortlist_id,
        Shortlist.client_id == client.client_id
    ).first()
    
    if not shortlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist not found"
        )
    
    db.delete(shortlist)
    db.commit()
    
    return {"message": "Shortlist deleted successfully"}