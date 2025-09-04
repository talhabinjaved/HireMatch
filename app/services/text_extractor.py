import os
from typing import Optional, Tuple
from docx import Document
import pdfplumber


class TextExtractor:
    @staticmethod
    def extract_text(file_path: str) -> Tuple[str, Optional[str], Optional[dict]]:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.txt':
            return TextExtractor._extract_txt(file_path)
        elif file_extension == '.docx':
            return TextExtractor._extract_docx(file_path)
        elif file_extension == '.pdf':
            return TextExtractor._extract_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    @staticmethod
    def _extract_txt(file_path: str) -> Tuple[str, Optional[str], Optional[dict]]:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content, None, None
    
    @staticmethod
    def _extract_docx(file_path: str) -> Tuple[str, Optional[str], Optional[dict]]:
        doc = Document(file_path)
        content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        candidate_name = TextExtractor._extract_candidate_name(content)
        contact_info = TextExtractor._extract_contact_info(content)
        
        return content, candidate_name, contact_info
    
    @staticmethod
    def _extract_pdf(file_path: str) -> Tuple[str, Optional[str], Optional[dict]]:
        content = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"
        
        candidate_name = TextExtractor._extract_candidate_name(content)
        contact_info = TextExtractor._extract_contact_info(content)
        
        return content, candidate_name, contact_info
    
    @staticmethod
    def _extract_candidate_name(content: str) -> Optional[str]:
        lines = content.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if line and len(line) > 2 and len(line) < 100:
                if not any(char.isdigit() for char in line):
                    return line
        return None
    
    @staticmethod
    def _extract_contact_info(content: str) -> Optional[dict]:
        import re
        
        contact_info = {}
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        
        emails = re.findall(email_pattern, content)
        if emails:
            contact_info['email'] = emails[0]
        
        phones = re.findall(phone_pattern, content)
        if phones:
            phone = ''.join(phones[0])
            if phone.startswith('+1'):
                contact_info['phone'] = f"+1-{phone[2:3]}-{phone[3:6]}-{phone[6:10]}"
            else:
                contact_info['phone'] = f"+1-{phone[0:3]}-{phone[3:6]}-{phone[6:10]}"
        
        return contact_info if contact_info else None
