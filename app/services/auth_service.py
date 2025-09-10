from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User, OAuth2Client, AccessToken
import secrets
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Main authentication service for password handling and JWT management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT token for super admin authentication"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create refresh token for super admin"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    @staticmethod
    def verify_jwt_token(token: str, token_type: str = "access") -> Optional[str]:
        """Verify JWT token and return username"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            token_type_payload: str = payload.get("type")
            if username is None or token_type_payload != token_type:
                return None
            return username
        except JWTError:
            return None

    @staticmethod
    def authenticate_super_admin(username: str, password: str, db: Session) -> Optional[User]:
        """Authenticate super admin user"""
        user = db.query(User).filter(
            User.username == username,
            User.is_super_admin == True,
            User.is_active == True
        ).first()
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        
        return user


class OAuth2Service:
    """OAuth2 service for client credentials flow"""
    
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
            user_id=None,  # Pure OAuth2 - no user context
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
        
        if not AuthService.verify_password(client_secret, client.client_secret):
            return None
        
        # Update last used timestamp
        client.last_used_at = datetime.utcnow()
        db.commit()
        
        return client
    
    @staticmethod
    def verify_access_token(token: str, db: Session) -> Optional[tuple[AccessToken, OAuth2Client]]:
        """Verify and return access token with client details"""
        token_hash = OAuth2Service.hash_token(token)
        
        db_token = db.query(AccessToken).filter(
            AccessToken.token_hash == token_hash,
            AccessToken.is_active == True,
            AccessToken.expires_at > datetime.utcnow()
        ).first()
        
        if not db_token:
            return None
        
        client = db.query(OAuth2Client).filter(
            OAuth2Client.client_id == db_token.client_id,
            OAuth2Client.is_active == True
        ).first()
        
        if not client:
            return None
        
        # Update last used timestamp
        db_token.last_used_at = datetime.utcnow()
        db.commit()
        
        return db_token, client
    
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


