# HireMatch AI - Pure OAuth2 CV Shortlisting SaaS

An enterprise-grade AI-powered SaaS application that automatically shortlists CVs against job descriptions using OpenAI's text embeddings and GPT models. Built with a **pure OAuth2 client credentials architecture** for secure multi-client API access.

## 🏗️ System Architecture

### Pure OAuth2 Design
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Super Admin   │────│  OAuth2 Clients  │────│  Client Data    │
│                 │    │                  │    │                 │
│ • Onboard       │    │ • client_id      │    │ • CVs           │
│   clients       │    │ • client_secret  │    │ • Jobs          │
│ • View usage    │    │ • rate_limits    │    │ • Shortlists    │
│ • Analytics     │    │ • access_tokens  │    │ • Usage logs    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow
1. **Super Admin** creates OAuth2 clients → Gets `client_id`/`client_secret`
2. **Client** uses credentials → Gets access token with full API access
3. **Client** uploads CVs/jobs → Data linked to that `client_id`
4. **All operations** are isolated per client - complete data segregation

### Authentication Methods
- **Super Admin**: Legacy JWT tokens (for client management dashboard only)
- **API Clients**: OAuth2 Client Credentials flow (main API access)

## ✨ Features

### Core Functionality
- **Multi-format CV Support**: Upload CVs in PDF, DOCX, or TXT formats
- **AI-powered Analysis**: Uses OpenAI embeddings and GPT for intelligent matching
- **Comprehensive Reports**: Detailed analysis with strengths, gaps, and recommendations
- **Configurable Thresholds**: Set custom scoring thresholds for shortlisting

### Enterprise Features
- **Pure OAuth2 Architecture**: Industry-standard client credentials flow
- **Complete Data Isolation**: Each client's data is completely segregated
- **Client Analytics**: Simple data statistics (CVs, Jobs, Shortlists)
- **Super Admin Dashboard**: Client onboarding and management
- **Token Management**: Full OAuth2 token lifecycle management

## 🛠️ Tech Stack

- **Backend**: FastAPI with OAuth2 implementation
- **Database**: SQLite (production-ready for PostgreSQL)
- **AI**: OpenAI GPT-3.5-turbo and text-embedding-3-large
- **Authentication**: Pure OAuth2 Client Credentials + JWT for super admin
- **File Processing**: python-docx, pdfplumber
- **Vector Similarity**: NumPy for cosine similarity calculations
- **Security**: bcrypt password hashing, secure token generation

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key

### 1. Environment Setup

```bash
# Clone and setup
git clone <repository-url>
cd hire-match-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your OpenAI API key and secret key
```

### 2. Database Setup

```bash
# Run migrations
alembic upgrade head
```

### 3. Create Super Admin

```bash
# Interactive super admin creation
python create_super_admin.py
```

### 4. Start Application

```bash
# Development
python run.py

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 🔐 Authentication System

### Super Admin Authentication (Client Management)

Super admins use JWT tokens to manage OAuth2 clients:

```bash
# Login as super admin
curl -X POST "http://localhost:8000/auth/super-admin/login" \
  -d "username=your_admin_username&password=your_admin_password"

# Response: { "access_token": "jwt_token...", "token_type": "bearer" }
```

### OAuth2 Client Credentials Flow (API Access)

Main API authentication for all clients:

```bash
# Get access token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=hm_abc123...&client_secret=your_secret"

# Response: { "access_token": "hm_access_xyz...", "token_type": "Bearer", "expires_in": 3600 }

# Use token for API calls
curl -H "Authorization: Bearer hm_access_xyz..." \
     "http://localhost:8000/cvs/"
```

## 📋 API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

### Super Admin Endpoints (JWT Authentication)

```bash
# Authentication
POST   /auth/super-admin/login          # Super admin login
POST   /auth/super-admin/refresh        # Refresh admin token

