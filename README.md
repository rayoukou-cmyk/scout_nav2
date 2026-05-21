# Scout Mini Dual RS-AIRY LiDAR Navigation (ROS2 Humble + Ignition Fortress)

**Target Platform**: ARM64 (Apple Silicon M4 via UTM) + Ubuntu 22.04 Jammy  
**Simulator**: Ignition Gazebo Fortress (not Gazebo Classic, due to China network/ARM64 constraints)  
**ROS2 Distro**: Humble Hawksbill  
**Navigation**: Nav2 with dual front/rear LiDARs

---

## 1. Project Structure

```
scout_mini_nav2/
├── docker/
│   ├── Dockerfile              # ARM64 Ubuntu 22.04 + ROS2 Humble + Ignition Fortress
│   ├── docker-compose.yml      # GUI forwarding + host networking
│   └── run_container.sh        # One-click container startup
└── src/
    ├── scout_mini_description/   # URDF/Xacro with dual LiDARs
    │   ├── urdf/scout_mini.xacro
    │   └── launch/display.launch.py
    ├── scout_mini_gz_sim/        # Ignition Fortress simulation
    │   ├── launch/sim.launch.py
    │   ├── launch/teleop.launch.py
    │   ├── worlds/test_world.sdf
    │   └── config/ros_gz_bridge.yaml
    └── scout_mini_nav2/          # Nav2 configuration & navigation
        ├── config/
        │   ├── nav2_params.yaml
        │   └── slam_toolbox.yaml
        ├── launch/
        │   ├── bringup.launch.py   # Complete system bringup
        │   ├── nav2.launch.py
        │   └── slam.launch.py
        ├── maps/
        │   ├── test_map.pgm
        │   └── test_map.yaml
        ├── rviz/nav2.rviz
        └── scripts/send_goals.py   # Automated 3-goal test
```

---

## 2. Prerequisites

### Host System (macOS + UTM)
- **UTM** configured with Ubuntu 22.04 Server ARM64
- **Docker Desktop** installed on macOS (or Docker Engine inside VM)
- **XQuartz** installed for GUI forwarding (optional, RViz2/Gazebo GUI)
- At least **8GB RAM** allocated to VM

### China Network Considerations
The Dockerfile uses **Tsinghua University mirrors** for:
- `apt` sources (ports.ubuntu.com → mirrors.tuna.tsinghua.edu.cn)
- ROS2 apt repository (packages.ros.org → mirrors.tuna.tsinghua.edu.cn)
- PyPI (pypi.org → pypi.tuna.tsinghua.edu.cn)

**Note**: Ignition Fortress packages are from OSRF (packages.osrfoundation.org). If this is blocked in your region, you may need to:
1. Use a VPN during Docker build, OR
2. Build Ignition from source (very slow on ARM64), OR
3. Download `.deb` packages manually from a mirror

---

## 3. Quick Start

### Step 1: Build Docker Image

```bash
cd scout_mini_nav2/docker
./run_container.sh
```

Or manually:
```bash
cd scout_mini_nav2
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d
```

### Step 2: Enter Container & Build Workspace

```bash
docker exec -it scout_mini_nav2 bash
cd ~/scout_ws

# Copy/clone your source code into src/
# (If using bind mount, it's already at /home/ros/scout_ws/src/scout_mini_nav2)

# Install dependencies
rosdep install --from-paths src --ignore-src -r -y

# Build
colcon build --symlink-install
source install/setup.bash
```

### Step 3: Launch Simulation

**Option A: Full system (Gazebo + Nav2 + RViz2)**
```bash
ros2 launch scout_mini_nav2 bringup.launch.py
```

**Option B: Simulation only (for testing teleop)**
```bash
# Terminal 1: Gazebo
ros2 launch scout_mini_gz_sim sim.launch.py

# Terminal 2: Teleop
ros2 launch scout_mini_gz_sim teleop.launch.py
```

**Option C: SLAM mode (create your own map)**
```bash
# Terminal 1: Simulation
ros2 launch scout_mini_gz_sim sim.launch.py

# Terminal 2: SLAM Toolbox
ros2 launch scout_mini_nav2 slam.launch.py

# Terminal 3: Teleop to drive around
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Terminal 4: Save map
ros2 run nav2_map_server map_saver_cli -f ~/scout_ws/src/scout_mini_nav2/maps/my_map
```

---

## 4. Nav2 Goal Testing

### Manual Goal via RViz2
1. Launch full system: `ros2 launch scout_mini_nav2 bringup.launch.py`
2. In RViz2, click **"2D Goal Pose"** button
3. Click on map to set goal position and orientation
4. Watch robot navigate while avoiding obstacles

### Automated 3-Goal Test
```bash
# After bringup.launch.py is running
ros2 run scout_mini_nav2 send_goals.py
```

This sends 3 goals automatically:
1. **(3.0, 0.0, 0.0)** — Straight ahead (East corridor)
2. **(3.0, 3.0, 1.57)** — Northeast corner, facing North
3. **(-2.0, -2.0, -1.57)** — Southwest area, facing South

Results are saved to `/tmp/scout_mini_nav2_results_*.json`.

---

## 5. TF Tree Verification

```bash
# View TF tree
ros2 run tf2_tools view_frames

# Expected frames:
# map → odom → base_link
#              ├── front_lidar_link
#              ├── rear_lidar_link
#              ├── front_left_wheel_link
#              ├── front_right_wheel_link
#              ├── rear_left_wheel_link
#              └── rear_right_wheel_link

# Check specific transforms
ros2 tf2_echo base_link front_lidar_link
ros2 tf2_echo base_link rear_lidar_link
```

