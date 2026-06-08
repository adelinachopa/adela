#!/bin/bash
export PATH=/home/user/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /home/user/emk_game
buildozer android debug > /tmp/buildozer_output4.log 2>&1
echo EXIT_CODE=$?