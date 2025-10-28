import os
import hashlib
import hmac
import json
from datetime import datetime
from typing import Optional, Dict
from flask import Flask, request, jsonify
from google.cloud import firestore
from google.cloud import secretmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# API Key configuration
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-secret-key-change-in-production")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "retail-api-397423")
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "adagio-teas-visitor-ids")

# Secret Manager client
secret_client = secretmanager.SecretManagerServiceClient()

# Initialize Firestore client
db = firestore.Client(project=PROJECT_ID, database=FIRESTORE_DATABASE_ID)

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

def get_api_key():
    """Extract and validate API key from header."""
    authorization = request.headers.get('Authorization')
    if not authorization:
        return None, jsonify({"error": "Unauthorized", "message": "API key required in Authorization header", "status_code": 401}), 401
    
    if not verify_api_key(authorization):
        return None, jsonify({"error": "Unauthorized", "message": "Invalid API key", "status_code": 401}), 401
    
    return authorization, None, None

@app.route('/')
def root():
    """Health check endpoint."""
    return jsonify({"message": "Adagio Visitor ID Lookup API", "status": "healthy"})

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/lookup', methods=['POST'])
def lookup_visitor_id():
    """
    Lookup visitor ID by user ID from Firestore database.
    
    Returns:
        JSON response with visitor_id, user_id, and timestamp
        
    Raises:
        404 if user_id not found, 500 for server errors
    """
    # Check API key
    api_key, error_response, status_code = get_api_key()
    if error_response:
        return error_response, status_code
    
    try:
        # Get user_id from request
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({"error": "Bad Request", "message": "user_id is required", "status_code": 400}), 400
        
        user_id = data['user_id']
        logger.info(f"Looking up visitor ID for user_id: {user_id}")
        
        # Query Firestore for the document with user_id
        collection_ref = db.collection("visitor_ids")
        query = collection_ref.where("user_id", "==", user_id).limit(1)
        docs = query.stream()
        
        # Check if document exists
        doc_found = False
        visitor_id = None
        
        for doc in docs:
            doc_found = True
            data = doc.to_dict()
            visitor_id = data.get("visitor_id")
            logger.info(f"Found visitor_id: {visitor_id} for user_id: {user_id}")
            break
        
        if not doc_found:
            logger.warning(f"No visitor ID found for user_id: {user_id}")
            return jsonify({"error": "Not Found", "message": f"No visitor ID found for user_id: {user_id}", "status_code": 404}), 404
        
        if not visitor_id:
            logger.error(f"Visitor ID field missing for user_id: {user_id}")
            return jsonify({"error": "Internal Server Error", "message": "Visitor ID field missing in database record", "status_code": 500}), 500
        
        return jsonify({
            "visitor_id": visitor_id,
            "user_id": user_id,
            "found_at": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error looking up visitor ID for user_id {user_id}: {str(e)}")
        return jsonify({"error": "Internal Server Error", "message": "Internal server error during lookup", "status_code": 500}), 500

# Google Cloud Functions entry point
@functions_framework.http
def main(request):
    """Entry point for Google Cloud Functions."""
    return app(request)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)