#!/usr/bin/env bash

API_URL="https://ct.dmitrym.online/api/occurrences?activity=Health%3A%20Meditate"

# Toggle popup
CURRENT=$(sketchybar --query meditate | /opt/homebrew/bin/jq -r '.popup.drawing')

if [ "$CURRENT" = "on" ]; then
    sketchybar --set meditate popup.drawing=off
    exit 0
fi

# Fetch data from API
DATA=$(curl -s "$API_URL")

if [ -z "$DATA" ] || [ "$DATA" = "null" ]; then
    exit 0
fi

# Remove old popup items
sketchybar --remove '/meditate.item\..*/' 2>/dev/null

# Create popup items from events
EVENTS=$(echo "$DATA" | /opt/homebrew/bin/jq -r '.events | sort_by(.startTime) | reverse | .[] | @base64')

INDEX=0
for EVENT in $EVENTS; do
    DECODED=$(echo "$EVENT" | base64 --decode)
    DATE=$(echo "$DECODED" | /opt/homebrew/bin/jq -r '.startTime | split("T")[0]')
    DURATION=$(echo "$DECODED" | /opt/homebrew/bin/jq -r '.durationMinutes')

    sketchybar --add item meditate.item.$INDEX popup.meditate \
               --set meditate.item.$INDEX label="$DATE  ${DURATION}min" \
                     label.font="Hack Nerd Font:Regular:12.0" \
                     background.padding_left=10 \
                     background.padding_right=10

    INDEX=$((INDEX + 1))
done

sketchybar --set meditate popup.drawing=on
