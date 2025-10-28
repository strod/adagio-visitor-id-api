# Adagio Visitor ID Lookup API - Quick Start Guide

## API Tokens

Use these tokens for testing:

### Test Token 1 (Development)
```
sk_test_YOUR_TEST_TOKEN_HERE
```

### Test Token 2 (Production-like)
```
sk_live_YOUR_LIVE_TOKEN_HERE
```

## Quick cURL Examples

### 1. Health Check
```bash
curl -X GET "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/"
```

### 2. Lookup Visitor ID
```bash
curl -X POST "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/lookup" \
  -H "Authorization: Bearer sk_test_YOUR_TEST_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_12345"}'
```

### 3. Test Not Found Case
```bash
curl -X POST "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/lookup" \
  -H "Authorization: Bearer sk_test_YOUR_TEST_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "nonexistent_user"}'
```

## Expected Responses

### Success (200)
```json
{
  "visitor_id": "visitor_12345",
  "user_id": "user_67890",
  "found_at": "2024-01-15T10:30:00.000Z"
}
```

### Not Found (404)
```json
{
  "error": "Not Found",
  "message": "No visitor ID found for user_id: nonexistent_user",
  "status_code": 404
}
```

### Unauthorized (401)
```json
{
  "error": "Unauthorized",
  "message": "Invalid API key",
  "status_code": 401
}
```

## Python Quick Test

```python
import requests

# Test the API
url = "https://us-central1-adagio-teas-visitor-ids.cloudfunctions.net/adagio-visitor-id-lookup/lookup"
headers = {
    "Authorization": "Bearer sk_test_YOUR_TEST_TOKEN_HERE",
    "Content-Type": "application/json"
}

# Test with valid user_id
response = requests.post(url, headers=headers, json={"user_id": "user_12345"})
print("Status:", response.status_code)
print("Response:", response.json())

# Test with invalid user_id
response = requests.post(url, headers=headers, json={"user_id": "nonexistent_user"})
print("Status:", response.status_code)
print("Response:", response.json())
```
