from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Shortlist
from app.schemas import ShortlistCreate, Shortlist as ShortlistSchema, ShortlistReport
from app.auth import get_current_user
from app.services.shortlist_service import ShortlistService

router = APIRouter()
shortlist_service = ShortlistService()


@router.post("/", response_model=ShortlistReport)
def create_shortlist(
    shortlist_data: ShortlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        report = shortlist_service.run_shortlisting(
            current_user.id,
            shortlist_data.job_description_id,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shortlists = shortlist_service.get_shortlist_history(current_user.id, db)
    return shortlists


@router.get("/{shortlist_id}", response_model=ShortlistSchema)
def get_shortlist(
    shortlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shortlist = shortlist_service.get_shortlist_details(shortlist_id, current_user.id, db)
    
    if not shortlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist not found"
        )
    
    return shortlist


@router.delete("/{shortlist_id}")
def delete_shortlist(
    shortlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    shortlist = shortlist_service.get_shortlist_details(shortlist_id, current_user.id, db)
    
    if not shortlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shortlist not found"
        )
    
    db.delete(shortlist)
    db.commit()
    
    return {"message": "Shortlist deleted successfully"}
