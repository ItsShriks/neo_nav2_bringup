# steve_navigation

Common Nav2 bringup package for Neobotix robots, supporting both simulation and real hardware.

## Overview

This package provides launch files for:
- **Simulation**: Gazebo-based simulation with localization and SLAM
- **Real Robot**: Hardware bringup, localization, and SLAM for physical robots

## Documentation

Official documentation: https://neobotix-docs.de/ros/packages/steve_navigation.html

---

## How to Run the Simulation

### 1. Clone the repository (with submodules)
```bash
git clone --recurse-submodules git@gitlab.igg.uni-bonn.de:hrl_students/ws2526_butler/steve_ros2_ws.git -b dev
```

### 2. Build the workspace
```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select steve_simulation steve_navigation
```

### 3. Source the workspace
```bash
source install/setup.bash
```

### 4. Launch the simulation
Basic launch:
```bash
ros2 launch steve_simulation simulation.launch.py
```

### 5. Navigation and Mapping

We provide multiple launch files for different use cases:

#### Quick Start: Full Navigation Stack (Recommended)
Launch everything (simulation + localization + navigation) with a single command:
```bash
ros2 launch steve_navigation localization_simulation.launch.py
```

This automatically starts:
- Gazebo simulation with MMO-700 robot (UR5e arm + pan-tilt camera)
- AMCL localization with pre-built map
- Nav2 autonomous navigation stack
- RViz for visualization

**Using a custom map:**
```bash
ros2 launch steve_navigation localization_simulation.launch.py map:=/path/to/your/map.yaml
```

**Using a different world:**
```bash
ros2 launch steve_navigation localization_simulation.launch.py world:=neo_track1
```

**Using custom world and map:**
```bash
ros2 launch steve_navigation localization_simulation.launch.py \
  world:=/path/to/custom.world \
  map:=/path/to/custom_map.yaml
```

#### Alternative: SLAM Mapping (Build Your Own Map)

If you want to create a new map instead of using a pre-built one:
```bash
ros2 launch steve_navigation slam_simulation.launch.py
```

**Using a different world for SLAM:**
```bash
ros2 launch steve_navigation slam_simulation.launch.py world:=neo_track1
```

Then in a **separate terminal**, launch navigation:
```bash
source install/setup.bash
ros2 launch steve_navigation navigation_neo.launch.py use_sim_time:=true use_rviz:=false
```

This starts:
- Gazebo simulation with MMO-700 robot
- SLAM Toolbox for real-time mapping
- Nav2 for autonomous navigation

#### Using the Navigation Stack

