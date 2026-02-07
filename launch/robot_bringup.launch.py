import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """
    Comprehensive hardware bringup for the real MMO-700 robot.

    This launch file is a wrapper around steve_hardware_bringup/hardware_bringup.launch.py
    that initializes all hardware components:
    - Base platform (CAN drivers, motors, IMU, LiDARs)
    - UR5/UR5e arm with controllers
    - Pan-tilt camera unit with L515 RealSense
    - Logitech joystick controller

    Usage:
        ros2 launch steve_navigation robot_bringup.launch.py

    Optional arguments:
        arm_type:=ur5e (default: ur5e, options: ur5, ur5e)
        enable_camera:=true (default: true)
        enable_joystick:=true (default: true - note: uses neo_teleop2)
    """
    ld = LaunchDescription()

    # --- LAUNCH ARGUMENTS ---
    declare_arm_type_arg = DeclareLaunchArgument(
        "arm_type", default_value="ur5e", description="UR arm type: ur5 or ur5e"
    )

    declare_enable_camera_arg = DeclareLaunchArgument(
        "enable_camera",
        default_value="true",
        description="Enable L515 RealSense camera on pan-tilt unit",
    )

    declare_enable_joystick_arg = DeclareLaunchArgument(
        "enable_joystick",
        default_value="true",
        description="Enable Logitech joystick controller (uses neo_teleop2)",
    )

    # --- HARDWARE BRINGUP ---
    # Launches all hardware components via steve_hardware_bringup
    # This includes: CAN drivers, motor controllers, LiDARs, IMU, UR5e arm, pan-tilt, camera, and teleop
    robot_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_hardware_bringup"),
                "launch",
                "hardware_bringup.launch.py",
            )
        ),
        launch_arguments={
            "arm_type": LaunchConfiguration("arm_type"),
            "enable_camera": LaunchConfiguration("enable_camera"),
            "enable_pan_tilt": "true",  # Always enable pan-tilt for navigation
            # Note: enable_joystick is handled internally by hardware_bringup.launch.py
            # It always launches teleop via neo_teleop2
        }.items(),
    )

    # --- ADD ALL ACTIONS ---
    ld.add_action(declare_arm_type_arg)
    ld.add_action(declare_enable_camera_arg)
    ld.add_action(declare_enable_joystick_arg)

    ld.add_action(robot_base_launch)

    return ld
