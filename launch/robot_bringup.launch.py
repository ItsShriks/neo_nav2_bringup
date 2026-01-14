import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    """
    Comprehensive hardware bringup for the real MMO-700 robot.
    
    This launch file initializes all hardware components:
    - Base platform (CAN drivers, motors, IMU, LiDARs)
    - UR5/UR5e arm with controllers
    - Pan-tilt camera unit with L515 RealSense
    - Logitech joystick controller
    
    Usage:
        ros2 launch neo_nav2_bringup robot_bringup.launch.py
        
    Optional arguments:
        arm_type:=ur5e (default: ur5e, options: ur5, ur5e)
        enable_camera:=true (default: true)
        enable_joystick:=true (default: true)
    """
    ld = LaunchDescription()

    # --- LAUNCH ARGUMENTS ---
    declare_arm_type_arg = DeclareLaunchArgument(
        'arm_type',
        default_value='ur5e',
        description='UR arm type: ur5 or ur5e'
    )
    
    declare_enable_camera_arg = DeclareLaunchArgument(
        'enable_camera',
        default_value='true',
        description='Enable L515 RealSense camera on pan-tilt unit'
    )
    
    declare_enable_joystick_arg = DeclareLaunchArgument(
        'enable_joystick',
        default_value='true',
        description='Enable Logitech joystick controller'
    )

    # --- 1. BASE PLATFORM & CORE DRIVERS ---
    # Launches CAN drivers, motor controllers, UR5e driver, LiDARs, and IMU
    # This assumes you have the neo_mpo_700-2 package installed
    robot_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_mpo_700-2'), 'launch', 'bringup.launch.py')
        ),
        launch_arguments={
            'imu_enable': 'True',
            'd435_enable': 'False',  # Disable built-in camera, using L515 instead
            'arm_type': LaunchConfiguration('arm_type')
        }.items()
    )

    # --- 2. PAN-TILT CONTROLLER ---
    # Delayed by 5 seconds to allow CAN bus and TF tree to stabilize
    # This controller manages the servo motors for pan and tilt movements
    pan_tilt_controller = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=['pan_tilt_controller', '-c', '/controller_manager'],
                output='screen'
            )
        ]
    )

    # --- 3. L515 REALSENSE CAMERA ---
    # Delayed by 10 seconds to allow USB initialization and TF tree stabilization
    # The L515 is mounted on the pan-tilt unit
    realsense_launch = TimerAction(
        period=10.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')
                ),
                launch_arguments={
                    'camera_name': 'l515',
                    'device_type': 'l515',
                    'enable_pointcloud': 'true',
                    'align_depth.enable': 'true',
                    'initial_reset': 'true',  # Power-cycle USB to clear "Device Busy" errors
                    'enable_sync': 'true',
                    'reconnect_timeout': '6.0',
                    'enable_color': 'true',
                    'enable_depth': 'true'
                }.items(),
                condition=IfCondition(LaunchConfiguration('enable_camera'))
            )
        ]
    )

    # --- 4. JOYSTICK CONTROLLER ---
    # Logitech joystick for manual robot control
    # joy_node publishes sensor_msgs/Joy messages
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'dev': '/dev/input/js0',  # Default joystick device
            'deadzone': 0.05,
            'autorepeat_rate': 20.0
        }],
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_joystick'))
    )

    # teleop_twist_joy converts Joy messages to Twist commands
    teleop_twist_joy = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'config', 'joystick.yaml')
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('enable_joystick'))
    )

    # --- ADD ALL ACTIONS ---
    ld.add_action(declare_arm_type_arg)
    ld.add_action(declare_enable_camera_arg)
    ld.add_action(declare_enable_joystick_arg)
    
    ld.add_action(robot_base_launch)
    ld.add_action(pan_tilt_controller)
    ld.add_action(realsense_launch)
    ld.add_action(joy_node)
    ld.add_action(teleop_twist_joy)

    return ld
