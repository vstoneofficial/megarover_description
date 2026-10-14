cmake_minimum_required(VERSION 3.8)
project(megarover_description)

find_package(ament_cmake REQUIRED)

install(
  PROGRAMS
    ${CMAKE_CURRENT_SOURCE_DIR}/params/rover_twist_relay.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch meshes rviz urdf params
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
