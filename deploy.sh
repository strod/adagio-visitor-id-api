# Google Cloud Functions deployment script
#!/bin/bash

# Configuration
FUNCTION_NAME="adagio-visitor-id-lookup"
REGION="us-central1"
RUNTIME="python312"
ENTRY_POINT="main"
MEMORY="256MB"
TIMEOUT="60s"
MAX_INSTANCES="10"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Error: No active gcloud authentication found."
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set the project
echo "Setting project to retail-api-397423..."
gcloud config set project retail-api-397423

# Deploy the function
echo "Deploying function $FUNCTION_NAME to region $REGION..."
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=. \
    --entry-point=$ENTRY_POINT \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --max-instances=$MAX_INSTANCES \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars="API_SECRET_KEY=your-secret-key-change-in-production,GOOGLE_CLOUD_PROJECT=retail-api-397423,FIRESTORE_DATABASE_ID=adagio-teas-visitor-ids,API_TOKENS_SECRET_NAME=adagio-visitorid-fastapi-tokens"

if [ $? -eq 0 ]; then
    echo "✅ Function deployed successfully!"
    echo "Function URL: https://$REGION-retail-api-397423.cloudfunctions.net/$FUNCTION_NAME"
else
    echo "❌ Deployment failed!"
    exit 1
fi
