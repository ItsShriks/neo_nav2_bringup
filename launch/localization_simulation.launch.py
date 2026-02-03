import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchContext
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def launch_setup(context: LaunchContext, world_arg, map_arg):
    """Setup function to dynamically compute map path based on world selection"""
    launch_actions = []
    
    world = world_arg.perform(context)
    map_path = map_arg.perform(context)
    
    # If map is not explicitly provided, derive it from world name
    # This handles cases where world is 'neo_workshop', 'neo_track1', 'small_house'
    if map_path == '':
        # Extract world name if it's a built-in world
        if world in ['neo_workshop', 'neo_track1', 'small_house']:
            world_name = world
        else:
            # For custom world paths, try to extract the base name
            world_name = os.path.splitext(os.path.basename(world))[0]
        
        # Construct map path
        map_path = os.path.join(
            get_package_share_directory('neo_simulation2'), 
            'maps', 
            f'{world_name}.yaml'
        )
        print(f"[INFO] Auto-detected map file: {map_path}")
    
    # Launch Simulation
    simulation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_simulation2'), 'launch', 'simulation.launch.py')
        ),
        launch_arguments={
            'my_robot': 'mmo_700',
            'world': world,
            'use_sim_time': 'true',
            'arm_type': 'ur5e',
            'include_pan_tilt': 'true',
            'use_rviz': 'false'  # Disable simulation RViz, use navigation RViz instead
        }.items()
    )

    # Launch Localization
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'launch', 'localization_amcl.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'map': map_path,
            'params_file': os.path.join(get_package_share_directory('neo_nav2_bringup'), 'config', 'localization.yaml')
        }.items()
    )

    # Launch Navigation
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'launch', 'navigation_neo.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'params_file': os.path.join(get_package_share_directory('neo_nav2_bringup'), 'config', 'navigation.yaml'),
            'use_rviz': 'True'  # Enable navigation RViz for visualization
        }.items()
    )

    launch_actions.append(simulation_launch)
    launch_actions.append(localization_launch)
    launch_actions.append(navigation_launch)
    
    return launch_actions

def generate_launch_description():
    ld = LaunchDescription()

    # Declare world argument with small_house as default
    declare_world_arg = DeclareLaunchArgument(
        'world',
        default_value='small_house',
        description='World to load in Gazebo. Available: "neo_workshop", "neo_track1", "small_house", or full path to .world file'
    )

    # Declare map argument (optional - will auto-detect from world if not provided)
    declare_map_arg = DeclareLaunchArgument(
        'map',
        default_value='',
        description='Full path to map yaml file to load. If empty, will auto-detect based on world name.'
    )

    world_arg = LaunchConfiguration('world')
    map_arg = LaunchConfiguration('map')

    ld.add_action(declare_world_arg)
    ld.add_action(declare_map_arg)
    
    # Use OpaqueFunction to dynamically compute map path
    ld.add_action(OpaqueFunction(
        function=launch_setup,
        args=[world_arg, map_arg]
    ))

    return ld
