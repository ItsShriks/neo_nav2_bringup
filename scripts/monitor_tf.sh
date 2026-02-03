#!/bin/bash
# ROS2 TF Monitor Script
# Continuously monitors critical TF transforms for localization

echo "========================================="
echo "ROS2 TF Transform Monitor"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if ROS2 is sourced
if [ -z "$ROS_DISTRO" ]; then
    echo -e "${RED}✗ ROS2 not sourced. Please run: source install/setup.bash${NC}"
    exit 1
fi

echo -e "${GREEN}✓ ROS2 environment sourced${NC}"
echo ""
echo "Monitoring TF transforms (Press Ctrl+C to stop)..."
echo "========================================="
echo ""

# Function to monitor a transform
monitor_transform() {
    local from_frame=$1
    local to_frame=$2
    local label=$3
    
    echo -e "${BLUE}=== ${label} ===${NC}"
    
    # Try to get the transform
    output=$(timeout 2 ros2 run tf2_ros tf2_echo ${from_frame} ${to_frame} 2>&1)
    
    if [ $? -eq 0 ]; then
        # Extract translation and rotation
        trans_x=$(echo "$output" | grep "Translation:" -A 1 | grep "x:" | awk '{print $2}')
        trans_y=$(echo "$output" | grep "Translation:" -A 1 | grep "y:" | awk '{print $2}')
        trans_z=$(echo "$output" | grep "Translation:" -A 1 | grep "z:" | awk '{print $2}')
        
        rot_x=$(echo "$output" | grep "Rotation:" -A 1 | grep "x:" | awk '{print $2}')
        rot_y=$(echo "$output" | grep "Rotation:" -A 1 | grep "y:" | awk '{print $2}')
        rot_z=$(echo "$output" | grep "Rotation:" -A 1 | grep "z:" | awk '{print $2}')
        rot_w=$(echo "$output" | grep "Rotation:" -A 1 | grep "w:" | awk '{print $2}')
        
        echo -e "${GREEN}✓ Transform Available${NC}"
        echo "  Translation: [${trans_x}, ${trans_y}, ${trans_z}]"
        echo "  Rotation (quat): [${rot_x}, ${rot_y}, ${rot_z}, ${rot_w}]"
    else
        echo -e "${RED}✗ Transform NOT Available${NC}"
        echo "  Error: Transform from '${from_frame}' to '${to_frame}' not found"
    fi
    
    echo ""
}

# Main monitoring loop
while true; do
    clear
    echo "========================================="
    echo "ROS2 TF Transform Monitor"
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================="
    echo ""
    
    # Monitor critical transforms
    monitor_transform "map" "odom" "map -> odom (Published by AMCL)"
    monitor_transform "odom" "base_link" "odom -> base_link (Published by Odometry/Gazebo)"
    monitor_transform "map" "base_link" "map -> base_link (Full Localization Chain)"
    
    echo "========================================="
    echo "Press Ctrl+C to stop monitoring"
    echo "========================================="
    
    # Wait before next update
    sleep 1
done
