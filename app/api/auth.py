from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, OAuth2Client, AccessToken
from app.schemas import Token, ClientCredentialsToken
from app.services.auth_service import AuthService, OAuth2Service
from jose import JWTError
from app.config import settings
from datetime import timedelta

router = APIRouter()
security = HTTPBearer()

def get_super_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Super admin authentication using JWT tokens"""
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

# Super Admin Authentication
@router.post("/super-admin/login", response_model=Token)
def super_admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Super admin login - for dashboard access"""
    user = AuthService.authenticate_super_admin(form_data.username, form_data.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid super admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = AuthService.create_jwt_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = AuthService.create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/super-admin/refresh", response_model=Token)
def refresh_super_admin_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh super admin access token"""
    username = AuthService.verify_jwt_token(refresh_token, "refresh")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(
        User.username == username,
        User.is_super_admin == True,
        User.is_active == True
    ).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Super admin not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = AuthService.create_jwt_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    new_refresh_token = AuthService.create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

# OAuth2 Client Credentials Flow (Main API Authentication)
@router.post("/token", response_model=ClientCredentialsToken)
def get_access_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    db: Session = Depends(get_db)
):
    """OAuth2 Client Credentials flow - Main API authentication method"""
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only 'client_credentials' grant type is supported"
        )
    
    # Verify client credentials
    client = OAuth2Service.verify_client_credentials(client_id, client_secret, db)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token (full access to all endpoints)
    expires_in = settings.oauth2_access_token_expire_seconds
    access_token, db_token = OAuth2Service.create_access_token(
        client_id=client.client_id,
        expires_in=expires_in,
        db=db
    )
    
    return ClientCredentialsToken(
        access_token=access_token,
        token_type="Bearer",
        expires_in=expires_in
    )

@router.post("/revoke")
def revoke_token(
    token: str = Form(...),
    client_data: tuple = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Revoke an access token"""
    success = OAuth2Service.revoke_token(token, db)
    return {"revoked": success}

@router.post("/logout")
def logout():
    """Logout endpoint (placeholder for token cleanup)"""
    return {"message": "Logged out successfully"}