1. **Wait for all nodes to start** (you'll see "Managed nodes are active" in the terminal)
2. **In RViz**, use the **2D Nav Goal** tool to set navigation goals
3. **Click and drag** on the map to set the goal pose
4. The robot will **autonomously navigate** to the goal, avoiding obstacles

**Note:** Navigation goals must be set within the mapped area (visible in RViz as colored regions).

#### Available Worlds

The simulation supports the following Gazebo worlds:
- `small_house` (default) - AWS RoboMaker small house environment
- `neo_workshop` - Indoor workshop environment
- `neo_track1` - Outdoor track environment  
- Custom worlds - Provide full path to your `.world` file

> **Tip:** When using a custom world with localization, ensure you have a corresponding map file.

---

## Programmatic Navigation (Nav2Navigator)

Send navigation goals programmatically via command line or Python API.

### Command-Line Usage

```bash
# Navigate to specific coordinates (x, y, yaw in radians)
ros2 run steve_navigation nav2_navigator.py --x 2.0 --y 1.5 --yaw 1.57

# Navigate to origin
ros2 run steve_navigation nav2_navigator.py --x 0.0 --y 0.0 --yaw 0.0

# Non-blocking mode (send goal and return immediately)
ros2 run steve_navigation nav2_navigator.py --x 3.0 --y 2.0 --yaw 0.0 --no-wait

# Use degrees with convenience script
./src/steve_navigation/scripts/send_nav_goal.sh 2.0 1.5 90
```

### Python API Usage

```python
#!/usr/bin/env python3
import rclpy
from nav2_navigator import Nav2Navigator

rclpy.init()
navigator = Nav2Navigator()

if navigator.wait_for_server(10.0):
    # Send navigation goal
    navigator.go_to_pose(
        x=2.0,      # meters
        y=1.5,      # meters
        yaw=1.57,   # radians (90 degrees)
        frame_id="map",
        wait=True   # Block until completion
    )

navigator.destroy_node()
rclpy.shutdown()
```

### Scene Graph Integration Example

Perfect for semantic navigation systems:

```python
SCENE_GRAPH = {
    "kitchen": {"x": 3.5, "y": 2.0, "yaw": 1.57},
    "living_room": {"x": 1.0, "y": 1.0, "yaw": 0.0},
}

def navigate_to_location(location_name: str):
    pose = SCENE_GRAPH[location_name]
    cmd = [
        "ros2", "run", "steve_navigation", "nav2_navigator.py",
        "--x", str(pose["x"]),
        "--y", str(pose["y"]),
        "--yaw", str(pose["yaw"])
    ]
    subprocess.run(cmd)

navigate_to_location("kitchen")
```

**Command-Line Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--x` | float | 1.0 | Target X coordinate (meters) |
| `--y` | float | 0.0 | Target Y coordinate (meters) |
| `--yaw` | float | 0.0 | Target yaw angle (radians) |
| `--frame` | string | "map" | Reference frame |
| `--no-wait` | flag | False | Non-blocking mode |

---

## Real Robot Launch Files

### 1. Hardware Bringup Only
```bash
ros2 launch steve_navigation robot_bringup.launch.py
```
Initializes all robot hardware:
- Base platform (CAN drivers, motors, IMU, LiDARs)
- UR5/UR5e arm with controllers
- Pan-tilt camera unit with L515 RealSense
- Logitech joystick controller

**Optional arguments:**
- `arm_type:=ur5e` (default: ur5e)
- `enable_camera:=true` (default: true)
- `enable_joystick:=true` (default: true)

### 2. SLAM (Real Robot)
```bash
ros2 launch steve_navigation slam.launch.py
```
Brings up hardware + SLAM for creating new maps.

**Save map after building:**
```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
```

### 3. Localization (Real Robot)
```bash
ros2 launch steve_navigation localization.launch.py map:=/path/to/map.yaml
```
Brings up hardware + localization + navigation with existing map.

**Example:**
```bash
ros2 launch steve_navigation localization.launch.py \
    map:=~/maps/my_map.yaml \
    use_rviz:=true
```

### 4. Standalone Joystick Control
```bash
ros2 launch steve_navigation teleop.launch.py
```
Launches only joystick control (when robot is already running).

---

## Quick Start Guide

### For Simulation
1. Launch localization simulation:
   ```bash
   ros2 launch steve_navigation localization_simulation.launch.py
   ```
2. Set initial pose in RViz (2D Pose Estimate)
3. Send navigation goals (2D Nav Goal or programmatically)

### For Real Robot

#### First Time - Build a Map
1. Launch SLAM:
   ```bash
   ros2 launch steve_navigation slam.launch.py
   ```
2. Drive robot around with joystick (hold LB + left stick)
3. Save map:
   ```bash
   ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
   ```

#### Normal Operation - Navigate with Map
1. Launch localization:
   ```bash
   ros2 launch steve_navigation localization.launch.py \
       map:=~/maps/my_map.yaml \
       use_rviz:=true
   ```
2. Set initial pose in RViz
3. Send navigation goals

---

## Hardware Components (Real Robot)

- **Base Platform**: MMO-700 omnidirectional mobile base
- **LiDARs**: 2x laser scanners for obstacle detection
- **Camera**: L515 RealSense on pan-tilt unit
- **Arm**: UR5/UR5e with Robotiq gripper
- **Joystick**: Logitech controller via USB dongle
- **IMU**: Inertial measurement unit

---

## Key Differences: Simulation vs Real Robot

| Feature | Simulation | Real Robot |
|---------|-----------|------------|
| Launch file suffix | `_simulation.launch.py` | `.launch.py` |
| `use_sim_time` | `true` | `false` |
| Hardware bringup | Gazebo | `robot_bringup.launch.py` |
| Initialization delays | None | 5s, 10s for hardware |

---

## Troubleshooting

### Camera Not Starting
- Check USB connection
- Verify with: `rs-enumerate-devices`
- Camera has 10s initialization delay

### Joystick Not Working
- Check device: `ls -l /dev/input/js*`
- Verify permissions: `sudo chmod a+rw /dev/input/js0`
- Hold LB button to enable movement

### No Localization
- Verify map is loaded: `ros2 topic echo /map --once`
- Set initial pose in RViz
- Check AMCL is running: `ros2 node list | grep amcl`

### TF Errors
- Generate TF tree: `ros2 run tf2_tools view_frames`
- Check robot_state_publisher is running

### Navigation Goal Not Working
- Ensure Nav2 is running: `ros2 node list | grep nav2`
- Check action server: `ros2 action list | grep navigate_to_pose`
- Verify robot is localized on the map

---

## Configuration Files

- `config/localization.yaml` - AMCL parameters
- `config/navigation.yaml` - Nav2 parameters
- `config/mapping.yaml` - SLAM parameters
- `config/joystick.yaml` - Joystick button mappings

---

## Dependencies

### Required Packages
- `neo_mpo_700-2` - Base platform drivers
- `realsense2_camera` - RealSense camera driver
- `nav2_bringup` - Nav2 navigation stack
- `slam_toolbox` - SLAM implementation
- `joy` - Joystick driver
- `teleop_twist_joy` - Joystick teleop

### Installation
```bash
sudo apt install ros-humble-nav2-bringup \
                 ros-humble-slam-toolbox \
                 ros-humble-joy \
                 ros-humble-teleop-twist-joy
```

---

## Visuals
![Gazebo Simulation](images/gazebo.png)
![RViz Visualization](images/rviz.png)

---

## (Optional) Using Docker
This workspace is configured with a DevContainer for easy setup.

### Option 1: VSCode DevContainer (Recommended)
1. Open the workspace in VSCode.
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and select **"Dev Containers: Reopen in Container"**.
3. VSCode will automatically build the image and set up the environment.

### Option 2: Build and Run Manually
Since the DevContainer is configured to build from source, you can also build and run the image manually:
1. Build the image:

```bash
   docker build \
  --network=host \
  --build-arg DOCKER_REPO=osrf/ros \
  --build-arg ROS_DISTRO=humble \
  --build-arg IMAGE_SUFFIX=-desktop-full \
  --build-arg USERNAME=$(whoami) \
  --build-arg USER_UID=$(id -u) \
  --build-arg USER_GID=$(id -g) \
  -t test_nav2:latest \
  -f .devcontainer/Dockerfile .
```

2. Run the container:

```bash
   docker run -it --rm --net=host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd):/home/steve_ros2_ws \
  -v ~/.ssh:/home/$(whoami)/.ssh \
  -w /home/steve_ros2_ws \
  test_nav2:latest
```

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review official documentation
3. Verify all hardware connections
4. Check ROS2 logs: `ros2 launch --log-level debug`

---

For more details, see the [Neobotix ROS2 simulation documentation](https://neobotix-docs.de/ros/ros2/simulation_classic.html) and the [modern Gazebo migration guide](https://neobotix-docs.de/ros/ros2/simulation_modern.html).

---
Since the classic gazebo has reached End of Life, There will be no further updates to this packages. 

All the robots in this packages have been migrated to modern Gazebo with some more additional features. More information about the installation and usage of the new modern Gazebo simulation can be [found in our documentation.](https://neobotix-docs.de/ros/ros2/simulation_modern.html)
