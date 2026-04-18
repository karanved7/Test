#!/usr/bin/env bash
set -euo pipefail

# Install ttyd if not present
if ! command -v ttyd &>/dev/null; then
  echo "Installing ttyd..."
  sudo apt-get update -qq && sudo apt-get install -y ttyd 2>/dev/null || \
  (curl -L https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64 -o /usr/local/bin/ttyd && chmod +x /usr/local/bin/ttyd)
fi

# Install ngrok if not present
if ! command -v ngrok &>/dev/null; then
  echo "Installing ngrok..."
  curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
  sudo apt-get update -qq && sudo apt-get install -y ngrok 2>/dev/null || true
fi

echo "Setup complete. Run './start.sh' to launch."
