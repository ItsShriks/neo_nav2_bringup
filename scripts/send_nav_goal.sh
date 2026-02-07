#!/bin/bash
# Convenience wrapper for sending navigation goals
# Usage: ./send_nav_goal.sh <x> <y> <yaw_degrees>

if [ $# -lt 3 ]; then
  echo "Usage: $0 <x> <y> <yaw_degrees>"
  echo "Example: $0 2.0 1.5 90"
  exit 1
fi

X=$1
Y=$2
YAW_DEG=$3

# Convert degrees to radians
YAW_RAD=$(echo "scale=6; $YAW_DEG * 3.14159265359 / 180" | bc -l)

echo "Sending navigation goal:"
echo "  Position: ($X, $Y) m"
echo "  Orientation: $YAW_DEG° ($YAW_RAD rad)"

ros2 run steve_navigation nav2_navigator.py --x $X --y $Y --yaw $YAW_RAD
