#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    pkg_nav2 = get_package_share_directory('scout_mini_nav2')
    pkg_gz_sim = get_package_share_directory('scout_mini_gz_sim')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_nav2 = LaunchConfiguration('use_nav2', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    headless = LaunchConfiguration('headless', default='false')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock'
    )

    declare_use_nav2 = DeclareLaunchArgument(
        'use_nav2',
        default_value='true',
        description='Launch Nav2 navigation stack'
    )

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch RViz2'
    )

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Run Gazebo in headless mode'
    )

    # Gazebo Simulation
    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gz_sim, 'launch', 'sim.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'headless': headless,
        }.items()
    )

    # Nav2
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2, 'launch', 'nav2.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
        }.items(),
        condition=IfCondition(use_nav2)
    )

    # RViz2 with saved config
    rviz_config_file = os.path.join(pkg_nav2, 'rviz', 'nav2.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz)
    )

    # Initial pose publisher (for AMCL)
    initial_pose_cmd = Node(
        package='nav2_util',
        executable='lifecycle_bringup',
        name='amcl_lifecycle',
        arguments=['amcl'],
        condition=IfCondition(use_nav2)
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_nav2,
        declare_use_rviz,
        declare_headless,
        gz_sim_launch,
        nav2_launch,
        rviz_node,
        initial_pose_cmd,
    ])
