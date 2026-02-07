# steve_navigation

**Navigation & SLAM Package** for the Steve Butler robot.

This package provides the launch files and configurations to run the ROS 2 Navigation Stack (Nav2) and SLAM Toolbox on both the real robot and in simulation.

## Overview

This package orchestrates:
- **Autonomous Navigation**: Path planning, obstacle avoidance, and goal execution via Nav2.
- **SLAM (Simultaneous Localization and Mapping)**: Building 2D maps using LiDAR data.
- **Localization (AMCL)**: Localizing the robot within an existing map.

It relies on **`steve_essentials`** for underlying hardware drivers (LiDAR, Odometry, TF) and simulation descriptions.

---

## Launch Instructions

### 1. Quick Start: Full Navigation (Simulation)
Launch everything (Gazebo + AMCL + Nav2 + RViz) with a single command:

```bash
ros2 launch steve_navigation localization.launch.py use_sim_time:=true
```

This uses the default map and world (`small_house`).

### 2. Customizing the Environment
You can specify a different world or map using launch arguments:

**Using a Custom Map:**
```bash
ros2 launch steve_navigation localization.launch.py \
    use_sim_time:=true \
    map:=/path/to/my_map.yaml
```

**Using a Different Simulation World:**
```bash
ros2 launch steve_navigation localization.launch.py \
    use_sim_time:=true \
    world:=neo_track1
```

**Combining Both:**
```bash
ros2 launch steve_navigation localization.launch.py \
    use_sim_time:=true \
    world:=/path/to/custom.world \
    map:=/path/to/custom_map.yaml
```

### 3. SLAM (Building a Map)
To create a new map from scratch:

**Simulation:**
```bash
ros2 launch steve_navigation slam.launch.py use_sim_time:=true
```

**Real Robot:**
```bash
ros2 launch steve_navigation slam.launch.py use_sim_time:=false
```

Once you have mapped the area, save the map:
```bash
ros2 run nav2_map_server map_saver_cli -f ~/my_new_map
```

---

## Programmatic Navigation

You can send navigation goals via the command line or Python API using `nav2_navigator.py`.

**Command-Line Example:**
```bash
# Navigate to x=2.0, y=1.5, yaw=90 degrees
ros2 run steve_navigation nav2_navigator.py --x 2.0 --y 1.5 --yaw 1.57
```

**Python API Example:**
```python
from nav2_navigator import Nav2Navigator

navigator = Nav2Navigator()
navigator.go_to_pose(x=2.0, y=1.5, yaw=1.57)
```

---

## Dependencies

- **`steve_essentials`**: Provides robot description, hardware drivers, and sensor transforms.
- **`nav2_bringup`**: Core navigation stack.
- **`slam_toolbox`**: SLAM implementation.

---

## Troubleshooting

### "Map not found"
Ensure the path provided to the `map:=` argument is absolute. Relative paths may not resolve correctly.

### "Robot not moving"
- Check if the emergency stop is active.
- Verify that the Nav2 stack is active (`ros2 node list | grep nav2`).
- Check if the robot is localized (cloud of arrows in RViz should match robot position).

For hardware-specific issues, check the [steve_hardware_bringup README](../steve_hardware_bringup/README.md).

---

### Acknowledgements
- **Rohit Menon** - For mentorship and technical guidance on Neobotix platforms.
- **Prof. Maren Bennewitz** - Head of the Humanoid Robots Lab, University of Bonn.
