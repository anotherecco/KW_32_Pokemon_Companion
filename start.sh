#!/bin/bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting the application..."

sleep 2

cd "$SCRIPT_DIR/backend"

# Start the backend server in the background.
uvicorn main:app --host 0.0.0.0 --port 8000 &
backend_pid=$!

echo "Backend server started with PID: $backend_pid"
echo "Starting the frontend server..."

sleep 2

cd "$SCRIPT_DIR/frontend/pokemon-companion"
# Start the frontend server from the Vite package directory.
npm run dev -- --host 0.0.0.0 &
frontend_pid=$!

cd "$SCRIPT_DIR"

echo "Frontend server started with PID: $frontend_pid"

sleep 2

echo "Waiting for servers"
sleep 5

echo "open browser at http://localhost:5173"
if command -v xdg-open > /dev/null; then
  xdg-open http://localhost:5173
elif command -v open > /dev/null; then
  open http://localhost:5173
else
  echo "Please open your browser and navigate to http://localhost:5173"
fi

cleanup() {
  if [[ -n "${backend_pid:-}" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    echo "Stopping backend server (PID: $backend_pid)"
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  else
    echo "Backend server is already stopped"
  fi

  if [[ -n "${frontend_pid:-}" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    echo "Stopping frontend server (PID: $frontend_pid)"
    kill "$frontend_pid" 2>/dev/null || true
    wait "$frontend_pid" 2>/dev/null || true
  else
    echo "Frontend server is already stopped"
  fi
}

trap cleanup EXIT

echo "servers are running, if you wish to stop them press enter"
read -r

cleanup

