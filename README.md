# Adagio Visitor ID Lookup API

A FastAPI-based microservice deployed on Google Cloud Functions that provides visitor ID lookup functionality using Firestore database.

## Overview

This API service allows you to lookup visitor IDs by providing a user ID. It integrates with Google Firestore database (`adagio-teas-visitor-ids`) and includes API key authentication with checksum verification.

## Features

- 🔍 **Visitor ID Lookup**: Query visitor IDs by user ID from Firestore
- 🔐 **API Key Authentication**: Secure access with checksum verification
- ☁️ **Google Cloud Functions**: Serverless deployment ready
- 📊 **Health Monitoring**: Built-in health check endpoints
- 🚀 **FastAPI**: Modern, fast web framework
- 📝 **Comprehensive Logging**: Detailed request/response logging

## API Endpoints

### Base URL
```
https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup
```

### Endpoints

#### 1. Health Check
```http
GET /
GET /health
```

**Response:**
```json
{
  "message": "Adagio Visitor ID Lookup API",
  "status": "healthy"
}
```

#### 2. Lookup Visitor ID
```http
POST /lookup
```

**Headers:**
```
Authorization: Bearer <API_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "string"
}
```

**Success Response (200):**
```json
{
  "visitor_id": "visitor_12345",
  "user_id": "user_67890",
  "found_at": "2024-01-15T10:30:00.000Z"
}
```

**Error Responses:**

**404 - Not Found:**
```json
{
  "error": "Not Found",
  "message": "No visitor ID found for user_id: user_67890",
  "status_code": 404
}
```

**401 - Unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "Invalid API key",
  "status_code": 401
}
```

**500 - Internal Server Error:**
```json
{
  "error": "Internal Server Error",
  "message": "Internal server error during lookup",
  "status_code": 500
}
```

## API Authentication

The API uses Bearer token authentication with checksum verification. API tokens are stored securely in Google Secret Manager and retrieved at runtime.

Include your API token in the `Authorization` header:

```
Authorization: Bearer <your_api_token>
```

### Token Management

API tokens are managed through Google Secret Manager for enhanced security:

- 🔐 **Secure Storage**: Tokens stored in Google Secret Manager
- 🔄 **Easy Rotation**: Update tokens without code changes
- 📊 **Audit Trail**: Track token access and usage
- 🚀 **Zero Downtime**: Seamless token updates

For setup instructions, see [SECRET_MANAGER_SETUP.md](SECRET_MANAGER_SETUP.md).

### Available API Tokens

For testing and development, configure these tokens in Secret Manager:

#### Test Token 1
```
Token: sk_test_YOUR_TEST_TOKEN_HERE
Usage: Development and testing
```

#### Test Token 2
```
Token: sk_live_YOUR_LIVE_TOKEN_HERE
Usage: Production-like testing
```

## cURL Examples

### 1. Health Check
```bash
curl -X GET "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/"
```

### 2. Lookup Visitor ID (Success)
```bash
curl -X POST "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/lookup" \
  -H "Authorization: Bearer sk_test_YOUR_TEST_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345"
  }'
```

### 3. Lookup Visitor ID (Not Found)
```bash
curl -X POST "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/lookup" \
  -H "Authorization: Bearer sk_test_YOUR_TEST_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "nonexistent_user"
  }'
```

### 4. Invalid API Key
```bash
curl -X POST "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/lookup" \
  -H "Authorization: Bearer invalid_token" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345"
  }'
```

### 5. Missing Authorization Header
```bash
curl -X POST "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_12345"
  }'
```

## Python Examples

### Using requests library
```python
import requests
import json

# Configuration
API_URL = "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup"
API_TOKEN = "sk_test_YOUR_TEST_TOKEN_HERE"

# Headers
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Lookup visitor ID
def lookup_visitor_id(user_id):
    url = f"{API_URL}/lookup"
    data = {"user_id": user_id}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"No visitor ID found for user_id: {user_id}")
        elif e.response.status_code == 401:
            print("Invalid API key")
        else:
            print(f"Error: {e}")
        return None

