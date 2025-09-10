from sqlalchemy.orm import Session
from app.models import OAuth2Client, AccessToken, CV, JobDescription, Shortlist
from typing import Optional

class AnalyticsService:
    """Service for client analytics and system statistics"""
    
    @staticmethod
    def get_client_statistics(client_id: str, db: Session) -> Optional[dict]:
        """Get comprehensive statistics for a specific client"""
        # Verify client exists
        client = db.query(OAuth2Client).filter(
            OAuth2Client.client_id == client_id
        ).first()
        
        if not client:
            return None
        
        # Count client data
        total_cvs = db.query(CV).filter(CV.client_id == client_id).count()
        total_jobs = db.query(JobDescription).filter(JobDescription.client_id == client_id).count()
        total_shortlists = db.query(Shortlist).filter(Shortlist.client_id == client_id).count()
        
        return {
            "client_id": client_id,
            "client_name": client.name,
            "total_cvs": total_cvs,
            "total_jobs": total_jobs,
            "total_shortlists": total_shortlists,
            "is_active": client.is_active,
            "last_used_at": client.last_used_at,
            "created_at": client.created_at
        }
    
    @staticmethod
    def get_system_overview(db: Session) -> dict:
        """Get system-wide analytics overview"""
        # Client statistics
        total_clients = db.query(OAuth2Client).count()
        active_clients = db.query(OAuth2Client).filter(OAuth2Client.is_active == True).count()
        
        # Token statistics
        total_tokens = db.query(AccessToken).filter(AccessToken.is_active == True).count()
        
        # Data statistics
        total_cvs = db.query(CV).count()
        total_jobs = db.query(JobDescription).count()
        total_shortlists = db.query(Shortlist).count()
        
        return {
            "total_clients": total_clients,
            "active_clients": active_clients,
            "active_tokens": total_tokens,
            "total_cvs": total_cvs,
            "total_jobs": total_jobs,
            "total_shortlists": total_shortlists,
            "system_status": "operational"
        }
    
    @staticmethod
    def get_all_clients_summary(db: Session) -> list:
        """Get summary statistics for all clients"""
        clients = db.query(OAuth2Client).all()
        summaries = []
        
        for client in clients:
            stats = AnalyticsService.get_client_statistics(client.client_id, db)
            if stats:
                summaries.append(stats)
        
        return summaries
