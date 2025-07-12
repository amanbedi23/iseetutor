# Security Implementation Guide

This document outlines the security measures implemented in the ISEE Tutor system.

## Overview

The security implementation includes:
- JWT-based authentication
- Role-based access control (RBAC)
- Input validation and sanitization
- Rate limiting
- Security headers
- SQL injection prevention
- XSS protection

## Authentication

### JWT Tokens
- Access tokens expire after 30 minutes
- Refresh tokens expire after 7 days
- Tokens use HS256 algorithm
- Secret key must be changed in production

### User Registration
```python
POST /api/auth/register
{
  "username": "student123",
  "email": "student@example.com",
  "password": "SecurePass123!",
  "age": 12,
  "grade_level": 6,
  "parent_email": "parent@example.com"
}
```

### Login
```python
POST /api/auth/token
{
  "username": "student123",
  "password": "SecurePass123!"
}
```

## Authorization

### User Roles
- **student**: Basic access to learning features
- **parent**: Can view child's progress
- **teacher**: Can manage multiple students
- **admin**: Full system access

### Protected Endpoints
All `/api/companion/*` endpoints require authentication:
```python
headers = {
  "Authorization": "Bearer <access_token>"
}
```

## Input Validation

### Pydantic Models
All inputs are validated using Pydantic:
- Message length limits (1-1000 chars)
- Mode validation (tutor/friend/hybrid)
- Age validation (5-18 years)
- Grade validation (1-12)

### SQL Injection Prevention
- Parameterized queries everywhere
- Table name whitelist validation
- No dynamic SQL construction

### XSS Prevention
- HTML stripping with bleach
- Content sanitization
- CSP headers

## Rate Limiting

### Limits by Endpoint
- Auth endpoints: 5/minute
- Chat endpoints: 30/minute
- Default: 100/minute

### Headers
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1625097600
```

## Security Headers

### Applied Headers
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'...
```

## CORS Configuration

### Allowed Origins
- http://localhost:3000 (React dev)
- http://localhost:8000 (API)
- Production URLs (add as needed)

### Allowed Methods
- GET, POST, PUT, DELETE

### Allowed Headers
- Content-Type, Authorization, X-API-Key

## WebSocket Security

### Optional Authentication
WebSocket connections can be authenticated:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=<access_token>');
```

### Message Validation
- JSON validation
- Content sanitization
- Rate limiting per connection

## Database Security

### Password Storage
- bcrypt with 12 rounds
- Never store plain text
- Automatic hashing on user creation

### Session Management
- Sessions tracked in database
- Metadata for login/logout times
- Can invalidate sessions

## API Key Authentication

### Service-to-Service
Internal services use API keys:
```
X-API-Key: <service_api_key>
```

### Webhook Validation
Webhooks use HMAC signatures:
```
X-Signature: <hmac_sha256_signature>
```

## Environment Variables

### Required in Production
```env
SECRET_KEY=<random_32_char_string>
SERVICE_API_KEY=<random_32_char_string>
WEBHOOK_SECRET=<random_32_char_string>
ENVIRONMENT=production
```

### Generate Secrets
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Security Checklist

### Before Production
- [ ] Change all default secrets
- [ ] Enable HTTPS only
- [ ] Set ENVIRONMENT=production
- [ ] Review CORS origins
- [ ] Enable firewall rules
- [ ] Set up intrusion detection
- [ ] Configure log monitoring
- [ ] Implement backup encryption
- [ ] Security audit
- [ ] Penetration testing

### Regular Maintenance
- [ ] Update dependencies
- [ ] Review access logs
- [ ] Rotate secrets
- [ ] Check for vulnerabilities
- [ ] Update security headers

## Incident Response

### If Breach Detected
1. Disable affected accounts
2. Rotate all secrets
3. Review audit logs
4. Notify affected users
5. Document incident

### Contact
Security issues: security@iseetutor.com

## Testing Security

### Run Security Tests
```bash
# Install security tools
pip install bandit safety

# Run static analysis
bandit -r src/

# Check dependencies
safety check

# Test authentication
python tests/test_security.py
```

### Manual Testing
1. Try SQL injection in search
2. Attempt XSS in messages
3. Test rate limits
4. Verify token expiration
5. Check authorization