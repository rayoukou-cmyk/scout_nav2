#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_nav2 = get_package_share_directory('scout_mini_nav2')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    slam_params_file = LaunchConfiguration('slam_params_file')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock'
    )

    declare_slam_params = DeclareLaunchArgument(
        'slam_params_file',
        default_value=os.path.join(pkg_nav2, 'config', 'slam_toolbox.yaml'),
        description='Full path to SLAM Toolbox parameters YAML file'
    )

    slam_toolbox = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': use_sim_time}
        ],
        remappings=[
            ('/scan', '/front_lidar_scan'),  # Use front LiDAR for SLAM
        ]
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_slam_params,
        slam_toolbox,
    ])
