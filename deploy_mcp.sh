#!/bin/bash
# Deploy MCP Server to Cloud Run
# Usage: GOOGLE_CLOUD_PROJECT=your-project-id ./deploy_mcp.sh
set -euo pipefail

PROJECT=${GOOGLE_CLOUD_PROJECT:?Error: GOOGLE_CLOUD_PROJECT must be set}
REGION=${GOOGLE_CLOUD_LOCATION:-us-central1}

set -x
mv Dockerfile Dockerfile.bak
mv Dockerfile.mcp Dockerfile

gcloud run deploy mcp-server \
    --project "$PROJECT" \
    --region "$REGION" \
    --source . \
    --allow-unauthenticated \
    --memory 512Mi

res=$?
mv Dockerfile Dockerfile.mcp
mv Dockerfile.bak Dockerfile
exit $res
