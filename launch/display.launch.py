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

import os
import shlex
from pathlib import Path

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from rclpy.utilities import get_rmw_implementation_identifier


def generate_launch_description():

    # --------------------------------------------------
    # Package path
    # --------------------------------------------------
    desc_pkg = get_package_share_directory('megarover_description')
    rmw = get_rmw_implementation_identifier()
    rmw_library = Path(get_package_prefix(rmw)) / 'lib' / ('lib' + rmw + '.so')
    if not rmw_library.is_file():
        raise RuntimeError('RViz RMW library unavailable: ' + str(rmw_library))
    rviz_preload = str(rmw_library)
    if os.environ.get('LD_PRELOAD'):
        rviz_preload += ':' + os.environ['LD_PRELOAD']

    # --------------------------------------------------
    # Launch arguments
    # --------------------------------------------------
    rover = LaunchConfiguration('rover', default='mega3')
    gui = LaunchConfiguration('gui', default='true')

    # --------------------------------------------------
    # Select xacro and rviz by rover type
    # --------------------------------------------------
    model_file = PythonExpression([
        repr(shlex.quote(os.path.join(desc_pkg, 'urdf') + os.sep)), ' + (',
        '"mega3_outdoor.xacro" if "', rover, '" == "mega3_outdoor" else ',
        '"mega3.xacro" if "', rover, '" == "mega3" else ',
        '"s40a_lb.xacro" if "', rover, '" == "s40a_lb" else ',
        '"f120a.xacro")'
    ])

    rviz_file = PythonExpression([
        repr(os.path.join(desc_pkg, 'rviz') + os.sep), ' + (',
        '"mega3.rviz" if "', rover, '" in ("mega3", "mega3_outdoor") else ',
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
        package='megarover_description',
        executable='joint_state_node.py',
        prefix='setsid',
        condition=UnlessCondition(gui)
    )

    joint_state_publisher_gui = Node(
        package='megarover_description',
        executable='joint_state_gui.py',
        prefix='setsid',
        condition=IfCondition(gui)
    )

    rviz = Node(
        package='megarover_description',
        executable='gui_session.py',
        name='rviz2',
        prefix='setsid',
        additional_env={'LD_PRELOAD': rviz_preload},
        arguments=[
            os.path.join(
                get_package_prefix('megarover_description'),
                'lib/megarover_description/rviz_no_prompt'),
            '-d', rviz_file],
        output='screen'
    )

    # --------------------------------------------------
    # Launch description
    # --------------------------------------------------
    return LaunchDescription([

        DeclareLaunchArgument(
            'rover',
            default_value='mega3',
            description='Rover type: mega3 | mega3_outdoor | f120a | s40a_lb'
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
