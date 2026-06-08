#!/bin/bash
cd /home/user/emk_game
export PATH=$PATH:/home/user/.local/bin
nohup bash build_with_patches.sh > /tmp/build_runner.log 2>&1 &
echo "PID: $!"