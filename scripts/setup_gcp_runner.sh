#!/bin/bash
# GitLab Runner on GCP - Automated Setup
# Usage: ./setup_gcp_runner.sh <GITLAB_RUNNER_TOKEN>

set -e

# Configuration
PROJECT_ID="myk8sproject-207017"
ZONE="europe-west1-b"
INSTANCE_NAME="gitlab-runner-clarissa"
MACHINE_TYPE="e2-small"  # ~$13/mo, or use e2-micro for ~$6/mo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 GitLab Runner Setup for CLARISSA${NC}"
echo "========================================"

# Check for runner token
if [ -z "$1" ]; then
    echo -e "${RED}Error: GitLab Runner Token required${NC}"
    echo ""
    echo "Get it from:"
    echo "  GitLab → Settings → CI/CD → Runners → New project runner"
    echo ""
    echo "Usage: $0 <GITLAB_RUNNER_TOKEN>"
    exit 1
fi

RUNNER_TOKEN="$1"

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not installed${NC}"
    echo "Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   Project:  $PROJECT_ID"
echo "   Zone:     $ZONE"
echo "   Instance: $INSTANCE_NAME"
echo "   Machine:  $MACHINE_TYPE"
echo ""

# Set project
gcloud config set project $PROJECT_ID

# Create startup script
STARTUP_SCRIPT=$(cat << 'STARTUP'
#!/bin/bash
set -e

# Install Docker
apt-get update
apt-get install -y docker.io curl
systemctl enable docker
systemctl start docker

# Install GitLab Runner
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | bash
apt-get install -y gitlab-runner

# Add gitlab-runner to docker group
usermod -aG docker gitlab-runner

# Signal completion
touch /tmp/setup_complete
STARTUP
)

echo -e "${YELLOW}🖥️  Creating VM...${NC}"
gcloud compute instances create $INSTANCE_NAME \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=30GB \
    --tags=gitlab-runner \
    --metadata=startup-script="$STARTUP_SCRIPT"

echo -e "${YELLOW}⏳ Waiting for VM setup (60s)...${NC}"
sleep 60

echo -e "${YELLOW}🔧 Registering GitLab Runner...${NC}"
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    sudo gitlab-runner register \
        --non-interactive \
        --url 'https://gitlab.com/' \
        --token '$RUNNER_TOKEN' \
        --executor 'docker' \
        --docker-image 'python:3.11-slim' \
        --docker-privileged \
        --docker-volumes '/var/run/docker.sock:/var/run/docker.sock' \
        --docker-volumes '/cache' \
        --description 'gcp-runner-clarissa' \
        --tag-list 'gcp,docker,clarissa' \
        --run-untagged='true'
"

echo -e "${YELLOW}🚀 Starting Runner...${NC}"
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    sudo gitlab-runner start
    sudo gitlab-runner status
"

echo ""
echo -e "${GREEN}✅ GitLab Runner Setup Complete!${NC}"
echo "=================================="
echo ""
echo "VM: $INSTANCE_NAME"
echo "Zone: $ZONE"
echo "Cost: ~\$13/month (e2-small)"
echo ""
echo "Commands:"
echo "  SSH:    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo "  Stop:   gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE"
echo "  Start:  gcloud compute instances start $INSTANCE_NAME --zone=$ZONE"
echo "  Delete: gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "Check runner in GitLab:"
echo "  Settings → CI/CD → Runners"