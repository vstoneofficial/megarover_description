cmake_minimum_required(VERSION 3.8)
project(megarover_description)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rviz_common REQUIRED)
find_package(Qt5 REQUIRED COMPONENTS Widgets)
find_package(OpenGL REQUIRED)

add_executable(rviz_no_prompt src/rviz_no_prompt.cpp)
ament_target_dependencies(rviz_no_prompt rclcpp rviz_common)
target_link_libraries(rviz_no_prompt Qt5::Widgets OpenGL::GL OpenGL::GLX)
install(TARGETS rviz_no_prompt DESTINATION lib/${PROJECT_NAME})

install(
  PROGRAMS
    ${CMAKE_CURRENT_SOURCE_DIR}/params/rover_twist_relay.py
    ${CMAKE_CURRENT_SOURCE_DIR}/scripts/joint_state_gui.py
    ${CMAKE_CURRENT_SOURCE_DIR}/scripts/joint_state_node.py
    ${CMAKE_CURRENT_SOURCE_DIR}/scripts/gui_session.py
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
