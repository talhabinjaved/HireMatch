from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, OAuth2Client, AccessToken
from app.schemas import (
    OAuth2ClientCreate, OAuth2ClientResponse, OAuth2Client as OAuth2ClientSchema,
    OAuth2ClientUpdate, AccessTokenInfo
)
from app.services.auth_service import AuthService
from app.services.client_service import ClientService
from jose import JWTError
from app.config import settings
from typing import List, Optional

router = APIRouter()
security = HTTPBearer()

def get_super_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Super admin authentication for client management"""
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

# OAuth2 Client Management (Super Admin Only)
@router.post("/", response_model=OAuth2ClientResponse)
def create_oauth2_client(
    client_data: OAuth2ClientCreate,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Create new OAuth2 client (Super Admin only)"""
    db_client, client_secret = ClientService.create_client(
        name=client_data.name,
        description=client_data.description,
        created_by_user_id=super_admin.id,
        db=db
    )
    
    return OAuth2ClientResponse(
        id=db_client.id,
        client_id=db_client.client_id,
        client_secret=client_secret,  # Return plain secret only on creation
        name=db_client.name,
        description=db_client.description,
        is_active=db_client.is_active,
        last_used_at=db_client.last_used_at,
        created_by=db_client.created_by,
        created_at=db_client.created_at,
        updated_at=db_client.updated_at
    )

@router.get("/", response_model=List[OAuth2ClientSchema])
def get_oauth2_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Get all OAuth2 clients (Super Admin only)"""
    return ClientService.get_all_clients(skip=skip, limit=limit, db=db)

@router.get("/{client_id}", response_model=OAuth2ClientSchema)
def get_oauth2_client(
    client_id: str,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Get OAuth2 client by ID (Super Admin only)"""
    client = ClientService.get_client_by_id(client_id, db)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client

@router.put("/{client_id}", response_model=OAuth2ClientSchema)
def update_oauth2_client(
    client_id: str,
    client_update: OAuth2ClientUpdate,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Update OAuth2 client (Super Admin only)"""
    client = ClientService.update_client(
        client_id=client_id,
        name=client_update.name,
        description=client_update.description,
        is_active=client_update.is_active,
        db=db
    )
    
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return client

@router.post("/{client_id}/regenerate-secret", response_model=OAuth2ClientResponse)
def regenerate_client_secret(
    client_id: str,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Regenerate client secret (Super Admin only)"""
    client, new_secret = ClientService.regenerate_client_secret(client_id, db)
    
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return OAuth2ClientResponse(
        id=client.id,
        client_id=client.client_id,
        client_secret=new_secret,  # Return new plain secret
        name=client.name,
        description=client.description,
        is_active=client.is_active,
        last_used_at=client.last_used_at,
        created_by=client.created_by,
        created_at=client.created_at,
        updated_at=client.updated_at
    )

@router.delete("/{client_id}")
def delete_oauth2_client(
    client_id: str,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Delete OAuth2 client and all associated data (Super Admin only)"""
    success = ClientService.delete_client(client_id, db)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    return {"message": "Client and all associated data deleted successfully"}

# Token Management
@router.get("/tokens", response_model=List[AccessTokenInfo])
def get_access_tokens(
    client_id: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_super_admin_user)
):
    """Get access tokens (Super Admin only)"""
    return ClientService.get_client_tokens(
        client_id=client_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
        db=db
    )
