import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    ld = LaunchDescription()

    # --- SLAM / NAVIGATION ---
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'launch', 'mapping.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'False',
            'param_file': os.path.join(get_package_share_directory('neo_nav2_bringup'), 'config', 'mapping.yaml')
        }.items()
    )

    ld.add_action(slam_launch)

    return ld