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

# Capture the real Cloud Run hostname and inject it back as SHOP_AGENT_HOST
# K_SERVICE only contains the service name (e.g. "shop-agent"), not the full hostname.
# The real hostname (e.g. shop-agent-abc123-uc.a.run.app) is only known after deployment.
SHOP_URL=$(gcloud run services describe shop-agent \
  --region "$REGION" \
  --project "$PROJECT" \
  --format 'value(status.url)')
SHOP_HOST="${SHOP_URL#https://}"

echo "Shop Agent deployed at: $SHOP_URL"
echo "Setting SHOP_AGENT_HOST=$SHOP_HOST"

gcloud run services update shop-agent \
  --region "$REGION" \
  --project "$PROJECT" \
  --update-env-vars "SHOP_AGENT_HOST=$SHOP_HOST"

mv Dockerfile Dockerfile.shop
mv Dockerfile.root.bak Dockerfile

echo ""
echo "Next: add this to your .env before deploying the Agent Engine:"
echo "  SHOP_AGENT_URL=$SHOP_URL"
