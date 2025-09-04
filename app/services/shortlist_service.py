from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import User, JobDescription, CV, Shortlist, ShortlistResult
from app.schemas import ShortlistReport
from app.services.ai_service import AIService
from app.services.text_extractor import TextExtractor
import os
import tempfile


class ShortlistService:
    def __init__(self):
        self.ai_service = AIService()
    
    def process_cv_upload(self, file_content: bytes, filename: str, user_id: int, db: Session) -> CV:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            content, candidate_name, contact_info = TextExtractor.extract_text(temp_file_path)
            
            embedding = self.ai_service.generate_embedding(content)
            
            cv = CV(
                user_id=user_id,
                filename=filename,
                candidate_name=candidate_name,
                contact_info=contact_info,
                content=content,
                embedding=embedding
            )
            
            db.add(cv)
            db.commit()
            db.refresh(cv)
            
            return cv
            
        finally:
            os.unlink(temp_file_path)
    
    def process_job_description(self, job_data: Dict[str, Any], user_id: int, db: Session) -> JobDescription:
        content = job_data.get('content', '')
        title = job_data.get('title', 'Job Description')
        summary = job_data.get('summary', '')
        
        key_requirements = self.ai_service.extract_job_requirements(content)
        
        job_description = JobDescription(
            user_id=user_id,
            title=title,
            summary=summary,
            key_requirements=key_requirements,
            content=content
        )
        
        db.add(job_description)
        db.commit()
        db.refresh(job_description)
        
        return job_description
    
    def run_shortlisting(self, user_id: int, job_description_id: int, threshold: float, db: Session) -> ShortlistReport:
        user = db.query(User).filter(User.id == user_id).first()
        job_description = db.query(JobDescription).filter(JobDescription.id == job_description_id).first()
        cvs = db.query(CV).filter(CV.user_id == user_id).all()
        
        if not job_description or not cvs:
            raise ValueError("Job description or CVs not found")
        
        job_embedding = self.ai_service.generate_embedding(job_description.content)
        
        shortlist = Shortlist(
            user_id=user_id,
            job_description_id=job_description_id,
            threshold=threshold
        )
        db.add(shortlist)
        db.commit()
        
        shortlisted_results = []
        rejected_results = []
        
        for cv in cvs:
            cv_embedding = cv.embedding
            similarity_score = self.ai_service.calculate_similarity(cv_embedding, job_embedding)
            
            analysis = self.ai_service.analyze_cv_match(cv.content, job_description.content, similarity_score)
            
            shortlist_result = ShortlistResult(
                shortlist_id=shortlist.id,
                cv_id=cv.id,
                score=similarity_score,
                match_summary=analysis.get('match_summary', ''),
                strengths=analysis.get('strengths', []),
                gaps=analysis.get('gaps', []),
                reasoning=analysis.get('reasoning', ''),
                recommendation=analysis.get('recommendation', 'Consider')
            )
            
            db.add(shortlist_result)
            
            if similarity_score >= threshold:
                shortlisted_results.append(shortlist_result)
            else:
                rejected_results.append(shortlist_result)
        
        db.commit()
        
        return ShortlistReport(
            job_description=job_description,
            shortlisted=shortlisted_results,
            rejected=rejected_results,
            threshold=threshold,
            total_candidates=len(cvs),
            shortlisted_count=len(shortlisted_results),
            rejected_count=len(rejected_results)
        )
    
    def get_shortlist_history(self, user_id: int, db: Session) -> List[Shortlist]:
        return db.query(Shortlist).filter(Shortlist.user_id == user_id).all()
    
    def get_shortlist_details(self, shortlist_id: int, user_id: int, db: Session) -> Shortlist:
        return db.query(Shortlist).filter(
            Shortlist.id == shortlist_id,
            Shortlist.user_id == user_id
        ).first()
