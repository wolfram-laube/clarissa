#!/bin/bash
# gitlab-runner-check.sh
# Health check and auto-restart for GitLab Runner on macOS
# 
# Usage: 
#   ./gitlab-runner-check.sh          # Check status
#   ./gitlab-runner-check.sh --fix    # Auto-fix if not running
#   ./gitlab-runner-check.sh --watch  # Continuous monitoring

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_docker() {
    if docker info &>/dev/null; then
        echo -e "${GREEN}✅ Docker:${NC} running"
        return 0
    else
        echo -e "${RED}❌ Docker:${NC} not running"
        return 1
    fi
}

check_runner_process() {
    if pgrep -f "gitlab-runner" &>/dev/null; then
        echo -e "${GREEN}✅ Runner Process:${NC} running (PID $(pgrep -f 'gitlab-runner' | head -1))"
        return 0
    else
        echo -e "${RED}❌ Runner Process:${NC} not running"
        return 1
    fi
}

check_brew_service() {
    local status=$(brew services list 2>/dev/null | grep gitlab-runner | awk '{print $2}')
    if [ "$status" = "started" ]; then
        echo -e "${GREEN}✅ Brew Service:${NC} started"
        return 0
    elif [ "$status" = "none" ] || [ -z "$status" ]; then
        echo -e "${YELLOW}⚠️  Brew Service:${NC} not registered"
        return 1
    else
        echo -e "${RED}❌ Brew Service:${NC} $status"
        return 1
    fi
}

check_runner_online() {
    # Quick check if runner can connect (optional - requires network)
    if gitlab-runner verify 2>&1 | grep -q "is alive"; then
        echo -e "${GREEN}✅ Runner Verify:${NC} alive and connected to GitLab"
        return 0
    else
        echo -e "${YELLOW}⚠️  Runner Verify:${NC} cannot verify (check network)"
        return 1
    fi
}

fix_runner() {
    echo ""
    echo -e "${YELLOW}🔧 Attempting to fix...${NC}"
    
    # 1. Check Docker first
    if ! docker info &>/dev/null; then
        echo "   Starting Docker Desktop..."
        open -a Docker
        echo "   Waiting for Docker to start (30s)..."
        for i in {1..30}; do
            if docker info &>/dev/null; then
                echo -e "   ${GREEN}Docker started!${NC}"
                break
            fi
            sleep 1
        done
    fi
    
    # 2. Restart gitlab-runner service
    echo "   Restarting gitlab-runner service..."
    brew services restart gitlab-runner 2>/dev/null || {
        echo "   Service not registered, starting..."
        brew services start gitlab-runner
    }
    
    sleep 2
    echo ""
    echo "Status after fix:"
    check_status
}

check_status() {
    echo "═══════════════════════════════════════"
    echo "  GitLab Runner Health Check"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "═══════════════════════════════════════"
    echo ""
    
    local all_ok=true
    
    check_docker || all_ok=false
    check_runner_process || all_ok=false
    check_brew_service || all_ok=false
    check_runner_online 2>/dev/null || true  # Don't fail on network issues
    
    echo ""
    if $all_ok; then
        echo -e "${GREEN}All systems operational! 🚀${NC}"
        return 0
    else
        echo -e "${RED}Some issues detected.${NC}"
        echo "Run with --fix to attempt auto-repair"
        return 1
    fi
}

watch_mode() {
    echo "Watching gitlab-runner status (Ctrl+C to stop)..."
    echo ""
    while true; do
        clear
        check_status
        echo ""
        echo -e "${YELLOW}Next check in 30s...${NC}"
        sleep 30
    done
}

# Main
case "${1:-}" in
    --fix)
        check_status || fix_runner
        ;;
    --watch)
        watch_mode
        ;;
    --help|-h)
        echo "Usage: $0 [--fix|--watch|--help]"
        echo ""
        echo "Options:"
        echo "  (none)   Check status"
        echo "  --fix    Auto-fix if not running"
        echo "  --watch  Continuous monitoring"
        ;;
    *)
        check_status
        ;;
esac
