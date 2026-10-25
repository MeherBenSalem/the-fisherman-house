#!/usr/bin/env bash
# Runs coast_checks.py (server and client checks) on a fresh world for each build:
#   tools/qa/run_matrix.sh [ws:loader ...]     (default: all ten)
# Results go to $QA_LOGS/results/<ws>-<loader>.txt and screenshots to $QA_LOGS/shots/<ws>-<loader>/; a summary line
# per build is printed.
set -u
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
LOGS=${QA_LOGS:-/tmp/fc-qa}
mkdir -p "$LOGS/results"
BUILDS=${*:-"1.20.1:fabric 1.20.1:forge 1.21.1:fabric 1.21.1:neoforge 26.1.2:fabric 26.1.2:neoforge 26.2:fabric 26.2:neoforge 26.3:fabric 26.3:neoforge"}
QA="$ROOT/tools/qa"

wait_for() {  # file, pattern, seconds
  local deadline=$((SECONDS + $3))
  while [ $SECONDS -lt $deadline ]; do
    grep -qE "$2" "$1" 2>/dev/null && return 0
    sleep 5
  done
  return 1
}

for build in $BUILDS; do
  ws=${build%%:*}; loader=${build##*:}
  out="$LOGS/results/$ws-$loader.txt"
  "$QA/devrun.sh" stop-client; "$QA/devrun.sh" stop-server; sleep 10
  "$QA/devrun.sh" prepare-server "$ws" "$loader"
  rm -f "$LOGS/$loader-server.log" "$LOGS/$loader-client.log"
  "$QA/devrun.sh" start-server "$ws" "$loader"
  if ! wait_for "$LOGS/$loader-server.log" 'Done \(|BUILD FAILED|Exception in thread|Failed to start the minecraft server' 1800 \
      || ! grep -q 'Done (' "$LOGS/$loader-server.log"; then
    echo "$ws $loader: SERVER DID NOT START" | tee "$out"; continue
  fi
  "$QA/devrun.sh" start-client "$ws" "$loader"
  if ! wait_for "$LOGS/$loader-server.log" 'Builder joined the game' 2400; then
    echo "$ws $loader: CLIENT DID NOT JOIN" | tee "$out"
    python3 "$QA/coast_checks.py" --log "$LOGS/$loader-server.log" --ws "$ws" --loader "$loader" >> "$out" 2>&1
  else
    sleep 10
    python3 "$QA/coast_checks.py" --log "$LOGS/$loader-server.log" --client --ws "$ws" --loader "$loader" \
      --shots "$LOGS/shots/$ws-$loader" > "$out" 2>&1
  fi
  cp "$LOGS/$loader-server.log" "$LOGS/results/$ws-$loader-server.log"
  echo "$ws $loader: $(tail -n 1 "$out")"
done
"$QA/devrun.sh" stop-client; "$QA/devrun.sh" stop-server
