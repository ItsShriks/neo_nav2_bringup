# neo_nav2_bringup

Common Nav2 bringup package for Neobotix robots, supporting both simulation and real hardware.

## Overview

This package provides launch files for:
- **Simulation**: Gazebo-based simulation with localization and SLAM
- **Real Robot**: Hardware bringup, localization, and SLAM for physical robots

## Documentation

Official documentation: https://neobotix-docs.de/ros/packages/neo_nav2_bringup.html

---

## Simulation Launch Files

### Localization (Simulation)
```bash
ros2 launch neo_nav2_bringup localization_simulation.launch.py
```
Launches Gazebo simulation + AMCL localization + Nav2 navigation.

### SLAM (Simulation)
```bash
ros2 launch neo_nav2_bringup slam_simulation.launch.py
```
Launches Gazebo simulation + SLAM for map building.

---

## Real Robot Launch Files

### 1. Hardware Bringup Only
```bash
ros2 launch neo_nav2_bringup robot_bringup.launch.py
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
ros2 launch neo_nav2_bringup slam.launch.py
```
Brings up hardware + SLAM for creating new maps.

**Save map after building:**
```bash
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
```

### 3. Localization (Real Robot)
```bash
ros2 launch neo_nav2_bringup localization.launch.py map:=/path/to/map.yaml
```
Brings up hardware + localization + navigation with existing map.

**Example:**
```bash
ros2 launch neo_nav2_bringup localization.launch.py \
    map:=~/maps/my_map.yaml \
    use_rviz:=true
```

### 4. Standalone Joystick Control
```bash
ros2 launch neo_nav2_bringup teleop.launch.py
```
Launches only joystick control (when robot is already running).

---

## Quick Start Guide

### For Simulation
1. Launch localization simulation:
   ```bash
   ros2 launch neo_nav2_bringup localization_simulation.launch.py
   ```
2. Set initial pose in RViz (2D Pose Estimate)
3. Send navigation goals (2D Nav Goal)

### For Real Robot

#### First Time - Build a Map
1. Launch SLAM:
   ```bash
   ros2 launch neo_nav2_bringup slam.launch.py
   ```
2. Drive robot around with joystick (hold LB + left stick)
3. Save map:
   ```bash
   ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
   ```

#### Normal Operation - Navigate with Map
1. Launch localization:
   ```bash
   ros2 launch neo_nav2_bringup localization.launch.py \
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

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review official documentation
3. Verify all hardware connections
4. Check ROS2 logs: `ros2 launch --log-level debug`

---

