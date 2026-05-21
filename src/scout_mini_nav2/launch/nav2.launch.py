#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_nav2 = get_package_share_directory('scout_mini_nav2')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    map_yaml_file = LaunchConfiguration('map', default=os.path.join(pkg_nav2, 'maps', 'test_map.yaml'))
    params_file = LaunchConfiguration('params_file', default=os.path.join(pkg_nav2, 'config', 'nav2_params.yaml'))

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock'
    )

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_nav2, 'maps', 'test_map.yaml'),
        description='Full path to map YAML file'
    )

    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_nav2, 'config', 'nav2_params.yaml'),
        description='Full path to Nav2 parameters YAML file'
    )

    # Include Nav2 bringup launch
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map': map_yaml_file,
            'params_file': params_file,
            'autostart': 'true',
        }.items()
    )

    # Lifecycle manager is included in bringup_launch.py

    return LaunchDescription([
        declare_use_sim_time,
        declare_map,
        declare_params,
        nav2_bringup_launch,
    ])
