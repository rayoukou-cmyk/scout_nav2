#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    pkg_gz_sim = get_package_share_directory('scout_mini_gz_sim')
    pkg_description = get_package_share_directory('scout_mini_description')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    world_name = LaunchConfiguration('world_name', default='test_world')
    headless = LaunchConfiguration('headless', default='false')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock'
    )

    declare_world = DeclareLaunchArgument(
        'world_name',
        default_value='test_world',
        description='World file name (without .sdf extension)'
    )

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Run Gazebo in headless mode (no GUI)'
    )

    # World file path
    world_file = os.path.join(pkg_gz_sim, 'worlds', PythonExpression(["'", world_name, "' + '.sdf'"]))

    # Start Ignition Gazebo (Fortress)
    # Note: On ARM64 UTM with software rendering, we use --render-engine ogre
    gazebo = ExecuteProcess(
        cmd=[
            'ign', 'gazebo',
            '-r',  # Run simulation
            '--render-engine', 'ogre',
            os.path.join(pkg_gz_sim, 'worlds', 'test_world.sdf')
        ],
        output='screen',
        condition=IfCondition(PythonExpression(['not ', headless]))
    )

    # Headless Gazebo (for CI/testing)
    gazebo_headless = ExecuteProcess(
        cmd=[
            'ign', 'gazebo',
            '-r',
            '-s',  # Server only (headless)
            os.path.join(pkg_gz_sim, 'worlds', 'test_world.sdf')
        ],
        output='screen',
        condition=IfCondition(headless)
    )

    # Robot State Publisher (publishes TF from URDF)
    urdf_path = os.path.join(pkg_description, 'urdf', 'scout_mini.xacro')
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': open(urdf_path).read()
        }]
    )

    # Spawn robot in Gazebo using ros_gz_sim create
    # We use a Python script to spawn after Gazebo is ready
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'scout_mini',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.5',
            '-Y', '0.0'
        ],
        output='screen'
    )

    # ROS-Gazebo Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # Clock
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            # Cmd Vel
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            # Odometry
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            # IMU
            '/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU',
            # Front LiDAR
            '/front_lidar_scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            # Rear LiDAR
            '/rear_lidar_scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            # Joint states (for wheel rotation visualization)
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
        ],
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # TF Broadcaster for odom -> base_link (Gazebo publishes this, but we ensure it)
    # Actually Gazebo diff-drive plugin publishes odom, we just need to bridge it

    return LaunchDescription([
        declare_use_sim_time,
        declare_world,
        declare_headless,
        gazebo,
        gazebo_headless,
        robot_state_publisher,
        spawn_robot,
        bridge,
    ])