---

## 6. Topic Verification

```bash
# List all topics
ros2 topic list

# Expected key topics:
# /front_lidar_scan      (sensor_msgs/LaserScan)
# /rear_lidar_scan       (sensor_msgs/LaserScan)
# /odom                  (nav_msgs/Odometry)
# /cmd_vel               (geometry_msgs/Twist)
# /imu                   (sensor_msgs/Imu)
# /map                   (nav_msgs/OccupancyGrid)
# /plan                  (nav_msgs/Path)
# /local_plan            (nav_msgs/Path)
# /particlecloud         (geometry_msgs/PoseArray)
# /goal_pose             (geometry_msgs/PoseStamped)

# Check publication rates
ros2 topic hz /front_lidar_scan
ros2 topic hz /rear_lidar_scan
ros2 topic hz /odom

# Echo data
ros2 topic echo /front_lidar_scan --once
```

---

## 7. Known Issues & Workarounds

### Issue 1: Gazebo GUI Black Screen on UTM
**Cause**: UTM on macOS lacks GPU passthrough; OpenGL software rendering may fail.  
**Fix**: Run headless mode and use RViz2 on host:
```bash
ros2 launch scout_mini_nav2 bringup.launch.py headless:=true
```

### Issue 2: `rosdep update` fails in China
**Fix**: Use ghproxy for GitHub raw files:
```bash
sudo sed -i 's|raw.githubusercontent.com|ghproxy.com/https://raw.githubusercontent.com|g' /etc/ros/rosdep/sources.list.d/*.list
rosdep update
```

### Issue 3: Ignition Fortress Installation Fails
**Fix A**: Use VPN during Docker build.  
**Fix B**: Install from pre-downloaded debs:
```bash
cd /tmp
wget https://packages.osrfoundation.org/gazebo/ubuntu-stable/pool/main/i/ignition-fortress/ignition-fortress_1.0.3-2~jammy_arm64.deb
dpkg -i ignition-fortress_*.deb || apt-get install -f
```

### Issue 4: Scout ROS2 Mesh Path Bug
The original `agilexrobotics/scout_ros2` has a known mesh path bug (Issue #17).  
**Fix**: This project uses a custom simplified URDF with primitive geometries instead of external mesh files, avoiding the path issue entirely.

---

## 8. Real Robot Deployment Notes (Japan)

When deploying on the physical Scout Mini:

### Hardware Interface Changes
| Simulation | Real Robot |
|-----------|-----------|
| `ignition-gazebo-diff-drive-system` | `scout_base` node (CAN bus) |
| `gpu_lidar` (simulated) | `rslidar_sdk` (RoboSense driver) |
| `/front_lidar_scan` (Ignition) | `/front/rslidar_points` (point cloud) |
| `/rear_lidar_scan` (Ignition) | `/back/rslidar_points` (point cloud) |

### CAN Setup
```bash
# Bring up CAN interface
sudo ip link set can0 up type can bitrate 500000
# Verify with
candump can0
```

### LiDAR Ethernet Setup
```bash
# Set static IP for LiDAR network
sudo ip addr add 192.168.1.100/24 dev eth0
# Front LiDAR: 192.168.1.200
# Rear LiDAR: 192.168.1.201
```

### Safety Checklist (Pre-flight)
- [ ] Emergency stop tested
- [ ] Low-speed test (< 0.3 m/s) in obstacle-free area
- [ ] LiDAR data verified in RViz2
- [ ] CAN communication verified (`ros2 topic echo /scout/status`)
- [ ] Nav2 costmap shows correct obstacle avoidance
- [ ] Battery > 50%

---

## 9. Assignment Deliverables Checklist

| Requirement | Status | Location |
|------------|--------|----------|
| Dockerfile | ✅ | `docker/Dockerfile` |
| docker-compose / run script | ✅ | `docker/` |
| Buildable workspace | ✅ | Full `src/` tree |
| Scout Mini URDF | ✅ | `scout_mini_description/urdf/` |
| Dual LiDAR TF frames | ✅ | `front_lidar_link`, `rear_lidar_link` |
| Dual LiDAR topics | ✅ | `/front_lidar_scan`, `/rear_lidar_scan` |
| Gazebo world | ✅ | `scout_mini_gz_sim/worlds/test_world.sdf` |
| Static map | ✅ | `scout_mini_nav2/maps/test_map.*` |
| Nav2 parameters | ✅ | `scout_mini_nav2/config/nav2_params.yaml` |
| Nav2 launch files | ✅ | `scout_mini_nav2/launch/` |
| RViz2 config | ✅ | `scout_mini_nav2/rviz/nav2.rviz` |
| Goal sender script | ✅ | `scout_mini_nav2/scripts/send_goals.py` |
| SLAM support | ✅ | `scout_mini_nav2/launch/slam.launch.py` |
| Teleop launch | ✅ | `scout_mini_gz_sim/launch/teleop.launch.py` |

---

## 10. License

MIT License - For academic assignment use.

## 11. References

- [agilexrobotics/scout_ros2](https://github.com/agilexrobotics/scout_ros2)
- [BRN-Hub/scout_lidar](https://github.com/BRN-Hub/scout_lidar)
- [Nav2 Documentation](https://navigation.ros.org/)
- [Ignition Fortress Documentation](https://gazebosim.org/docs/fortress)
