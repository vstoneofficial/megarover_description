cmake_minimum_required(VERSION 3.8)
project(megarover_description)

find_package(ament_cmake REQUIRED)
find_package(gz_sim_vendor REQUIRED)
find_package(gz_plugin_vendor REQUIRED)
find_package(gz_physics_vendor REQUIRED)
find_package(gz-sim8 REQUIRED)
find_package(gz-plugin2 REQUIRED COMPONENTS register)

add_library(megarover_support_friction SHARED src/support_friction.cpp)
target_compile_features(megarover_support_friction PUBLIC cxx_std_17)
target_link_libraries(megarover_support_friction PRIVATE gz-sim8::gz-sim8 gz-plugin2::register)
install(TARGETS megarover_support_friction LIBRARY DESTINATION lib)

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
  find_package(ament_cmake_copyright REQUIRED)
  # Check distributed source and LICENSE without requiring CONTRIBUTING.md.
  ament_copyright(LICENSE launch params src)
  list(APPEND AMENT_LINT_AUTO_EXCLUDE ament_cmake_copyright)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
