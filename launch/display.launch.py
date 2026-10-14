# Copyright 2026 YOSHIDA-V (ROS 2 Jazzy modifications)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    # --------------------------------------------------
    # Package path
    # --------------------------------------------------
    desc_pkg = get_package_share_directory('megarover_description')

    # --------------------------------------------------
    # Launch arguments
    # --------------------------------------------------
    rover = LaunchConfiguration('rover', default='mega3')
    gui = LaunchConfiguration('gui', default='true')

    # --------------------------------------------------
    # Select xacro and rviz by rover type
    # --------------------------------------------------
    model_file = PythonExpression([
        '"', desc_pkg, '/urdf/" + (',
        '"mega3.xacro" if "', rover, '" == "mega3" else ',
        '"s40a_lb.xacro" if "', rover, '" == "s40a_lb" else ',
        '"f120a.xacro")'
    ])

    rviz_file = PythonExpression([
        '"', desc_pkg, '/rviz/" + (',
        '"mega3.rviz" if "', rover, '" == "mega3" else ',
        '"s40a_lb.rviz" if "', rover, '" == "s40a_lb" else ',
        '"f120a.rviz")'
    ])

    # --------------------------------------------------
    # Robot description
    # --------------------------------------------------
    robot_description = ParameterValue(
        Command(['xacro ', model_file, ' use_ros2_control:=false']),
        value_type=str
    )

    # --------------------------------------------------
    # Nodes
    # --------------------------------------------------
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description
        }]
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        condition=UnlessCondition(gui)
    )

    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        condition=IfCondition(gui)
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_file],
        output='screen'
    )

    # --------------------------------------------------
    # Launch description
    # --------------------------------------------------
    return LaunchDescription([

        DeclareLaunchArgument(
            'rover',
            default_value='mega3',
            description='Rover type: mega3 | f120a | s40a_lb'
        ),

        DeclareLaunchArgument(
            'gui',
            default_value='true',
            description='Use joint_state_publisher_gui'
        ),

        robot_state_publisher,
        joint_state_publisher,
        joint_state_publisher_gui,
        rviz,
    ])
