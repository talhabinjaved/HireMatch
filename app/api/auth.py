from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import User, OAuth2Client, AccessToken, APIUsage
from app.schemas import (
    User as UserSchema, Token, UserCreateAdmin, UserUpdate, 
    OAuth2ClientCreate, OAuth2ClientResponse, OAuth2Client as OAuth2ClientSchema,
    OAuth2ClientUpdate, ClientCredentialsToken, APIUsageStats, AccessTokenInfo
)
from app.auth import (
    OAuth2Service, get_current_user, get_current_admin_user, get_current_super_admin_user,
    get_current_client, verify_client_scope, check_rate_limit_middleware,
    create_access_token, create_refresh_token, verify_token
)
from app.config import settings
from datetime import timedelta, datetime
from typing import List, Optional
import time

router = APIRouter()

# Legacy login endpoint for backward compatibility
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Legacy login endpoint for backward compatibility"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not OAuth2Service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    username = verify_token(refresh_token, "refresh")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

# OAuth2 Client Credentials Flow
@router.post("/token", response_model=ClientCredentialsToken)
def get_access_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: Optional[str] = Form("read write"),
    db: Session = Depends(get_db)
):
    """OAuth2 Client Credentials flow - get access token for API access"""
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
    
    # Parse and validate scopes
    requested_scopes = scope.split() if scope else []
    allowed_scopes = client.allowed_scopes or []
    
    # Check if all requested scopes are allowed
    invalid_scopes = [s for s in requested_scopes if s not in allowed_scopes]
    if invalid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scopes: {', '.join(invalid_scopes)}"
        )
    
    # Use allowed scopes if no specific scopes requested
    if not requested_scopes:
        requested_scopes = allowed_scopes
    
    # Create access token
    expires_in = 3600  # 1 hour
    access_token, db_token = OAuth2Service.create_access_token(
        client_id=client.client_id,
        scopes=requested_scopes,
        expires_in=expires_in,
        db=db
    )
    
    return ClientCredentialsToken(
        access_token=access_token,
        token_type="Bearer",
        expires_in=expires_in,
        scope=" ".join(requested_scopes)
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

# User Management (Super Admin only)
@router.get("/users", response_model=List[UserSchema])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_current_super_admin_user)
):
    """Get all users (Super Admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/users", response_model=UserSchema)
def create_user(
    user: UserCreateAdmin, 
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_current_super_admin_user)
):
    """Create a new user (Super Admin only)"""
    # Check for existing email
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check for existing username
    db_username = db.query(User).filter(User.username == user.username).first()
    if db_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    hashed_password = OAuth2Service.get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        is_admin=user.is_admin,
        is_super_admin=user.is_super_admin
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/users/{user_id}", response_model=UserSchema)
def get_user(
    user_id: str, 
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_current_super_admin_user)
):
    """Get user by ID (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_current_super_admin_user)
):
    """Update user (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check email uniqueness
    if user_update.email is not None:
        existing_user = db.query(User).filter(
            User.email == user_update.email, 
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_update.email
    
    # Check username uniqueness
    if user_update.username is not None:
        existing_user = db.query(User).filter(
            User.username == user_update.username, 
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = user_update.username
    
    # Update other fields
    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin
    
    if user_update.is_super_admin is not None:
        user.is_super_admin = user_update.is_super_admin
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    super_admin: User = Depends(get_current_super_admin_user)
):
    """Delete user (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == super_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# OAuth2 Client Management
@router.post("/clients", response_model=OAuth2ClientResponse)
def create_oauth2_client(
    client_data: OAuth2ClientCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Create new OAuth2 client (Admin+ only)"""
    client_id, client_secret = OAuth2Service.generate_client_credentials()
    hashed_secret = OAuth2Service.get_password_hash(client_secret)
    
    db_client = OAuth2Client(
        client_id=client_id,
        client_secret=hashed_secret,
        name=client_data.name,
        description=client_data.description,
        client_type=client_data.client_type,
        allowed_scopes=client_data.allowed_scopes,
        redirect_uris=client_data.redirect_uris,
        rate_limit_per_hour=client_data.rate_limit_per_hour,
        created_by=admin_user.id
    )
    
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    
    return OAuth2ClientResponse(
        id=db_client.id,
        client_id=db_client.client_id,
        client_secret=client_secret,  # Return plain secret only on creation
        name=db_client.name,
        description=db_client.description,
        client_type=db_client.client_type,
        is_active=db_client.is_active,
        allowed_scopes=db_client.allowed_scopes,
        redirect_uris=db_client.redirect_uris,
        rate_limit_per_hour=db_client.rate_limit_per_hour,
        last_used_at=db_client.last_used_at,
        created_by=db_client.created_by,
        created_at=db_client.created_at,
        updated_at=db_client.updated_at
    )

@router.get("/clients", response_model=List[OAuth2ClientSchema])
def get_oauth2_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get OAuth2 clients (Admin+ only)"""
    query = db.query(OAuth2Client)
    
    # Non-super admins can only see their own clients
    if not admin_user.is_super_admin:
        query = query.filter(OAuth2Client.created_by == admin_user.id)
    
    clients = query.offset(skip).limit(limit).all()
    return clients

@router.get("/clients/{client_id}", response_model=OAuth2ClientSchema)
def get_oauth2_client(
    client_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get OAuth2 client by ID (Admin+ only)"""
    query = db.query(OAuth2Client).filter(OAuth2Client.id == client_id)
    
    # Non-super admins can only access their own clients
    if not admin_user.is_super_admin:
        query = query.filter(OAuth2Client.created_by == admin_user.id)
    
    client = query.first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client

@router.put("/clients/{client_id}", response_model=OAuth2ClientSchema)
def update_oauth2_client(
    client_id: str,
    client_update: OAuth2ClientUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Update OAuth2 client (Admin+ only)"""
    query = db.query(OAuth2Client).filter(OAuth2Client.id == client_id)
    
    # Non-super admins can only update their own clients
    if not admin_user.is_super_admin:
        query = query.filter(OAuth2Client.created_by == admin_user.id)
    
    client = query.first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Update fields
    if client_update.name is not None:
        client.name = client_update.name
    if client_update.description is not None:
        client.description = client_update.description
    if client_update.allowed_scopes is not None:
        client.allowed_scopes = client_update.allowed_scopes
    if client_update.redirect_uris is not None:
        client.redirect_uris = client_update.redirect_uris
    if client_update.rate_limit_per_hour is not None:
        client.rate_limit_per_hour = client_update.rate_limit_per_hour
    if client_update.is_active is not None:
        client.is_active = client_update.is_active
    
    db.commit()
    db.refresh(client)
    return client

@router.post("/clients/{client_id}/regenerate-secret", response_model=OAuth2ClientResponse)
def regenerate_client_secret(
    client_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Regenerate client secret (Admin+ only)"""
    query = db.query(OAuth2Client).filter(OAuth2Client.id == client_id)
    
    # Non-super admins can only regenerate their own clients
    if not admin_user.is_super_admin:
        query = query.filter(OAuth2Client.created_by == admin_user.id)
    
    client = query.first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Generate new secret
    _, new_secret = OAuth2Service.generate_client_credentials()
    client.client_secret = OAuth2Service.get_password_hash(new_secret)
    
    # Revoke all existing tokens for this client
    db.query(AccessToken).filter(
        AccessToken.client_id == client.client_id
    ).update({"is_active": False})
    
    db.commit()
    db.refresh(client)
    
    return OAuth2ClientResponse(
        id=client.id,
        client_id=client.client_id,
        client_secret=new_secret,  # Return new plain secret
        name=client.name,
        description=client.description,
        client_type=client.client_type,
        is_active=client.is_active,
        allowed_scopes=client.allowed_scopes,
        redirect_uris=client.redirect_uris,
        rate_limit_per_hour=client.rate_limit_per_hour,
        last_used_at=client.last_used_at,
        created_by=client.created_by,
        created_at=client.created_at,
        updated_at=client.updated_at
    )

@router.delete("/clients/{client_id}")
def delete_oauth2_client(
    client_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Delete OAuth2 client (Admin+ only)"""
    query = db.query(OAuth2Client).filter(OAuth2Client.id == client_id)
    
    # Non-super admins can only delete their own clients
    if not admin_user.is_super_admin:
        query = query.filter(OAuth2Client.created_by == admin_user.id)
    
    client = query.first()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Revoke all tokens for this client
    db.query(AccessToken).filter(
        AccessToken.client_id == client.client_id
    ).update({"is_active": False})
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"}

# Token Management
@router.get("/tokens", response_model=List[AccessTokenInfo])
def get_access_tokens(
    client_id: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get access tokens (Admin+ only)"""
    query = db.query(AccessToken)
    
    if active_only:
        query = query.filter(AccessToken.is_active == True)
    
    if client_id:
        # Verify admin has access to this client
        client_query = db.query(OAuth2Client).filter(OAuth2Client.client_id == client_id)
        if not admin_user.is_super_admin:
            client_query = client_query.filter(OAuth2Client.created_by == admin_user.id)
        
        if not client_query.first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found or no access"
            )
        
        query = query.filter(AccessToken.client_id == client_id)
    elif not admin_user.is_super_admin:
        # Non-super admins can only see tokens for their clients
        user_client_ids = db.query(OAuth2Client.client_id).filter(
            OAuth2Client.created_by == admin_user.id
        ).subquery()
        query = query.filter(AccessToken.client_id.in_(user_client_ids))
    
    tokens = query.order_by(desc(AccessToken.created_at)).offset(skip).limit(limit).all()
    return tokens

# Analytics
@router.get("/analytics/usage/{client_id}", response_model=APIUsageStats)
def get_client_usage_stats(
    client_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get usage statistics for a client (Admin+ only)"""
    # Verify admin has access to this client
    query = db.query(OAuth2Client).filter(OAuth2Client.client_id == client_id)
    if not admin_user.is_super_admin:
        query = query.filter(OAuth2Client.created_by == admin_user.id)
    
    client = query.first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or no access"
        )
    
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_hour = now - timedelta(hours=1)
    
    # Total requests
    total_requests = db.query(APIUsage).filter(
        APIUsage.client_id == client_id
    ).count()
    
    # Requests in last 24 hours
    requests_24h = db.query(APIUsage).filter(
        APIUsage.client_id == client_id,
        APIUsage.request_time >= last_24h
    ).count()
    
    # Requests in last hour
    requests_1h = db.query(APIUsage).filter(
        APIUsage.client_id == client_id,
        APIUsage.request_time >= last_hour
    ).count()
    
    # Average response time
    avg_response = db.query(func.avg(APIUsage.response_time_ms)).filter(
        APIUsage.client_id == client_id,
        APIUsage.request_time >= last_24h
    ).scalar() or 0
    
    # Error rate
    error_requests = db.query(APIUsage).filter(
        APIUsage.client_id == client_id,
        APIUsage.request_time >= last_24h,
        APIUsage.status_code >= 400
    ).count()
    
    error_rate = (error_requests / requests_24h * 100) if requests_24h > 0 else 0
    
    return APIUsageStats(
        client_id=client_id,
        total_requests=total_requests,
        requests_last_24h=requests_24h,
        requests_last_hour=requests_1h,
        average_response_time=float(avg_response),
        error_rate=float(error_rate)
    )

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout (placeholder for token revocation)"""
    return {"message": "Successfully logged out"}