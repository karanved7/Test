#!/usr/bin/env bash
set -euo pipefail

PORT=7681
NGROK_TOKEN="${NGROK_TOKEN:-}"

# Start ttyd web terminal on localhost
echo "Starting web terminal on port $PORT..."
ttyd --port "$PORT" --writable bash &
TTYD_PID=$!

sleep 2

if [ -n "$NGROK_TOKEN" ]; then
  ngrok config add-authtoken "$NGROK_TOKEN"
  echo "Starting ngrok tunnel..."
  ngrok http "$PORT" &
  sleep 3
  # Print public URL
  PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])")
  echo ""
  echo "============================================"
  echo "  Open this URL on your phone:"
  echo "  $PUBLIC_URL"
  echo "============================================"
else
  LOCAL_IP=$(hostname -I | awk '{print $1}')
  echo ""
  echo "============================================"
  echo "  On your phone (same Wi-Fi), open:"
  echo "  http://$LOCAL_IP:$PORT"
  echo "============================================"
  echo "  For remote access, set NGROK_TOKEN and rerun."
fi

echo "Press Ctrl+C to stop."
wait $TTYD_PID
