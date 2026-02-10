import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def launch_setup(context: LaunchContext, use_sim_time_arg, world_arg, map_arg):
    """Setup function to dynamically compute map path and launch appropriate components"""
    launch_actions = []

    use_sim_time = use_sim_time_arg.perform(context)
    world = world_arg.perform(context)
    map_path = map_arg.perform(context)

    print(f"[DEBUG] use_sim_time: '{use_sim_time}' (Type: {type(use_sim_time)})")

    # Normalize boolean string
    is_sim = use_sim_time.lower() == "true"

    # If map is provided but is just a name (not a path/file that exists), try to find it
    if map_path and not os.path.exists(map_path):
        try:
            # Check if it's in steve_simulation/maps
            sim_pkg_share = get_package_share_directory("steve_simulation")
            potential_map = os.path.join(sim_pkg_share, "maps", f"{map_path}.yaml")
            
            if os.path.exists(potential_map):
                print(f"[INFO] Auto-resolved map '{map_path}' to: {potential_map}")
                map_path = potential_map
            else:
                # Try without .yaml extension in case user didn't provide it but file has it
                # or if user provided it but we constructed double .yaml above
                # Let's be robust:
                # 1. Try name as is in maps dir
                potential_map_asis = os.path.join(sim_pkg_share, "maps", map_path)
                if os.path.exists(potential_map_asis):
                     print(f"[INFO] Auto-resolved map '{map_path}' to: {potential_map_asis}")
                     map_path = potential_map_asis
                # 2. Try adding .yaml if not present
                elif not map_path.endswith('.yaml'):
                     potential_map_yaml = os.path.join(sim_pkg_share, "maps", f"{map_path}.yaml")
                     if os.path.exists(potential_map_yaml):
                         print(f"[INFO] Auto-resolved map '{map_path}' to: {potential_map_yaml}")
                         map_path = potential_map_yaml
        except Exception as e:
            print(f"[WARN] Could not resolve map path for '{map_path}': {e}")

    # If map is not explicitly provided AND we're in simulation, derive it from world name
    if is_sim and map_path == "":
        # Extract world name if it's a built-in world
        if world in ["neo_workshop", "neo_track1", "small_house"]:
            world_name = world
        else:
            # For custom world paths, try to extract the base name
            world_name = os.path.splitext(os.path.basename(world))[0]

        # Construct map path
        try:
            map_path = os.path.join(
                get_package_share_directory("steve_simulation"),
                "maps",
                f"{world_name}.yaml",
            )
            print(f"[INFO] Auto-detected map file for simulation: {map_path}")
        except Exception as e:
            print(f"[WARN] Could not auto-detect map for simulation: {e}")

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
                "use_rviz": "false",  # We'll launch our own RViz with localization config
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

    # --- 3. LOCALIZATION (AMCL) ---
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_navigation"),
                "launch",
                "localization_amcl.launch.py",
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "map": map_path,
            "params_file": os.path.join(
                get_package_share_directory("steve_navigation"),
                "config",
                "localization.yaml",
            ),
        }.items(),
    )

    # --- 4. NAVIGATION (Nav2) ---
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("steve_navigation"),
                "launch",
                "navigation_neo.launch.py",
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": os.path.join(
                get_package_share_directory("steve_navigation"),
                "config",
                "navigation.yaml",
            ),
            "use_rviz": "false",  # We'll launch our own RViz with localization config
        }.items(),
    )

    # --- 5. RVIZ ---
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
                "localization_rviz.rviz",
            ),
        ],
        parameters=[{"use_sim_time": is_sim}],
        condition=IfCondition(LaunchConfiguration("use_rviz")),
    )

    launch_actions.append(localization_launch)
    launch_actions.append(navigation_launch)
    launch_actions.append(rviz_node)

    return launch_actions


def generate_launch_description():
    """
    Unified localization launch file for both simulation and real robot.

    This launch file supports both Gazebo simulation and real MMO-700 robot hardware
    for AMCL localization with Nav2 navigation stack.

    Usage:
        # Simulation mode (map auto-detected from world name):
        ros2 launch steve_navigation localization.launch.py use_sim_time:=true world:=small_house

        # Simulation mode (explicit map):
        ros2 launch steve_navigation localization.launch.py use_sim_time:=true map:=/path/to/map.yaml

        # Real robot mode:
        ros2 launch steve_navigation localization.launch.py use_sim_time:=false map:=/path/to/map.yaml

    Optional arguments:
        use_sim_time:=false (default: false - set to true for simulation)
        world:=small_house (default: small_house - only used in simulation)
        map:= (default: empty - auto-detected in sim, REQUIRED for real robot)
        arm_type:=ur5e (default: ur5e)
        enable_camera:=true (default: true - only used for real robot)
        enable_joystick:=true (default: true - only used for real robot)
        use_rviz:=auto (default: auto - true for sim, false for real robot)
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

    declare_map_arg = DeclareLaunchArgument(
        "map",
        default_value="",
        description="Full path to map yaml file. If empty in simulation, auto-detects based on world name. REQUIRED for real robot.",
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
    map_arg = LaunchConfiguration("map")

    ld.add_action(declare_use_sim_time_arg)
    ld.add_action(declare_world_arg)
    ld.add_action(declare_map_arg)
    ld.add_action(declare_arm_type_arg)
    ld.add_action(declare_enable_camera_arg)
    ld.add_action(declare_enable_joystick_arg)
    ld.add_action(declare_use_rviz_arg)

    # Use OpaqueFunction to dynamically compute map path and launch components
    ld.add_action(
        OpaqueFunction(
            function=launch_setup, args=[use_sim_time_arg, world_arg, map_arg]
        )
    )

    return ld
