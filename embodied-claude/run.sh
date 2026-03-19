#!/usr/bin/env bash
set -euo pipefail

# Read options from HA add-on config
CONFIG_PATH="/data/options.json"

TAPO_CAMERA_HOST=$(jq -r '.tapo_camera_host' "$CONFIG_PATH")
TAPO_USERNAME=$(jq -r '.tapo_username' "$CONFIG_PATH")
TAPO_PASSWORD=$(jq -r '.tapo_password' "$CONFIG_PATH")
TAPO_ONVIF_PORT=$(jq -r '.tapo_onvif_port' "$CONFIG_PATH")
TAPO_MOUNT_MODE=$(jq -r '.tapo_mount_mode' "$CONFIG_PATH")
ANTHROPIC_API_KEY=$(jq -r '.anthropic_api_key' "$CONFIG_PATH")
MEMORY_DB_PATH=$(jq -r '.memory_db_path' "$CONFIG_PATH")

# Export environment variables for MCP servers
export TAPO_CAMERA_HOST
export TAPO_USERNAME
export TAPO_PASSWORD
export TAPO_ONVIF_PORT
export TAPO_MOUNT_MODE
export ANTHROPIC_API_KEY
export MEMORY_DB_PATH

# Ensure memory directory exists
mkdir -p "$(dirname "$MEMORY_DB_PATH")"

# Create .mcp.json for Claude Code
cat > /opt/embodied-claude/.mcp.json <<EOF
{
  "mcpServers": {
    "wifi-cam": {
      "command": "uv",
      "args": ["run", "--directory", "/opt/embodied-claude/wifi-cam-mcp", "wifi-cam-mcp"],
      "env": {
        "TAPO_CAMERA_HOST": "${TAPO_CAMERA_HOST}",
        "TAPO_USERNAME": "${TAPO_USERNAME}",
        "TAPO_PASSWORD": "${TAPO_PASSWORD}",
        "TAPO_ONVIF_PORT": "${TAPO_ONVIF_PORT}",
        "TAPO_MOUNT_MODE": "${TAPO_MOUNT_MODE}"
      }
    },
    "memory": {
      "command": "uv",
      "args": ["run", "--directory", "/opt/embodied-claude/memory-mcp", "memory-mcp"],
      "env": {
        "MEMORY_DB_PATH": "${MEMORY_DB_PATH}"
      }
    },
    "system-temperature": {
      "command": "uv",
      "args": ["run", "--directory", "/opt/embodied-claude/system-temperature-mcp", "system-temperature-mcp"]
    }
  }
}
EOF

echo "============================================"
echo " Embodied Claude - HA OS Add-on"
echo "============================================"
echo " Camera: ${TAPO_CAMERA_HOST}"
echo " Memory: ${MEMORY_DB_PATH}"
echo "============================================"

# Start ttyd (web terminal) with Claude Code
exec ttyd \
    --port 7681 \
    --writable \
    bash -c "cd /opt/embodied-claude && claude"
