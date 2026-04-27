#!/usr/bin/env bash

if pgrep -x "QuickRecorder" > /dev/null; then
    sketchybar --set "QuickRecorder,Item-0" drawing=on
else
    sketchybar --set "QuickRecorder,Item-0" drawing=off
fi