# Example usage
result = lookup_visitor_id("user_12345")
if result:
    print(f"Visitor ID: {result['visitor_id']}")
```

### Using httpx (async)
```python
import httpx
import asyncio

async def async_lookup_visitor_id(user_id):
    API_URL = "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup"
    API_TOKEN = "sk_test_YOUR_TEST_TOKEN_HERE"
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/lookup",
                headers=headers,
                json={"user_id": user_id}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e}")
            return None

# Example usage
result = asyncio.run(async_lookup_visitor_id("user_12345"))
```

## JavaScript/Node.js Examples

### Using fetch
```javascript
const API_URL = "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup";
const API_TOKEN = "sk_test_YOUR_TEST_TOKEN_HERE";

async function lookupVisitorId(userId) {
    try {
        const response = await fetch(`${API_URL}/lookup`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });

        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(`No visitor ID found for user_id: ${userId}`);
            } else if (response.status === 401) {
                throw new Error('Invalid API key');
            } else {
                throw new Error(`HTTP Error: ${response.status}`);
            }
        }

        return await response.json();
    } catch (error) {
        console.error('Error:', error.message);
        return null;
    }
}

// Example usage
lookupVisitorId("user_12345")
    .then(result => {
        if (result) {
            console.log(`Visitor ID: ${result.visitor_id}`);
        }
    });
```

## Database Schema

The API expects the following Firestore collection structure:

**Collection:** `visitor_ids`

**Document Structure:**
```json
{
  "user_id": "string",
  "visitor_id": "string",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

## Deployment

### Prerequisites
- Google Cloud SDK installed
- Authenticated with Google Cloud
- Firestore database configured
- Secret Manager API enabled
- API tokens configured in Secret Manager

### Deploy to Google Cloud Functions

1. **Clone the repository:**
```bash
git clone <repository-url>
cd adagio-visitorId-fastapi
```

2. **Set up Secret Manager** (see [SECRET_MANAGER_SETUP.md](SECRET_MANAGER_SETUP.md)):
```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secret and add your API tokens
gcloud secrets create adagio-api-tokens --replication-policy="automatic"
# Add your tokens to the secret (see setup guide)
```

3. **Deploy using the provided script:**
```bash
./deploy.sh
```

4. **Or deploy manually:**
```bash
gcloud functions deploy adagio-visitor-id-lookup \
    --gen2 \
    --runtime=python312 \
    --region=us-central1 \
    --source=. \
    --entry-point=main \
    --memory=256MB \
    --timeout=60s \
    --max-instances=10 \
    --allow-unauthenticated \
    --set-env-vars="API_SECRET_KEY=your-secret-key-change-in-production,GOOGLE_CLOUD_PROJECT=adagio-teas-visitor-ids,API_TOKENS_SECRET_NAME=adagio-api-tokens"
```

## Local Development

### Setup
1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp env.example .env
# Edit .env with your configuration
```

3. **Run locally:**
```bash
python main.py
```

The API will be available at `http://localhost:8080`

## Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid request format
- **401 Unauthorized**: Missing or invalid API key
- **404 Not Found**: User ID not found in database
- **500 Internal Server Error**: Server-side errors

All errors return JSON responses with detailed error information.

## Rate Limiting

Currently, the API does not implement rate limiting. For production use, consider implementing rate limiting based on your requirements.

## Security Considerations

1. **API Key Management**: Tokens stored securely in Google Secret Manager with automatic rotation support
2. **HTTPS Only**: Always use HTTPS in production
3. **Input Validation**: All inputs are validated using Pydantic models
4. **Logging**: Comprehensive logging for monitoring and debugging
5. **Secret Access**: Audit trails for all secret access through Secret Manager
6. **Least Privilege**: Cloud Functions only have access to necessary secrets

## Monitoring and Logging

The API includes structured logging for:
- Request/response details
- Error tracking
- Performance metrics
- Authentication events

Logs are available in Google Cloud Functions logs.

## Support

For issues or questions, please contact the development team or create an issue in the repository.

## License

This project is proprietary software for Adagio Teas.
