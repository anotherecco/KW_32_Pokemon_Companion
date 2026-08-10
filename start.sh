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

echo "servers are running, if you wish to stop them press enter"
read -r

kill "$backend_pid"
kill "$frontend_pid"

