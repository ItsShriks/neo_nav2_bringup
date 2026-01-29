import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()

    # Declare world argument
    declare_world_arg = DeclareLaunchArgument(
        'world',
        default_value='small_house',
        description='World to load in Gazebo. Available: "neo_workshop", "neo_track1", "small_house", or full path to .world file'
    )

    # Launch Simulation
    simulation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_simulation2'), 'launch', 'simulation.launch.py')
        ),
        launch_arguments={
            'my_robot': 'mmo_700',
            'world': LaunchConfiguration('world'),
            'use_sim_time': 'true',
            'arm_type': 'ur5e',
            'include_pan_tilt': 'true'
            
        }.items()
    )

    # Launch SLAM
    mapping_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'launch', 'mapping.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'param_file': os.path.join(get_package_share_directory('neo_nav2_bringup'), 'config', 'mapping.yaml')
        }.items()
    )

    ld.add_action(declare_world_arg)
    ld.add_action(simulation_launch)
    ld.add_action(mapping_launch)

    return ld
