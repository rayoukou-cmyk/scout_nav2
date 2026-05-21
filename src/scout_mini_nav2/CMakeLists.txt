cmake_minimum_required(VERSION 3.8)
project(scout_mini_nav2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  config
  launch
  maps
  rviz
  behavior_trees
  DESTINATION share/${PROJECT_NAME}/
)

install(PROGRAMS
  scripts/send_goals.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
