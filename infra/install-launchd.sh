#!/usr/bin/env bash
# Install launchd plists for career-ops scheduled jobs (BUILD.md Task 3.5).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs/career-ops"

mkdir -p "$LAUNCH_AGENTS_DIR" "$LOG_DIR"

PLISTS=(
  "com.career-ops.daily.plist"
  "com.career-ops.weekly.plist"
  "com.career-ops.healthcheck.plist"
)

for plist in "${PLISTS[@]}"; do
  src="$REPO_DIR/infra/$plist"
  dst="$LAUNCH_AGENTS_DIR/$plist"
  cp "$src" "$dst"
  # Update log paths to use $HOME
  sed -i '' "s|/Users/Shared/Library/Logs|$HOME/Library/Logs|g" "$dst" 2>/dev/null || true
  launchctl load "$dst" 2>/dev/null || launchctl bootstrap gui/"$(id -u)" "$dst"
  echo "Loaded: $plist"
done

echo ""
echo "All plists installed. Check with: launchctl list | grep com.career-ops"
echo "Logs: $LOG_DIR/"
