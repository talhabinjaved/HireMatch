from datetime import datetime, timedelta
from typing import Optional, List, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.config import settings
from app.database import get_db
from app.models import User, OAuth2Client, AccessToken, APIUsage
import secrets
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class OAuth2Service:
    """Modern OAuth2 service with comprehensive token and client management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def generate_client_credentials() -> tuple[str, str]:
        """Generate secure client_id and client_secret pair"""
        client_id = f"hm_{secrets.token_urlsafe(24)}"
        client_secret = secrets.token_urlsafe(48)
        return client_id, client_secret
    
    @staticmethod
    def generate_access_token() -> str:
        """Generate a secure access token"""
        return f"hm_access_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Create a hash of the token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def create_access_token(
        client_id: str,
        scopes: List[str],
        user_id: Optional[str] = None,
        expires_in: int = 3600,
        db: Session = None
    ) -> tuple[str, AccessToken]:
        """Create and store access token for OAuth2 client credentials flow"""
        token = OAuth2Service.generate_access_token()
        token_hash = OAuth2Service.hash_token(token)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        db_token = AccessToken(
            token_hash=token_hash,
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            expires_at=expires_at
        )
        
        if db:
            db.add(db_token)
            db.commit()
            db.refresh(db_token)
        
        return token, db_token
    
    @staticmethod
    def verify_client_credentials(
        client_id: str, 
        client_secret: str, 
        db: Session
    ) -> Optional[OAuth2Client]:
        """Verify OAuth2 client credentials"""
        if not client_id or not client_secret:
            return None
        
        client = db.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id,
            OAuth2Client.is_active == True
        ).first()
        
        if not client:
            return None
        
        if not OAuth2Service.verify_password(client_secret, client.client_secret):
            return None
        
        # Update last used timestamp
        client.last_used_at = datetime.utcnow()
        db.commit()
        
        return client
    
    @staticmethod
    def verify_access_token(token: str, db: Session) -> Optional[AccessToken]:
        """Verify and return access token details"""
        token_hash = OAuth2Service.hash_token(token)
        
        db_token = db.query(AccessToken).filter(
            AccessToken.token_hash == token_hash,
            AccessToken.is_active == True,
            AccessToken.expires_at > datetime.utcnow()
        ).first()
        
        if db_token:
            # Update last used timestamp
            db_token.last_used_at = datetime.utcnow()
            db.commit()
        
        return db_token
    
    @staticmethod
    def revoke_token(token: str, db: Session) -> bool:
        """Revoke an access token"""
        token_hash = OAuth2Service.hash_token(token)
        
        db_token = db.query(AccessToken).filter(
            AccessToken.token_hash == token_hash
        ).first()
        
        if db_token:
            db_token.is_active = False
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def check_rate_limit(client_id: str, db: Session) -> bool:
        """Check if client has exceeded rate limit"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        client = db.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id
        ).first()
        
        if not client:
            return False
        
        usage_count = db.query(APIUsage).filter(
            APIUsage.client_id == client_id,
            APIUsage.request_time >= one_hour_ago
        ).count()
        
        return usage_count < client.rate_limit_per_hour
    
    @staticmethod
    def log_api_usage(
        client_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        ip_address: str,
        db: Session
    ):
        """Log API usage for analytics and rate limiting"""
        usage = APIUsage(
            client_id=client_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address
        )
        db.add(usage)
        db.commit()


# Authentication dependencies
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from Bearer token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        # Check if it's an access token (OAuth2 client credentials)
        db_token = OAuth2Service.verify_access_token(token, db)
        if db_token and db_token.user_id:
            user = db.query(User).filter(User.id == db_token.user_id).first()
            if user and user.is_active:
                return user
        
        # Fallback to JWT verification for legacy tokens
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        user = db.query(User).filter(User.username == username).first()
        if user is None or not user.is_active:
            raise credentials_exception
        
        return user
        
    except JWTError:
        raise credentials_exception


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def get_current_super_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated super admin user"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user


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
    db_token = OAuth2Service.verify_access_token(token, db)
    
    if not db_token:
        raise credentials_exception
    
    client = db.query(OAuth2Client).filter(
        OAuth2Client.client_id == db_token.client_id,
        OAuth2Client.is_active == True
    ).first()
    
    if not client:
        raise credentials_exception
    
    return client, db_token


def verify_client_scope(required_scope: str):
    """Decorator to verify client has required scope"""
    def scope_checker(
        client_data: tuple[OAuth2Client, AccessToken] = Depends(get_current_client)
    ):
        client, token = client_data
        if required_scope not in token.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scope. Required: {required_scope}"
            )
        return client, token
    return scope_checker


def check_rate_limit_middleware(
    request: Request,
    client_data: tuple[OAuth2Client, AccessToken] = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """Middleware to check rate limits"""
    client, token = client_data
    
    if not OAuth2Service.check_rate_limit(client.client_id, db):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    return client, token


# Legacy functions for backward compatibility
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return OAuth2Service.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return OAuth2Service.get_password_hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Legacy JWT token creation for backward compatibility"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Legacy refresh token creation"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Legacy token verification"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        token_type_payload: str = payload.get("type")
        if username is None or token_type_payload != token_type:
            return None
        return username
    except JWTError:
        return None

def get_current_user_or_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Union[User, tuple[OAuth2Client, AccessToken]]:
    """
    Flexible authentication that supports both user tokens and OAuth2 client tokens.
    Returns either a User object or a tuple of (OAuth2Client, AccessToken).
    """
    try:
        token = credentials.credentials
        
        # First, try OAuth2 access token
        db_token = OAuth2Service.verify_access_token(token, db)
        if db_token:
            client = db.query(OAuth2Client).filter(
                OAuth2Client.client_id == db_token.client_id,
                OAuth2Client.is_active == True
            ).first()
            if client:
                return client, db_token
        
        # Fallback to JWT user token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username:
            user = db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            if user:
                return user
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_scope_or_user(required_scope: str = None):
    """
    Creates a dependency that accepts either:
    1. A valid user token (full access)
    2. An OAuth2 client token with the required scope
    """
    def dependency(
        auth_result = Depends(get_current_user_or_client),
        db: Session = Depends(get_db)
    ) -> Union[User, OAuth2Client]:
        
        if isinstance(auth_result, User):
            # User authentication - full access
            return auth_result
        
        elif isinstance(auth_result, tuple):
            # OAuth2 client authentication - check scope
            client, token = auth_result
            if required_scope and required_scope not in (token.scopes or []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient scope. Required: {required_scope}"
                )
            return client
        
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication"
            )
    
    return dependency

# Keep legacy functions for backward compatibility
verify_client_credentials = OAuth2Service.verify_client_credentials
generate_client_credentials = OAuth2Service.generate_client_credentials