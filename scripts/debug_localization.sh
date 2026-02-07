#!/bin/bash
# ROS2 Localization Debug Script
# This script checks all critical components of the localization system

echo "========================================="
echo "ROS2 Localization Debug Script"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if ROS2 is sourced
if [ -z "$ROS_DISTRO" ]; then
    echo -e "${RED}✗ ROS2 not sourced. Please run: source install/setup.bash${NC}"
    exit 1
fi

echo -e "${GREEN}✓ ROS2 environment sourced (ROS_DISTRO: $ROS_DISTRO)${NC}"
echo ""

# Step 1: Check Map Files
echo "========================================="
echo "Step 1: Checking Map Files"
echo "========================================="

MAP_DIR="/Users/shrikar/neo_700/steve_ros2_ws/src/steve_simulation/maps"
MAPS=("small_house" "neo_workshop" "neo_track1")

for map in "${MAPS[@]}"; do
    if [ -f "$MAP_DIR/${map}.yaml" ] && [ -f "$MAP_DIR/${map}.pgm" ]; then
        echo -e "${GREEN}✓ Map found: ${map}${NC}"
    else
        echo -e "${YELLOW}⚠ Map missing: ${map}${NC}"
    fi
done
echo ""

# Step 2: Check Running Nodes
echo "========================================="
echo "Step 2: Checking Running Nodes"
echo "========================================="

REQUIRED_NODES=("/map_server" "/amcl" "/lifecycle_manager_localization")

for node in "${REQUIRED_NODES[@]}"; do
    if ros2 node list 2>/dev/null | grep -q "$node"; then
        echo -e "${GREEN}✓ Node running: ${node}${NC}"
    else
        echo -e "${RED}✗ Node NOT running: ${node}${NC}"
    fi
done
echo ""

# Step 3: Check Lifecycle States
echo "========================================="
echo "Step 3: Checking Lifecycle Node States"
echo "========================================="

LIFECYCLE_NODES=("map_server" "amcl")

for node in "${LIFECYCLE_NODES[@]}"; do
    if ros2 node list 2>/dev/null | grep -q "/${node}"; then
        state=$(ros2 lifecycle get /${node} 2>/dev/null | grep -oP '\[\K[0-9]+' | head -1)
        state_name=$(ros2 lifecycle get /${node} 2>/dev/null | grep -oP '^[a-z]+')

        if [ "$state" == "3" ]; then
            echo -e "${GREEN}✓ /${node}: ${state_name} [${state}]${NC}"
        else
            echo -e "${RED}✗ /${node}: ${state_name} [${state}] (should be active [3])${NC}"
        fi
    else
        echo -e "${RED}✗ /${node}: NOT RUNNING${NC}"
    fi
done
echo ""

# Step 4: Check Critical Topics
echo "========================================="
echo "Step 4: Checking Critical Topics"
echo "========================================="

TOPICS=("/map" "/particlecloud" "/amcl_pose" "/lidar_1/scan" "/clock")

for topic in "${TOPICS[@]}"; do
    if ros2 topic list 2>/dev/null | grep -q "^${topic}$"; then
        # Check if topic is publishing
        timeout 2 ros2 topic echo ${topic} --once &>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Topic publishing: ${topic}${NC}"
        else
            echo -e "${YELLOW}⚠ Topic exists but not publishing: ${topic}${NC}"
        fi
    else
        echo -e "${RED}✗ Topic NOT found: ${topic}${NC}"
    fi
done
echo ""

# Step 5: Check AMCL Parameters
echo "========================================="
echo "Step 5: Checking AMCL Parameters"
echo "========================================="

