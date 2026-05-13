---
name: netlify-logs
description: Fetch Netlify observability request logs with client IPs, status codes, durations, and URL patterns. Use when investigating traffic anomalies, slow requests, crawlers, or error spikes on a Netlify site.
argument-hint: "[--site <site_id>] [--window 1h] [--status 502] [--count 100]"
allowed-tools: Bash(python3 *)
---

Fetch and analyze Netlify observability logs using the private bb-api endpoint.

## Arguments

Parse from `$SKILL_ARGS`:
- `--site <id>` — Netlify site ID (required)
- `--window <duration>` — time window ending now: `30m`, `1h`, `2h`, `24h` (default: `1h`)
- `--status <code>` — filter by HTTP status code, e.g. `502` (default: all)
- `--count <n>` — number of requests to fetch (default: `100`)

## Steps

1. Run the fetch script:

```bash
python3 ~/.claude/skills/netlify-logs/fetch.py --site <site_id> [--window <w>] [--status <s>] [--count <n>]
```

2. Present the output to the user. Highlight:
   - Any IPs with a disproportionate share of requests (possible crawlers/bots)
   - High error rates (502/500 dominating)
   - Requests with avg duration > 10s
   - IPs with fake or rotating user agents

## Auth

The script reads the token automatically from `~/Library/Preferences/netlify/config.json`.

## Example invocations

```
/netlify-logs --site 2137e8ee-e5d2-415f-95bb-950e9443d5cc --window 1h --status 502 --count 200
/netlify-logs --site 2137e8ee-e5d2-415f-95bb-950e9443d5cc --window 30m --count 500
```
