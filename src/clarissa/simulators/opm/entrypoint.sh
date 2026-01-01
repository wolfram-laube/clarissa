#!/bin/bash
set -e

# If LOCAL_UID and LOCAL_GID are set, create a user with matching IDs
# This solves permission issues with mounted volumes
if [ -n "$LOCAL_UID" ] && [ -n "$LOCAL_GID" ]; then
    # Create group if it doesn't exist
    if ! getent group opmgroup > /dev/null 2>&1; then
        groupadd -g "$LOCAL_GID" opmgroup
    fi
    
    # Create user if it doesn't exist
    if ! id opmuser > /dev/null 2>&1; then
        useradd -u "$LOCAL_UID" -g "$LOCAL_GID" -m -s /bin/bash opmuser
    fi
    
    # Run command as opmuser
    exec gosu opmuser "$@"
else
    # No UID/GID specified, run as root (simpler but less secure)
    exec "$@"
fi
