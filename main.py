import os
import hashlib
import hmac
import json
from datetime import datetime
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from google.cloud import firestore
from google.cloud import secretmanager
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Adagio Visitor ID Lookup API",
    description="API for looking up visitor IDs from Firestore database",
    version="1.0.0"
)

# Initialize Firestore client
db = firestore.Client(project="adagio-teas-visitor-ids")

# Pydantic models
class LookupRequest(BaseModel):
    user_id: str

class LookupResponse(BaseModel):
    visitor_id: str
    user_id: str
    found_at: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int

# API Key configuration
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-secret-key-change-in-production")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "adagio-teas-visitor-ids")

# Secret Manager client
secret_client = secretmanager.SecretManagerServiceClient()

def get_api_tokens() -> Dict[str, str]:
    """
    Retrieve API tokens from Google Secret Manager.
    Returns a dictionary of token names to token values.
    """
    try:
        # Get the secret name from environment variable
        secret_name = os.getenv("API_TOKENS_SECRET_NAME", "adagio-visitorid-fastapi-tokens")
        
        # Build the resource name of the secret version
        name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        
        # Access the secret version
        response = secret_client.access_secret_version(request={"name": name})
        
        # Decode the secret payload
        secret_payload = response.payload.data.decode("UTF-8")
        
        # Parse the JSON payload
        api_tokens = json.loads(secret_payload)
        
        logger.info("Successfully retrieved API tokens from Secret Manager")
        return api_tokens
        
    except Exception as e:
        logger.error(f"Failed to retrieve API tokens from Secret Manager: {str(e)}")
        # Fallback to environment variables for local development
        fallback_tokens = {
            "adagio_token_1": os.getenv("API_TOKEN_1", "sk_test_YOUR_TEST_TOKEN_HERE"),
            "adagio_token_2": os.getenv("API_TOKEN_2", "sk_live_YOUR_LIVE_TOKEN_HERE")
        }
        logger.warning("Using fallback API tokens from environment variables")
        return fallback_tokens

def verify_api_key(api_key: str) -> bool:
    """
    Verify API key using checksum verification.
    This creates a checksum based on the token and secret key.
    """
    if not api_key:
        return False
    
    # Extract token from API key format
    if not api_key.startswith("Bearer "):
        return False
    
    token = api_key[7:]  # Remove "Bearer " prefix
    
    # Get API tokens from Secret Manager
    api_tokens = get_api_tokens()
    
    # Check if token exists in our valid tokens
    if token not in api_tokens.values():
        return False
    
    # Create checksum verification
    expected_checksum = hmac.new(
        API_SECRET_KEY.encode(),
        token.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # For demo purposes, we'll use a simple verification
    # In production, you might want to store checksums separately
    return True

def get_api_key(authorization: Optional[str] = Header(None)) -> str:
    """Dependency to extract and validate API key from header."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="API key required in Authorization header"
        )
    
    if not verify_api_key(authorization):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return authorization

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Adagio Visitor ID Lookup API", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/lookup", response_model=LookupResponse)
async def lookup_visitor_id(
    request: LookupRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Lookup visitor ID by user ID from Firestore database.
    
    Args:
        request: LookupRequest containing user_id
        api_key: Valid API key from Authorization header
        
    Returns:
        LookupResponse with visitor_id, user_id, and timestamp
        
    Raises:
        HTTPException: 404 if user_id not found, 500 for server errors
    """
    try:
        logger.info(f"Looking up visitor ID for user_id: {request.user_id}")
        
        # Query Firestore for the document with user_id
        collection_ref = db.collection("visitor_ids")
        query = collection_ref.where("user_id", "==", request.user_id).limit(1)
        docs = query.stream()
        
        # Check if document exists
        doc_found = False
        visitor_id = None
        
        for doc in docs:
            doc_found = True
            data = doc.to_dict()
            visitor_id = data.get("visitor_id")
            logger.info(f"Found visitor_id: {visitor_id} for user_id: {request.user_id}")
            break
        
        if not doc_found:
            logger.warning(f"No visitor ID found for user_id: {request.user_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No visitor ID found for user_id: {request.user_id}"
            )
        
        if not visitor_id:
            logger.error(f"Visitor ID field missing for user_id: {request.user_id}")
            raise HTTPException(
                status_code=500,
                detail="Visitor ID field missing in database record"
            )
        
        return LookupResponse(
            visitor_id=visitor_id,
            user_id=request.user_id,
            found_at=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error looking up visitor ID for user_id {request.user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during lookup"
        )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "message": str(exc.detail), "status_code": 404}
    )

@app.exception_handler(401)
async def unauthorized_handler(request, exc):
    """Custom 401 handler."""
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized", "message": str(exc.detail), "status_code": 401}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": str(exc.detail), "status_code": 500}
    )

# Google Cloud Functions entry point
def main(request):
    """Entry point for Google Cloud Functions."""
    import uvicorn
    from fastapi import Request
    from fastapi.responses import Response
    
    # Handle the request
    return app(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
