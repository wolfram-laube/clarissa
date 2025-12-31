#!/bin/bash
# run-opm.sh - Convenience script for running OPM Flow with correct permissions

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create data and output directories if they don't exist
mkdir -p "$SCRIPT_DIR/data"
mkdir -p "$SCRIPT_DIR/output"

# Run OPM Flow with host user's UID/GID
docker run --rm \
    -e LOCAL_UID=$(id -u) \
    -e LOCAL_GID=$(id -g) \
    -v "$SCRIPT_DIR/data:/simulation/data" \
    -v "$SCRIPT_DIR/output:/simulation/output" \
    opm-flow:latest \
    "$@"
