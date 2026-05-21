# scout_mini_nav2/Dockerfile
# ARM64 Ubuntu 22.04 + ROS2 Humble + Ignition Fortress
# Optimized for China network (Tsinghua/USTC mirrors)

FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

SHELL ["/bin/bash", "-c"]

# 1. Replace apt sources with Tsinghua mirror (China)
RUN sed -i 's|http://ports.ubuntu.com/ubuntu-ports|https://mirrors.tuna.tsinghua.edu.cn/ubuntu-ports|g' /etc/apt/sources.list && \
    sed -i 's|http://archive.ubuntu.com/ubuntu|https://mirrors.tuna.tsinghua.edu.cn/ubuntu|g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
        locales \
        curl \
        gnupg2 \
        lsb-release \
        software-properties-common \
        git \
        wget \
        build-essential \
        python3-pip \
        python3-rosdep \
        python3-colcon-common-extensions \
        python3-vcstool \
        ros-dev-tools \
        nano \
        vim \
        iputils-ping \
        net-tools \
        mesa-utils \
        libgl1-mesa-glx \
        libgl1-mesa-dri \
        && rm -rf /var/lib/apt/lists/*

# 2. Locale setup
RUN locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8

# 3. Add ROS2 Humble apt source (Tsinghua mirror)
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2.list && \
    apt-get update && \
    apt-get install -y ros-humble-desktop ros-humble-ros-base ros-dev-tools && \
    rm -rf /var/lib/apt/lists/*

# 4. Add Ignition Fortress (Gazebo) apt source (OSRF - may need VPN in China, but Fortress has arm64 binaries)
RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" > /etc/apt/sources.list.d/gazebo-stable.list && \
    apt-get update && \
    apt-get install -y ignition-fortress && \
    rm -rf /var/lib/apt/lists/*

# 5. Install ROS-Gazebo bridge and Nav2 packages
RUN apt-get update && apt-get install -y \
    ros-humble-ros-gz \
    ros-humble-ros-gz-sim \
    ros-humble-ros-gz-bridge \
    ros-humble-nav2-bringup \
    ros-humble-nav2-simple-commander \
    ros-humble-slam-toolbox \
    ros-humble-teleop-twist-keyboard \
    ros-humble-joint-state-publisher-gui \
    ros-humble-xacro \
    ros-humble-robot-state-publisher \
    ros-humble-tf2-tools \
    ros-humble-rviz2 \
    ros-humble-twist-mux \
    && rm -rf /var/lib/apt/lists/*

# 6. pip China mirror
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install -U \
        setuptools \
        argcomplete \
        transforms3d

# 7. Initialize rosdep (China users may need to use ghproxy for github raw files)
RUN rosdep init || true && \
    rosdep update --rosdistro humble || true

# 8. Create user
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    usermod -aG sudo,adm,plugdev,video,audio $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 9. Setup bashrc
RUN echo "source /opt/ros/humble/setup.bash" >> /home/$USERNAME/.bashrc && \
    echo "export ROS_DOMAIN_ID=0" >> /home/$USERNAME/.bashrc && \
    echo "export RMW_IMPLEMENTATION=rmw_fastrtps_cpp" >> /home/$USERNAME/.bashrc && \
    echo "export GZ_SIM_RESOURCE_PATH=/home/$USERNAME/scout_ws/install/share:/home/$USERNAME/scout_ws/src" >> /home/$USERNAME/.bashrc

# 10. Setup workspace
RUN mkdir -p /home/$USERNAME/scout_ws/src && \
    chown -R $USERNAME:$USERNAME /home/$USERNAME/scout_ws

WORKDIR /home/$USERNAME/scout_ws
USER $USERNAME

CMD ["/bin/bash"]