# Client Management  
POST   /clients/                        # Create OAuth2 client
GET    /clients/                        # List all clients  
GET    /clients/{client_id}             # Get client details
PUT    /clients/{client_id}             # Update client
DELETE /clients/{client_id}             # Delete client
POST   /clients/{id}/regenerate-secret  # Regenerate secret
GET    /clients/tokens                  # List access tokens

# Analytics
GET    /analytics/client/{client_id}    # Client statistics (CVs, Jobs, Shortlists)
GET    /analytics/overview              # System overview  
GET    /analytics/clients               # All clients summary
```

### Client API Endpoints (OAuth2 Authentication)

All endpoints require `Authorization: Bearer {access_token}` header:

```bash
# CV Management
POST   /cvs/upload                 # Upload CV file
GET    /cvs/                       # List client's CVs
GET    /cvs/{cv_id}               # Get specific CV
DELETE /cvs/{cv_id}               # Delete CV

# Job Management  
POST   /jobs/                      # Upload job description
GET    /jobs/                      # List client's jobs
GET    /jobs/{job_id}             # Get specific job
DELETE /jobs/{job_id}             # Delete job

# Shortlisting
POST   /shortlist/                 # Run CV shortlisting
GET    /shortlist/                 # List client's shortlists
GET    /shortlist/{id}            # Get specific shortlist
GET    /shortlist/{id}/report     # Get detailed report
DELETE /shortlist/{id}            # Delete shortlist

# Token Management
POST   /auth/revoke               # Revoke access token
```

## 💼 Complete Usage Example

### 1. Super Admin: Create OAuth2 Client

```bash
# Login as super admin
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:8000/auth/super-admin/login" \
  -d "username=admin&password=password" | jq -r '.access_token')

# Create client
curl -X POST "http://localhost:8000/clients/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Recruitment Agency XYZ",
    "description": "External recruitment agency client"
  }'

# Response includes client_id and client_secret (save securely!)
```

### 2. Client: Get Access Token

```bash
# Get access token using client credentials
ACCESS_TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=hm_abc123...&client_secret=secret..." \
  | jq -r '.access_token')
```

### 3. Client: Upload CV and Job

```bash
# Upload CV
CV_ID=$(curl -s -X POST "http://localhost:8000/cvs/upload" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@resume.pdf" | jq -r '.id')

# Upload job description
JOB_ID=$(curl -s -X POST "http://localhost:8000/jobs/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@job_description.pdf" | jq -r '.id')
```

### 4. Client: Run Shortlisting

```bash
# Run shortlisting analysis
curl -X POST "http://localhost:8000/shortlist/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_description_id\": \"$JOB_ID\",
    \"cv_ids\": [\"$CV_ID\"],
    \"threshold\": 0.6
  }"
```

## 🗄️ Database Schema

### Core Tables

**oauth2_clients**
- `client_id` (Primary OAuth2 identifier)
- `client_secret` (Hashed)
- `name`, `description`
- `is_active`, `created_by` (super admin)

**access_tokens**
- `token_hash` (Hashed access token)
- `client_id` (Foreign key)
- `expires_at`, `is_active`

**cvs**
- `id`, `client_id` (Foreign key)
- `filename`, `content`, `embedding`
- `candidate_name`, `contact_info`

**job_descriptions**
- `id`, `client_id` (Foreign key)  
- `title`, `summary`, `key_requirements`
- `content`

**shortlists**
- `id`, `client_id` (Foreign key)
- `job_description_id`, `threshold`

**shortlist_results**
- `id`, `shortlist_id`, `cv_id`
- `score`, `match_summary`, `strengths`, `gaps`
- `reasoning`, `recommendation`


## ⚙️ Configuration

### Environment Variables

```env
# Core Configuration
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_jwt_secret_key_for_super_admin
DATABASE_URL=sqlite:///./hire_match.db

# OAuth2 Settings
OAUTH2_ACCESS_TOKEN_EXPIRE_SECONDS=3600

