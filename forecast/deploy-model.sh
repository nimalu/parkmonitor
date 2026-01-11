#!/bin/bash
# deploy.sh - Deploy trained model to production

set -e

SERVER="root@parkmonitor.niklaslutze.de"
REMOTE_PATH="/opt/parkmonitor"

echo "Deploying model to parkmonitor.niklaslutze.de..."

# Check if model exists
if [ ! -d "forecast/models" ] || [ -z "$(ls -A forecast/models/*.pkl 2>/dev/null)" ]; then
  echo "Error: No trained model found in forecast/models/"
  echo "Run 'pixi run train' first to train a model"
  exit 1
fi

# Sync model files to production
rsync -avz forecast/models/*.pkl $SERVER:$REMOTE_PATH/forecast/models/

echo "✓ Model deployment complete!"
echo "Visit: https://parkmonitor.niklaslutze.de/"
