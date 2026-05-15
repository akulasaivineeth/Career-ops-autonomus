# Scheduling (macOS launchd)

Daily apply pipeline and weekly digest run as `launchd` agents.

## Install

```bash
bash infra/install-launchd.sh
```

## Jobs

| Plist | Schedule | Script |
|-------|----------|--------|
| `com.career-ops.daily.plist` | Weekdays 09:00 | `bin/career-ops-daily` |
| `com.career-ops.weekly.plist` | Sundays 18:00 | `uv run python -m agents.workers.digest` |
| `com.career-ops.healthcheck.plist` | Every 6h | `uv run python -m agents.tools.session_health` |

## Status

```bash
launchctl list | grep com.career-ops
```

## Logs

Stdout / stderr go to `~/Library/Logs/career-ops/`.

## Unload

```bash
launchctl unload ~/Library/LaunchAgents/com.career-ops.daily.plist
```
