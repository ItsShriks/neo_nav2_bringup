import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    ld = LaunchDescription()

    # --- 1. ROBOT BASE & ARM ---
    # Launches CAN drivers, UR5e driver, LiDARs, and IMU
    robot_base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('neo_mpo_700-2'), 'launch', 'bringup.launch.py')
        ),
        launch_arguments={
            'imu_enable': 'True',
            'd435_enable': 'False',  # Disable built-in camera to use our custom one below
            'arm_type': 'ur5e'
        }.items()
    )

    # --- 2. REALSENSE CAMERA ---
    # Delayed by 10 seconds to allow CAN bus and TF tree to stabilize.
    # 'initial_reset' is CRITICAL: it power-cycles the USB port to clear "Device Busy" errors.
    realsense_launch = TimerAction(
        period=10.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory('realsense2_camera'), 'launch', 'rs_launch.py')
                ),
                launch_arguments={
                    'enable_pointcloud': 'true',
                    'align_depth.enable': 'true',
                    'initial_reset': 'false',
                    'enable_sync': 'true',
                    'reconnect_timeout': '6.0'
                }.items()
            )
        ]
    )

    ld.add_action(robot_base_launch)
    ld.add_action(realsense_launch)

    return ld
