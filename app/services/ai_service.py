import openai
import numpy as np
from typing import List, Dict, Any
from app.config import settings


class AIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "text-embedding-3-large"
    
    def generate_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def analyze_cv_match(self, cv_content: str, job_description: str, score: float) -> Dict[str, Any]:
        prompt = f"""
        Analyze this CV against the job description and provide a structured assessment.
        
        Job Description:
        {job_description}
        
        CV Content:
        {cv_content}
        
        Similarity Score: {score:.2f}
        
        Please provide:
        1. A brief match summary (1-2 sentences)
        2. List of strengths (3-5 key points)
        3. List of gaps/weaknesses (2-4 points)
        4. Detailed reasoning for the assessment (2-3 sentences)
        5. Recommendation: "Proceed to interview", "Consider", or "Reject"
        
        Format as JSON:
        {{
            "match_summary": "...",
            "strengths": ["...", "..."],
            "gaps": ["...", "..."],
            "reasoning": "...",
            "recommendation": "..."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an HR expert analyzing CVs against job descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            return {
                "match_summary": f"Analysis based on similarity score of {score:.2f}",
                "strengths": ["Content analysis unavailable"],
                "gaps": ["Content analysis unavailable"],
                "reasoning": f"Assessment based on similarity score. AI analysis failed: {str(e)}",
                "recommendation": "Consider" if score > 0.5 else "Reject"
            }
    
    def extract_job_requirements(self, job_description: str) -> List[str]:
        prompt = f"""
        Extract key technical requirements and skills from this job description.
        Return only the essential requirements as a list.
        
        Job Description:
        {job_description}
        
        Return as JSON array:
        ["requirement1", "requirement2", "requirement3"]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an HR expert extracting job requirements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result if isinstance(result, list) else []
            
        except Exception:
            return ["Requirements extraction failed"]