if ros2 node list 2>/dev/null | grep -q "/amcl"; then
    echo "Critical AMCL Parameters:"
    echo "  base_frame_id: $(ros2 param get /amcl base_frame_id 2>/dev/null | grep -oP 'String value is: \K.*')"
    echo "  odom_frame_id: $(ros2 param get /amcl odom_frame_id 2>/dev/null | grep -oP 'String value is: \K.*')"
    echo "  global_frame_id: $(ros2 param get /amcl global_frame_id 2>/dev/null | grep -oP 'String value is: \K.*')"
    echo "  tf_broadcast: $(ros2 param get /amcl tf_broadcast 2>/dev/null | grep -oP 'Boolean value is: \K.*')"
    echo "  scan_topic: $(ros2 param get /amcl scan_topic 2>/dev/null | grep -oP 'String value is: \K.*')"
    echo "  max_particles: $(ros2 param get /amcl max_particles 2>/dev/null | grep -oP 'Integer value is: \K.*')"
    echo "  min_particles: $(ros2 param get /amcl min_particles 2>/dev/null | grep -oP 'Integer value is: \K.*')"
else
    echo -e "${RED}✗ AMCL node not running${NC}"
fi
echo ""

# Step 6: Check Map Server Parameters
echo "========================================="
echo "Step 6: Checking Map Server Parameters"
echo "========================================="

if ros2 node list 2>/dev/null | grep -q "/map_server"; then
    echo "Map Server Parameters:"
    yaml_file=$(ros2 param get /map_server yaml_filename 2>/dev/null | grep -oP 'String value is: \K.*')
    use_sim_time=$(ros2 param get /map_server use_sim_time 2>/dev/null | grep -oP 'Boolean value is: \K.*')

    echo "  yaml_filename: ${yaml_file}"
    echo "  use_sim_time: ${use_sim_time}"

    # Check if file exists
    if [ -f "${yaml_file}" ]; then
        echo -e "${GREEN}  ✓ Map file exists${NC}"
    else
        echo -e "${RED}  ✗ Map file NOT found: ${yaml_file}${NC}"
    fi
else
    echo -e "${RED}✗ Map Server node not running${NC}"
fi
echo ""

# Step 7: Check TF Tree
echo "========================================="
echo "Step 7: Checking TF Tree"
echo "========================================="

echo "Checking critical transforms..."

# Check map -> odom
timeout 2 ros2 run tf2_ros tf2_echo map odom &>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Transform available: map -> odom${NC}"
else
    echo -e "${RED}✗ Transform NOT available: map -> odom (published by AMCL)${NC}"
fi

# Check odom -> base_link
timeout 2 ros2 run tf2_ros tf2_echo odom base_link &>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Transform available: odom -> base_link${NC}"
else
    echo -e "${RED}✗ Transform NOT available: odom -> base_link (published by odometry/Gazebo)${NC}"
fi

# Check map -> base_link (full chain)
timeout 2 ros2 run tf2_ros tf2_echo map base_link &>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Transform available: map -> base_link (full chain)${NC}"
else
    echo -e "${RED}✗ Transform NOT available: map -> base_link${NC}"
fi

echo ""
echo "To visualize the full TF tree, run:"
echo "  ros2 run tf2_tools view_frames"
echo "  open frames.pdf"
echo ""

# Step 8: Check Time Synchronization
echo "========================================="
echo "Step 8: Checking Time Synchronization"
echo "========================================="

if ros2 topic list 2>/dev/null | grep -q "/clock"; then
    echo -e "${GREEN}✓ /clock topic available (simulation time)${NC}"

    # Check use_sim_time for critical nodes
    for node in "/map_server" "/amcl"; do
        if ros2 node list 2>/dev/null | grep -q "$node"; then
            use_sim=$(ros2 param get ${node} use_sim_time 2>/dev/null | grep -oP 'Boolean value is: \K.*')
            if [ "$use_sim" == "True" ]; then
                echo -e "${GREEN}✓ ${node} use_sim_time: True${NC}"
            else
                echo -e "${RED}✗ ${node} use_sim_time: ${use_sim} (should be True)${NC}"
            fi
        fi
    done
else
    echo -e "${YELLOW}⚠ /clock topic not found (not using simulation time?)${NC}"
fi

echo ""
echo "========================================="
echo "Debug Complete"
echo "========================================="
echo ""
echo "Next Steps:"
echo "1. If map is not publishing, check lifecycle manager logs"
echo "2. If TF transforms are missing, check AMCL and odometry nodes"
echo "3. If particles not visible, add ParticleCloud display in RViz"
echo "4. Use 'ros2 topic echo /particlecloud' to verify particle data"
echo ""
