#!/bin/bash
# deploy_lightsail.sh — provision a new Lightsail instance and deploy JobScraper
#
# Prerequisites (local machine):
#   - AWS CLI configured (aws configure)
#   - SSH key pair already created in Lightsail (set KEY_NAME below)
#   - ANTHROPIC_API_KEY set in environment or passed as argument
#
# Usage:
#   ANTHROPIC_API_KEY=sk-ant-... ./deploy_lightsail.sh
#   ./deploy_lightsail.sh sk-ant-...   (as first argument)

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
INSTANCE_NAME="${INSTANCE_NAME:-jobscraper}"
REGION="${AWS_REGION:-us-east-1}"
BLUEPRINT="amazon_linux_2023"
BUNDLE="small_3_0"          # $12/mo — 2 vCPU, 2GB RAM, 60GB SSD
KEY_NAME="${LIGHTSAIL_KEY:-jobscraper}"      # Lightsail key pair name
IMAGE_NAME="jobscraper:latest"
DATA_DIR="/data"
PORT=3000

API_KEY="${1:-${ANTHROPIC_API_KEY:-}}"
if [[ -z "$API_KEY" ]]; then
  echo "ERROR: ANTHROPIC_API_KEY is required. Set it in env or pass as first argument." >&2
  exit 1
fi

# ── 1. Create instance (skip if already exists) ───────────────────────────────
EXISTING=$(aws lightsail get-instance \
  --instance-name "$INSTANCE_NAME" \
  --region "$REGION" \
  --query 'instance.state.name' \
  --output text 2>/dev/null || echo "")

if [[ -z "$EXISTING" ]]; then
  echo "==> Creating Lightsail instance: $INSTANCE_NAME ($BUNDLE, $REGION)"
  aws lightsail create-instances \
    --instance-names "$INSTANCE_NAME" \
    --availability-zone "${REGION}a" \
    --blueprint-id "$BLUEPRINT" \
    --bundle-id "$BUNDLE" \
    --key-pair-name "$KEY_NAME" \
    --region "$REGION"
else
  echo "==> Instance $INSTANCE_NAME already exists (state: $EXISTING), skipping creation."
fi

echo "==> Waiting for instance to become running..."
for i in $(seq 1 30); do
  STATE=$(aws lightsail get-instance \
    --instance-name "$INSTANCE_NAME" \
    --region "$REGION" \
    --query 'instance.state.name' \
    --output text 2>/dev/null || echo "pending")
  echo "    state: $STATE"
  [[ "$STATE" == "running" ]] && break
  sleep 10
done

INSTANCE_IP=$(aws lightsail get-instance \
  --instance-name "$INSTANCE_NAME" \
  --region "$REGION" \
  --query 'instance.publicIpAddress' \
  --output text)
echo "==> Instance IP: $INSTANCE_IP"

# ── 2. Open port 3000 ─────────────────────────────────────────────────────────
echo "==> Opening port $PORT..."
aws lightsail put-instance-public-ports \
  --instance-name "$INSTANCE_NAME" \
  --region "$REGION" \
  --port-infos "[
    {\"fromPort\":22,\"toPort\":22,\"protocol\":\"tcp\"},
    {\"fromPort\":$PORT,\"toPort\":$PORT,\"protocol\":\"tcp\"}
  ]"

# ── 3. SSH helper ─────────────────────────────────────────────────────────────
SSH_KEY="${HOME}/.ssh/${KEY_NAME}.pem"
if [[ ! -f "$SSH_KEY" ]]; then
  echo "ERROR: SSH key not found at $SSH_KEY" >&2
  exit 1
fi
chmod 600 "$SSH_KEY"

SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=no ec2-user@$INSTANCE_IP"

echo "==> Waiting for SSH to be available..."
for i in $(seq 1 20); do
  $SSH "echo ok" 2>/dev/null && break || sleep 6
done

# ── 4. Install Docker on instance ────────────────────────────────────────────
echo "==> Installing Docker..."
$SSH "sudo dnf install -y docker && sudo systemctl enable --now docker && sudo usermod -aG docker ec2-user"

# Re-open connection after group change
SSH="ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o SendEnv=none ec2-user@$INSTANCE_IP"

# ── 5. Build image locally and transfer ──────────────────────────────────────
echo "==> Building Docker image locally (linux/amd64)..."
docker build --platform linux/amd64 -t "$IMAGE_NAME" .

echo "==> Transferring image to instance (this may take a few minutes)..."
docker save "$IMAGE_NAME" | gzip | ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE_IP" \
  "gunzip | docker load"

# ── 6. Ensure data directory exists (preserve existing db on instance) ────────
$SSH "sudo mkdir -p $DATA_DIR && sudo mkdir -p $DATA_DIR/uploads && sudo chmod 777 $DATA_DIR $DATA_DIR/uploads"

# ── 7. Run container ──────────────────────────────────────────────────────────
echo "==> Starting container..."
$SSH "
  docker stop jobscraper 2>/dev/null || true
  docker rm   jobscraper 2>/dev/null || true
  docker run -d \
    --name jobscraper \
    --restart unless-stopped \
    -p $PORT:$PORT \
    -v $DATA_DIR:/data \
    -v $DATA_DIR/uploads:/tmp \
    -e ANTHROPIC_API_KEY='$API_KEY' \
    -e RESEND_API_KEY='${RESEND_API_KEY:-}' \
    -e EMAIL_FROM='${EMAIL_FROM:-}' \
    -e EMAIL_TO='${EMAIL_TO:-}' \
    -e DB_PATH=$DATA_DIR/jobs.db \
    -e PORT=$PORT \
    $IMAGE_NAME
"

echo ""
echo "==> Deploy complete!"
echo "    URL: http://$INSTANCE_IP:$PORT"
echo "    SSH: ssh -i $SSH_KEY ec2-user@$INSTANCE_IP"
echo "    Logs: ssh ... 'docker logs -f jobscraper'"
