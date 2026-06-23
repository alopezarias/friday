#!/bin/sh
while true; do
  python friday.py
  echo "crashed, restarting in 3s..."
  sleep 3
done
