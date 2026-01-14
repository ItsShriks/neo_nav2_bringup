import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """
    Standalone teleop launch file for joystick control.
    
    This launch file starts only the joystick nodes for manual robot control.
    Use this when the robot is already running and you just want to add joystick control.
    
    Usage:
        ros2 launch neo_nav2_bringup teleop.launch.py
    
    Note: Make sure your Logitech joystick is connected to /dev/input/js0
    You can check with: ls -l /dev/input/js*
    """
    ld = LaunchDescription()

    # Joy node - publishes sensor_msgs/Joy messages from the joystick
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'dev': '/dev/input/js0',  # Default joystick device
            'deadzone': 0.05,
            'autorepeat_rate': 20.0
        }],
        output='screen'
    )

    # Teleop twist joy - converts Joy messages to Twist commands
    teleop_twist_joy = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[
            os.path.join(get_package_share_directory('neo_nav2_bringup'), 'config', 'joystick.yaml')
        ],
        output='screen'
    )

    ld.add_action(joy_node)
    ld.add_action(teleop_twist_joy)

    return ld
