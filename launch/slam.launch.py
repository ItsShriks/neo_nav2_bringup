import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """
    Real robot SLAM launch file.

    This launch file brings up the real MMO-700 robot hardware and starts
    SLAM (Simultaneous Localization and Mapping) for map building.

    Usage:
        ros2 launch steve_navigation slam.launch.py

    Optional arguments:
        arm_type:=ur5e (default: ur5e)
        enable_camera:=true (default: true)
        enable_joystick:=true (default: true)

    After mapping, save your map with:
        ros2 run nav2_map_server map_saver_cli -f /path/to/save/map_name
    """
    ld = LaunchDescription()

    # --- LAUNCH ARGUMENTS ---
    declare_arm_type_arg = DeclareLaunchArgument(
        "arm_type", default_value="ur5e", description="UR arm type: ur5 or ur5e"
    )

    declare_enable_camera_arg = DeclareLaunchArgument(
        "enable_camera",
        default_value="true",
        description="Enable L515 RealSense camera",
    )

    declare_enable_joystick_arg = DeclareLaunchArgument(
        "enable_joystick",
        default_value="true",
        description="Enable Logitech joystick controller",
    )

    # --- 1. ROBOT HARDWARE BRINGUP ---
    # Launches all hardware: base platform, UR5 arm, pan-tilt camera, joystick
    robot_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_navigation"),
                "launch",
                "robot_bringup.launch.py",
            )
        ),
        launch_arguments={
            "arm_type": LaunchConfiguration("arm_type"),
            "enable_camera": LaunchConfiguration("enable_camera"),
            "enable_joystick": LaunchConfiguration("enable_joystick"),
        }.items(),
    )

    # --- 2. SLAM / MAPPING ---
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_navigation"),
                "launch",
                "mapping.launch.py",
            )
        ),
        launch_arguments={
            "use_sim_time": "false",  # CRITICAL: Real robot uses real time
            "param_file": os.path.join(
                get_package_share_directory("steve_navigation"),
                "config",
                "mapping.yaml",
            ),
        }.items(),
    )

    # --- ADD ALL ACTIONS ---
    ld.add_action(declare_arm_type_arg)
    ld.add_action(declare_enable_camera_arg)
    ld.add_action(declare_enable_joystick_arg)

    ld.add_action(robot_bringup_launch)
    ld.add_action(slam_launch)

    return ld
