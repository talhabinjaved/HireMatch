# 🚀 Hire Match AI - OAuth2 Authentication System

## Overview

Your authentication system has been completely revamped with a modern OAuth2 implementation that supports:

- **Super Admin** functionality for complete system management
- **Client Credentials Flow** for secure API access
- **Rate limiting** and usage analytics
- **Comprehensive token management**
- **Backward compatibility** with existing user authentication

## 🏗️ Architecture

### User Hierarchy
1. **Super Admin** - Complete system access, can manage all users and clients
2. **Admin** - Can create and manage OAuth2 clients 
3. **Regular User** - Standard application access

### Authentication Methods
1. **Legacy JWT** - For existing user login (backward compatible)
2. **OAuth2 Client Credentials** - For API access by external applications

## 🛠️ Initial Setup

### 1. Run Database Migration
```bash
alembic upgrade head
```

### 2. Create Super Admin Account
```bash
python create_super_admin.py
```

Follow the interactive prompts to create your first super admin account.

### 3. Start the Application
```bash
python run.py
```

## 📋 OAuth2 Client Management

### Creating OAuth2 Clients

As a super admin or admin, you can create OAuth2 clients:

**POST** `/auth/clients`
```json
{
  "name": "My External App",
  "description": "External application accessing our API",
  "client_type": "confidential",
  "allowed_scopes": ["read", "write"],
  "redirect_uris": [],
  "rate_limit_per_hour": 1000
}
```

**Response:**
```json
{
  "id": "client-uuid",
  "client_id": "hm_abc123...",
  "client_secret": "secret-only-shown-once",
  "name": "My External App",
  "description": "External application accessing our API",
  "client_type": "confidential",
  "is_active": true,
  "allowed_scopes": ["read", "write"],
  "redirect_uris": [],
  "rate_limit_per_hour": 1000,
  "created_by": "admin-user-id",
  "created_at": "2024-01-01T12:00:00Z"
}
```

**⚠️ Important:** The `client_secret` is only returned once during creation. Store it securely!

## 🔐 OAuth2 Client Credentials Flow

### 1. Get Access Token

**POST** `/auth/token`
```
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=hm_abc123...
&client_secret=your-secret
&scope=read write
```

**Response:**
```json
{
  "access_token": "hm_access_xyz789...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read write"
}
```

### 2. Use Access Token

Include the token in the Authorization header:
```
Authorization: Bearer hm_access_xyz789...
```

**Example API Call:**
```bash
curl -H "Authorization: Bearer hm_access_xyz789..." \
     -X GET https://your-api.com/cvs/
```

## 🛡️ API Endpoints Security

### Scope Requirements

| Endpoint | Required Scope | Description |
|----------|---------------|-------------|
| `GET /cvs/` | `read` | List CVs |
| `POST /cvs/upload` | `write` | Upload CV |
| `DELETE /cvs/{id}` | `write` | Delete CV |
| `GET /jobs/` | `read` | List jobs |
| `POST /jobs/` | `write` | Create job |
| `POST /shortlist/` | `write` | Create shortlist |

### Rate Limiting

- Default: 1000 requests/hour per client
- Configurable per client
- Returns HTTP 429 when exceeded

## 👤 User Management (Super Admin Only)

### Create User
**POST** `/auth/users`
```json
{
  "email": "user@example.com",
  "username": "newuser",
  "password": "secure-password",
  "is_admin": false,
  "is_super_admin": false
}
```

### Update User
**PUT** `/auth/users/{user_id}`
```json
{
  "is_admin": true,
  "is_active": true
}
```

### List Users
**GET** `/auth/users?skip=0&limit=100`

## 📊 Analytics & Monitoring

### Client Usage Statistics
**GET** `/auth/analytics/usage/{client_id}`

```json
{
  "client_id": "hm_abc123...",
  "total_requests": 15420,
  "requests_last_24h": 234,
  "requests_last_hour": 12,
  "average_response_time": 145.7,
  "error_rate": 2.1
}
```

### Access Token Management
**GET** `/auth/tokens?client_id=hm_abc123&active_only=true`

List all access tokens for monitoring and management.

## 🔧 Client Management Operations

### Regenerate Client Secret
**POST** `/auth/clients/{client_id}/regenerate-secret`

**⚠️ Warning:** This invalidates all existing tokens for the client.

### Update Client Settings
**PUT** `/auth/clients/{client_id}`
```json
{
  "rate_limit_per_hour": 2000,
  "is_active": false,
  "allowed_scopes": ["read"]
}
```

### Revoke Access Token
**POST** `/auth/revoke`
```
Content-Type: application/x-www-form-urlencoded

token=hm_access_xyz789...
```

## 🔒 Security Features

### Token Security
- Tokens are hashed before storage
- Automatic expiration (1 hour default)
- Secure random generation (256-bit entropy)

### Rate Limiting
- Per-client hourly limits
- Configurable thresholds
- Automatic blocking when exceeded

### Audit Trail
- All API calls logged with client context
- Response times tracked
- Error rates monitored

## 🚦 Migration from Legacy System

Your existing user authentication continues to work unchanged:

**POST** `/auth/login` (Legacy)
```json
{
  "username": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "jwt-token...",
  "refresh_token": "refresh-jwt...",
  "token_type": "bearer"
}
```

## 🧪 Testing Your Setup

### 1. Create a Test Client
```bash
# Login as super admin and create a client via API or admin interface
```

### 2. Get Access Token
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_SECRET&scope=read write"
```

### 3. Test API Access
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/cvs/
```

## 📝 Environment Variables

Add to your `.env` file:
```env
# OAuth2 Settings (optional - defaults provided)
OAUTH2_ACCESS_TOKEN_EXPIRE_SECONDS=3600
DEFAULT_CLIENT_RATE_LIMIT=1000
MAX_RATE_LIMIT=10000

# Security Settings
BCRYPT_ROUNDS=12
TOKEN_ENTROPY_BYTES=32
```

## 🆘 Troubleshooting

### Common Issues

1. **"Invalid client credentials"**
   - Verify client_id and client_secret are correct
   - Check if client is active: `GET /auth/clients/{client_id}`

2. **"Rate limit exceeded"**
   - Check current usage: `GET /auth/analytics/usage/{client_id}`
   - Increase limit or wait for reset

3. **"Insufficient scope"**
   - Verify token has required scope
   - Update client allowed_scopes if needed

4. **"Token expired"**
   - Get a new token using client credentials flow
   - Tokens expire after 1 hour by default

### Support Commands

```bash
# Check database migration status
alembic current

# Create new super admin
python create_super_admin.py

# View application logs
tail -f logs/app.log
```

## 🎯 Next Steps

1. **Run the migration:** `alembic upgrade head`
2. **Create super admin:** `python create_super_admin.py`
3. **Start the application:** `python run.py`
4. **Login with super admin credentials**
5. **Create your first OAuth2 client**
6. **Test the OAuth2 flow**
7. **Onboard your team and clients**

Your authentication system is now enterprise-ready with proper OAuth2 support! 🎉
