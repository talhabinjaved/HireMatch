from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Union
from app.database import get_db
from app.models import User, CV
from app.schemas import CV as CVSchema
from app.auth import get_current_user, require_scope_or_user
from app.services.shortlist_service import ShortlistService

router = APIRouter()
shortlist_service = ShortlistService()

@router.post("/upload", response_model=CVSchema)
async def upload_cv(
    file: UploadFile = File(...),
    auth_user: Union[User, object] = Depends(require_scope_or_user("write")),
    db: Session = Depends(get_db)
):
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
    
    # Get user ID for CV operations
    user_id = auth_user.id if isinstance(auth_user, User) else None
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required for CV operations"
        )
    
    try:
        file_content = await file.read()
        cv = shortlist_service.process_cv_upload(
            file_content, file.filename, user_id, db
        )
        return cv
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CV: {str(e)}"
        )


@router.get("/", response_model=List[CVSchema])
def get_cvs(
    auth_user: Union[User, object] = Depends(require_scope_or_user("read")),
    db: Session = Depends(get_db)
):
    user_id = auth_user.id if isinstance(auth_user, User) else None
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required for CV operations"
        )
    
    cvs = db.query(CV).filter(CV.user_id == user_id).all()
    return cvs


@router.get("/{cv_id}", response_model=CVSchema)
def get_cv(
    cv_id: str,
    auth_user: Union[User, object] = Depends(require_scope_or_user("read")),
    db: Session = Depends(get_db)
):
    user_id = auth_user.id if isinstance(auth_user, User) else None
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required for CV operations"
        )
    
    cv = db.query(CV).filter(
        CV.id == cv_id,
        CV.user_id == user_id
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
    auth_user: Union[User, object] = Depends(require_scope_or_user("write")),
    db: Session = Depends(get_db)
):
    user_id = auth_user.id if isinstance(auth_user, User) else None
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required for CV operations"
        )
    
    cv = db.query(CV).filter(
        CV.id == cv_id,
        CV.user_id == user_id
    ).first()
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    db.delete(cv)
    db.commit()
    
    return {"message": "CV deleted successfully"}
