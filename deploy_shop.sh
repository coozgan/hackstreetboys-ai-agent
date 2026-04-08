#!/bin/bash
# Deploy Shop Agent to Cloud Run
# Usage:
#   GOOGLE_CLOUD_PROJECT=your-project-id \
#   MCP_SERVER_URL=https://mcp-server-XXXX.us-central1.run.app \
#   ./deploy_shop.sh
set -euo pipefail

PROJECT=${GOOGLE_CLOUD_PROJECT:?Error: GOOGLE_CLOUD_PROJECT must be set}
REGION=${GOOGLE_CLOUD_LOCATION:-us-central1}
MCP_URL=${MCP_SERVER_URL:?Error: MCP_SERVER_URL must be set (deploy mcp-server first and paste its URL here)}

set -x
mv Dockerfile Dockerfile.root.bak
mv Dockerfile.shop Dockerfile

gcloud run deploy shop-agent \
  --source . \
  --project "$PROJECT" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_LOCATION=$REGION,MCP_SERVER_URL=$MCP_URL"

res=$?
mv Dockerfile Dockerfile.shop
mv Dockerfile.root.bak Dockerfile
exit $res
