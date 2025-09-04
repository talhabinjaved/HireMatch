# HireMatch AI - CV Shortlisting SaaS

An AI-powered SaaS application that automatically shortlists CVs against job descriptions using OpenAI's text embeddings and GPT models.

## Features

- **Multi-format CV Support**: Upload CVs in PDF, DOCX, or TXT formats
- **AI-powered Analysis**: Uses OpenAI embeddings and GPT for intelligent matching
- **Comprehensive Reports**: Detailed analysis with strengths, gaps, and recommendations
- **Multi-tenant Architecture**: Secure user isolation and data privacy
- **Configurable Thresholds**: Set custom scoring thresholds for shortlisting
- **JWT Authentication**: Secure user authentication and authorization

## Tech Stack

- **Backend**: FastAPI
- **Database**: SQLite (can be upgraded to PostgreSQL)
- **AI**: OpenAI GPT-3.5-turbo and text-embedding-3-large
- **Authentication**: JWT with bcrypt password hashing
- **File Processing**: python-docx, pdfplumber
- **Vector Similarity**: NumPy for cosine similarity calculations

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Docker (optional)

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd hire-match-ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp env.example .env
```

5. Update `.env` with your credentials:
```env
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///./hire_match.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Running the Application

#### Development Mode
```bash
uvicorn app.main:app --reload
```

#### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Using Docker
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login

#### CV Management
- `POST /cvs/upload` - Upload CV files
- `GET /cvs/` - List user's CVs
- `GET /cvs/{cv_id}` - Get specific CV
- `DELETE /cvs/{cv_id}` - Delete CV

#### Job Descriptions
- `POST /jobs/` - Upload job description file (PDF, DOCX, TXT)
- `GET /jobs/` - List job descriptions
- `GET /jobs/{job_id}` - Get specific job
- `PUT /jobs/{job_id}` - Update job description with new file
- `DELETE /jobs/{job_id}` - Delete job description

#### Shortlisting
- `POST /shortlist/` - Run shortlisting analysis
- `GET /shortlist/` - Get shortlist history
- `GET /shortlist/{shortlist_id}` - Get specific shortlist
- `DELETE /shortlist/{shortlist_id}` - Delete shortlist

## Usage Example

### 1. Register and Login
```bash
# Register
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"testuser","password":"password123"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -d "username=testuser&password=password123"
```

### 2. Upload CVs
```bash
curl -X POST "http://localhost:8000/cvs/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@resume.pdf"
```

### 3. Upload Job Description
```bash
curl -X POST "http://localhost:8000/jobs/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@job_description.pdf"
```

### 4. Run Shortlisting
```bash
curl -X POST "http://localhost:8000/shortlist/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description_id": 1,
    "threshold": 0.6
  }'
```

## Testing

Run the test suite:
```bash
pytest tests/
```

## Project Structure

```
hire-match-ai/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── cvs.py
│   │   ├── jobs.py
│   │   └── shortlist.py
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py
│       ├── shortlist_service.py
│       └── text_extractor.py
├── tests/
│   ├── __init__.py
│   └── test_auth.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── env.example
└── README.md
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: JWT secret key for token signing
- `DATABASE_URL`: Database connection string
- `ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

### Database

The application uses SQLite by default for simplicity. For production, consider using PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/hirematch
```

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Multi-tenant data isolation
- Input validation with Pydantic
- CORS middleware for web client support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on the repository.
