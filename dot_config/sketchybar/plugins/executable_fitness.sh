#!/usr/bin/env bash

API_URL="https://ct.dmitrym.online/api/occurrences?activity=Health%3A%20Fitness"

# Fetch data from API
DATA=$(curl -s "$API_URL")

if [ -z "$DATA" ] || [ "$DATA" = "null" ]; then
    sketchybar --set $NAME icon="🏋️" label="?"
    exit 0
fi

# Get the most recent workout date
LAST_WORKOUT=$(echo "$DATA" | /opt/homebrew/bin/jq -r '.events | sort_by(.startTime) | last | .startTime // empty')

if [ -z "$LAST_WORKOUT" ]; then
    sketchybar --set $NAME icon="🏋️" label="?"
    exit 0
fi

# Calculate calendar days since last workout
LAST_DATE=$(/bin/date -j -f "%Y-%m-%dT%H:%M:%S" "${LAST_WORKOUT%%.*}" "+%Y-%m-%d" 2>/dev/null)
TODAY=$(/bin/date "+%Y-%m-%d")
LAST_EPOCH=$(/bin/date -j -f "%Y-%m-%d" "$LAST_DATE" "+%s")
TODAY_EPOCH=$(/bin/date -j -f "%Y-%m-%d" "$TODAY" "+%s")
DAYS_SINCE=$(( (TODAY_EPOCH - LAST_EPOCH) / 86400 ))

# Set color based on days
if [ $DAYS_SINCE -le 1 ]; then
    COLOR="0xff8ec07c"  # green
elif [ $DAYS_SINCE -le 3 ]; then
    COLOR="0xfffabd2f"  # yellow
else
    COLOR="0xfffb4934"  # red
fi

sketchybar --set $NAME icon="🏋️" label="${DAYS_SINCE}d" label.color=$COLOR
