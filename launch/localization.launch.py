import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    """
    Real robot localization launch file.
    
    This launch file brings up the real MMO-700 robot hardware and starts
    AMCL localization with Nav2 navigation stack.
    
    Usage:
        ros2 launch neo_nav2_bringup localization.launch.py
        
    Optional arguments:
        map:=/path/to/map.yaml (required - path to your pre-built map)
        arm_type:=ur5e (default: ur5e)
        enable_camera:=true (default: true)
        enable_joystick:=true (default: true)
        use_rviz:=true (default: false)
    
    Example:
        ros2 launch neo_nav2_bringup localization.launch.py \\
            map:=/path/to/your/map.yaml \\
            use_rviz:=true
    """
    ld = LaunchDescription()

    # --- LAUNCH ARGUMENTS ---
    declare_map_arg = DeclareLaunchArgument(
        'map',
        description='Full path to map yaml file to load (REQUIRED for localization)'
    )
    
    declare_arm_type_arg = DeclareLaunchArgument(
        'arm_type',
        default_value='ur5e',
        description='UR arm type: ur5 or ur5e'
    )
    
    declare_enable_camera_arg = DeclareLaunchArgument(
        'enable_camera',
        default_value='true',
        description='Enable L515 RealSense camera'
    )
    
    declare_enable_joystick_arg = DeclareLaunchArgument(
        'enable_joystick',
        default_value='true',
        description='Enable Logitech joystick controller'
    )
    
    declare_use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz for visualization'
    )

    # --- 1. ROBOT HARDWARE BRINGUP ---
    # Launches all hardware: base platform, UR5 arm, pan-tilt camera, joystick
    robot_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'launch', 'robot_bringup.launch.py')
        ),
        launch_arguments={
            'arm_type': LaunchConfiguration('arm_type'),
            'enable_camera': LaunchConfiguration('enable_camera'),
            'enable_joystick': LaunchConfiguration('enable_joystick')
        }.items()
    )

    # --- 2. LOCALIZATION (AMCL) ---
    # Launches AMCL for localization with the provided map
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'launch', 'localization_amcl.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'false',  # CRITICAL: Real robot uses real time
            'map': LaunchConfiguration('map'),
            'params_file': os.path.join(get_package_share_directory('neo_nav2_bringup'), 'config', 'localization.yaml')
        }.items()
    )

    # --- 3. NAVIGATION (Nav2) ---
    # Launches Nav2 navigation stack
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'launch', 'navigation_neo.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'false',  # CRITICAL: Real robot uses real time
            'params_file': os.path.join(get_package_share_directory('neo_nav2_bringup'), 'config', 'navigation.yaml'),
            'use_rviz': LaunchConfiguration('use_rviz')
        }.items()
    )

    # --- ADD ALL ACTIONS ---
    ld.add_action(declare_map_arg)
    ld.add_action(declare_arm_type_arg)
    ld.add_action(declare_enable_camera_arg)
    ld.add_action(declare_enable_joystick_arg)
    ld.add_action(declare_use_rviz_arg)
    
    ld.add_action(robot_bringup_launch)
    ld.add_action(localization_launch)
    ld.add_action(navigation_launch)

    return ld
