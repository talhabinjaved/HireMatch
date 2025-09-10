from sqlalchemy.orm import Session
from app.models import OAuth2Client, AccessToken, User
from app.services.auth_service import AuthService, OAuth2Service
from typing import List, Optional

class ClientService:
    """Service for OAuth2 client management operations"""
    
    @staticmethod
    def create_client(
        name: str,
        description: str,
        created_by_user_id: str,
        db: Session
    ) -> tuple[OAuth2Client, str]:
        """Create a new OAuth2 client and return client with plain secret"""
        client_id, client_secret = OAuth2Service.generate_client_credentials()
        hashed_secret = AuthService.get_password_hash(client_secret)
        
        db_client = OAuth2Client(
            client_id=client_id,
            client_secret=hashed_secret,
            name=name,
            description=description,
            created_by=created_by_user_id
        )
        
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        
        return db_client, client_secret
    
    @staticmethod
    def get_all_clients(skip: int = 0, limit: int = 100, db: Session = None) -> List[OAuth2Client]:
        """Get all OAuth2 clients with pagination"""
        return db.query(OAuth2Client).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_client_by_id(client_id: str, db: Session) -> Optional[OAuth2Client]:
        """Get OAuth2 client by ID"""
        return db.query(OAuth2Client).filter(OAuth2Client.id == client_id).first()
    
    @staticmethod
    def update_client(
        client_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        db: Session = None
    ) -> Optional[OAuth2Client]:
        """Update OAuth2 client"""
        client = db.query(OAuth2Client).filter(OAuth2Client.id == client_id).first()
        if not client:
            return None
        
        if name is not None:
            client.name = name
        if description is not None:
            client.description = description
        if is_active is not None:
            client.is_active = is_active
        
        db.commit()
        db.refresh(client)
        return client
    
    @staticmethod
    def regenerate_client_secret(client_id: str, db: Session) -> tuple[Optional[OAuth2Client], Optional[str]]:
        """Regenerate client secret and revoke all existing tokens"""
        client = db.query(OAuth2Client).filter(OAuth2Client.id == client_id).first()
        if not client:
            return None, None
        
        # Generate new secret
        _, new_secret = OAuth2Service.generate_client_credentials()
        client.client_secret = AuthService.get_password_hash(new_secret)
        
        # Revoke all existing tokens for this client
        db.query(AccessToken).filter(
            AccessToken.client_id == client.client_id
        ).update({"is_active": False})
        
        db.commit()
        db.refresh(client)
        
        return client, new_secret
    
    @staticmethod
    def delete_client(client_id: str, db: Session) -> bool:
        """Delete OAuth2 client and revoke all associated tokens"""
        client = db.query(OAuth2Client).filter(OAuth2Client.id == client_id).first()
        if not client:
            return False
        
        # Revoke all tokens for this client
        db.query(AccessToken).filter(
            AccessToken.client_id == client.client_id
        ).update({"is_active": False})
        
        # Delete client (CVs, Jobs, Shortlists will be cascade deleted)
        db.delete(client)
        db.commit()
        return True
    
    @staticmethod
    def get_client_tokens(
        client_id: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
        db: Session = None
    ) -> List[AccessToken]:
        """Get access tokens with optional filtering"""
        query = db.query(AccessToken)
        
        if active_only:
            query = query.filter(AccessToken.is_active == True)
        
        if client_id:
            query = query.filter(AccessToken.client_id == client_id)
        
        return query.offset(skip).limit(limit).all()
