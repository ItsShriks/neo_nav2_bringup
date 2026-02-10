import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context: LaunchContext, use_sim_time_arg, world_arg):
    """Setup function to dynamically launch appropriate components based on use_sim_time"""
    launch_actions = []

    use_sim_time = use_sim_time_arg.perform(context)
    world = world_arg.perform(context)

    print(
        f"[DEBUG] SLAM Launch - use_sim_time: '{use_sim_time}' (Type: {type(use_sim_time)})"
    )

    # Normalize boolean string
    is_sim = use_sim_time.lower() == "true"

    # --- 1. SIMULATION BRINGUP (only if use_sim_time=true) ---
    if is_sim:
        simulation_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory("steve_simulation"),
                    "launch",
                    "simulation.launch.py",
                )
            ),
            launch_arguments={
                "my_robot": "mmo_700",
                "world": world,
                "use_sim_time": "true",
                "arm_type": LaunchConfiguration("arm_type"),
                "include_pan_tilt": "true",
                "use_rviz": "false",  # We'll launch our own RViz with SLAM config
                "launch_map_server": "false",
            }.items(),
        )
        launch_actions.append(simulation_launch)

    # --- 2. REAL ROBOT HARDWARE BRINGUP (only if use_sim_time=false) ---
    else:
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
        launch_actions.append(robot_bringup_launch)

    # --- 3. SLAM / MAPPING ---
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_navigation"),
                "launch",
                "mapping.launch.py",
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "param_file": os.path.join(
                get_package_share_directory("steve_navigation"),
                "config",
                "mapping.yaml",
            ),
        }.items(),
    )
    launch_actions.append(slam_launch)

    # --- 4. RVIZ ---
    # Launch RViz if use_rviz=true OR (use_rviz=auto AND use_sim_time=true)
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=[
            "-d",
            os.path.join(
                get_package_share_directory("steve_navigation"),
                "rviz",
                "slam_rviz.rviz",
            ),
        ],
        parameters=[{"use_sim_time": is_sim}],
        condition=IfCondition(LaunchConfiguration("use_rviz")),
    )
    launch_actions.append(rviz_node)

    return launch_actions


def generate_launch_description():
    """
    Unified SLAM launch file for both simulation and real robot.

    This launch file supports both Gazebo simulation and real MMO-700 robot hardware
    for SLAM (Simultaneous Localization and Mapping) / map building.

    Usage:
        # Simulation mode:
        ros2 launch steve_navigation slam.launch.py use_sim_time:=true world:=small_house

        # Real robot mode:
        ros2 launch steve_navigation slam.launch.py use_sim_time:=false

    Optional arguments:
        use_sim_time:=false (default: false - set to true for simulation)
        world:=small_house (default: small_house - only used in simulation)
        arm_type:=ur5e (default: ur5e)
        enable_camera:=true (default: true - only used for real robot)
        enable_joystick:=true (default: true - only used for real robot)
        use_rviz:=auto (default: auto - true for sim, false for real robot)

    After mapping, save your map with:
        ros2 run nav2_map_server map_saver_cli -f /path/to/save/map_name
    """
    ld = LaunchDescription()

    # --- LAUNCH ARGUMENTS ---
    declare_use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="true",
        description="Use simulation time (true) or real robot (false)",
    )

    declare_world_arg = DeclareLaunchArgument(
        "world",
        default_value="small_house",
        description='World to load in Gazebo (simulation only). Available: "neo_workshop", "neo_track1", "small_house", or full path to .world file',
    )

    declare_arm_type_arg = DeclareLaunchArgument(
        "arm_type", default_value="ur5e", description="UR arm type: ur5 or ur5e"
    )

    declare_enable_camera_arg = DeclareLaunchArgument(
        "enable_camera",
        default_value="true",
        description="Enable L515 RealSense camera (real robot only)",
    )

    declare_enable_joystick_arg = DeclareLaunchArgument(
        "enable_joystick",
        default_value="true",
        description="Enable Logitech joystick controller (real robot only)",
    )

    declare_use_rviz_arg = DeclareLaunchArgument(
        "use_rviz",
        default_value="true",
        description="Launch RViz for visualization",
    )

    use_sim_time_arg = LaunchConfiguration("use_sim_time")
    world_arg = LaunchConfiguration("world")

    ld.add_action(declare_use_sim_time_arg)
    ld.add_action(declare_world_arg)
    ld.add_action(declare_arm_type_arg)
    ld.add_action(declare_enable_camera_arg)
    ld.add_action(declare_enable_joystick_arg)
    ld.add_action(declare_use_rviz_arg)

    # Use OpaqueFunction to dynamically compute map path and launch components
    ld.add_action(
        OpaqueFunction(function=launch_setup, args=[use_sim_time_arg, world_arg])
    )

    return ld