# Security Settings  
BCRYPT_ROUNDS=12
TOKEN_ENTROPY_BYTES=32
```

### Production Setup

For production, use PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/hirematch
```

## 🔒 Security Features

### OAuth2 Security
- **Secure Token Generation**: 256-bit entropy tokens
- **Token Hashing**: SHA-256 hashed storage
- **Token Expiration**: 1-hour default expiration
- **Client Isolation**: Complete client data segregation

### General Security
- **Password Hashing**: bcrypt with configurable rounds
- **Input Validation**: Comprehensive Pydantic validation
- **CORS Configuration**: Secure cross-origin support
- **SQL Injection Protection**: SQLAlchemy ORM

## 📊 Analytics

### Client Statistics
- Total CVs uploaded per client
- Total job descriptions created per client
- Total shortlists completed per client
- Client activity tracking

### Super Admin Dashboard
- Client management interface
- System-wide analytics overview
- Token lifecycle management
- Client usage statistics

## 🏢 Multi-Tenancy

### Complete Data Isolation
- Each client's data is linked to their `client_id`
- No cross-client data access possible
- Automatic filtering on all queries
- Secure by design architecture

### Client Onboarding
1. Super admin creates OAuth2 client
2. Client receives `client_id` and `client_secret`
3. Client uses credentials to get access tokens
4. All API operations are isolated to that client

## 🧪 Testing

```bash
# Run test suite
pytest tests/

# Test OAuth2 flow
pytest tests/test_oauth2.py

# Test client isolation
pytest tests/test_multi_tenancy.py
```

## 📁 Project Structure

```
hire-match-ai/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration settings
│   ├── database.py            # Database connection
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   ├── api/
│   │   ├── auth.py            # Authentication endpoints only
│   │   ├── clients.py         # Client management endpoints
│   │   ├── analytics.py       # Analytics endpoints
│   │   ├── cvs.py             # CV management
│   │   ├── jobs.py            # Job description management
│   │   └── shortlist.py       # Shortlisting operations
│   └── services/
│       ├── auth_service.py    # Authentication business logic
│       ├── client_service.py  # OAuth2 client management
│       ├── analytics_service.py # Client analytics and statistics
│       ├── ai_service.py      # OpenAI integration
│       ├── shortlist_service.py # Core business logic
│       ├── text_extractor.py  # Document processing
│       └── pinecone_service.py # Vector storage (optional)
├── alembic/                   # Database migrations
├── create_super_admin.py      # Super admin setup script
├── requirements.txt           # Python dependencies
├── env.example               # Environment template
└── README.md                 # This file
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run
docker-compose up --build

# Production environment
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Create super admin
python create_super_admin.py

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔄 Migration from Legacy System

If migrating from a user-based system:

1. **Data Migration**: Link existing data to new client accounts
2. **Authentication Update**: Replace user tokens with OAuth2 flow  
3. **API Updates**: Update client applications to use client credentials
4. **Testing**: Verify complete data isolation

## 🛠️ Development

### Adding New Features

1. **Database Changes**: Create Alembic migration
2. **Models**: Update SQLAlchemy models
3. **Schemas**: Add Pydantic validation schemas
4. **Endpoints**: Implement API endpoints with OAuth2 auth
5. **Tests**: Add comprehensive test coverage

### Client Data Pattern

All data models follow this pattern:
```python
class YourModel(Base):
    id = Column(String, primary_key=True, default=uuid4)
    client_id = Column(String, ForeignKey("oauth2_clients.client_id"), nullable=False)
    # ... other fields
    
    client = relationship("OAuth2Client", foreign_keys=[client_id])
```

## 📞 Support

- **Issues**: Open GitHub issue for bugs/features
- **Documentation**: Visit `/docs` endpoint for API reference
- **Architecture Questions**: Review this README for system design

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🎯 Perfect for**: Recruitment agencies, HR departments, talent acquisition teams requiring secure, isolated CV processing with enterprise-grade OAuth2 authentication.