from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import ClientStats
from app.services.auth_service import AuthService
from app.services.analytics_service import AnalyticsService
from jose import JWTError
from typing import List

router = APIRouter()
security = HTTPBearer()

def get_super_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Super admin authentication for analytics"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Super admin authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        username = AuthService.verify_jwt_token(token, "access")
        if username is None:
            raise credentials_exception
        
        user = db.query(User).filter(
            User.username == username,
            User.is_active == True,
            User.is_super_admin == True
        ).first()
        
        if user is None:
            raise credentials_exception
        
        return user
        
    except JWTError:
        raise credentials_exception

# Analytics Endpoints (Super Admin Only)
@router.get("/client/{client_id}", response_model=ClientStats)
def get_client_statistics(
    client_id: str,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Get statistics for a specific client (Super Admin only)"""
    stats = AnalyticsService.get_client_statistics(client_id, db)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return stats

@router.get("/overview")
def get_system_overview(
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Get system-wide analytics overview (Super Admin only)"""
    return AnalyticsService.get_system_overview(db)

@router.get("/clients")
def get_all_clients_statistics(
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Get statistics for all clients (Super Admin only)"""
    return AnalyticsService.get_all_clients_summary(db)
