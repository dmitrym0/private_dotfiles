#!/bin/bash

export PATH='usr/local/bin:/usr/bin:$PATH'

# The default output of (org-pomodoro-format-seconds) contains parentheses, which I don't need. Sub them out with sed.
V=$( /opt/homebrew/bin/emacsclient --eval "(jx/produce-pomodoro-string-for-menu-bar)" | sed 's/["()]//g' )

/opt/homebrew/bin/sketchybar --set org-pomodoro label="$V"
