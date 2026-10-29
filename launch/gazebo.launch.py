"""Gazebo Harmonic bringup using native Jazzy model definitions."""
import os
import shlex
import subprocess
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, ExecuteLocal, ExecuteProcess, GroupAction,
    OpaqueFunction, RegisterEventHandler, SetLaunchConfiguration, Shutdown,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _gazebo_exited(event, context):
    if event.process_name.rsplit('-', 1)[0] != 'gazebo' or context.is_shutdown:
        return []
    return [Shutdown(reason='Gazebo exited')]


def _bind_gazebo_timeout(context, installed_action):
    actions = []
    for action in installed_action.execute(context):
        if isinstance(action, ExecuteProcess):
            # Preserve ros_gz_sim's executable, resource paths and shell settings.
            # A literal timeout survives the launch configuration scope popping.
            action = ExecuteLocal(
                process_description=action.process_description,
                shell=action.shell, output=action.output,
                emulate_tty=action.emulate_tty,
                sigterm_timeout='15.0', sigkill_timeout=action.sigkill_timeout,
            )
        actions.append(action)
    return actions


def _gazebo_group(context, gz_args):
    # Each CLI mode needs fresh entities: the source caches its actions.
    source = PythonLaunchDescriptionSource(os.path.join(
        get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py'))
    actions = [
        OpaqueFunction(function=_bind_gazebo_timeout, args=[action])
        if isinstance(action, OpaqueFunction) else action
        for action in source.get_launch_description(context).entities
    ]
    return GroupAction([
        SetLaunchConfiguration('launch-prefix', 'exec setsid'),
        SetLaunchConfiguration('gz_args', gz_args),
        SetLaunchConfiguration('on_exit_shutdown', 'false'),
        *actions,
    ])


def _setup(context):
    rover = LaunchConfiguration('rover').perform(context)
    gui = LaunchConfiguration('gui').perform(context).lower() == 'true'
    share = get_package_share_directory('megarover_description')
    description = subprocess.check_output([
        'xacro', os.path.join(get_package_share_directory('megarover_description'),
                              'urdf', rover + '.xacro')], text=True)
    model = ET.fromstring(description)
    server_args = '-r -s ' + ('' if gui else '--headless-rendering ')
    server_args += shlex.quote(os.path.join(share, 'worlds', 'empty.sdf'))
    gz_groups = [_gazebo_group(context, server_args)]
    if gui:
        gz_groups.append(_gazebo_group(context, '-g'))
    rsp = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        prefix='setsid',
        name='megarover_description_state_publisher',
        parameters=[{'robot_description': description, 'use_sim_time': True}], output='screen')
    spawn = Node(
        package='ros_gz_sim', executable='create',
        prefix='setsid',
        arguments=['-world', 'default', '-name', rover, '-topic', '/robot_description',
                   '-z', LaunchConfiguration('spawn_z')], output='screen')
    controllers = Node(
        package='controller_manager', executable='spawner',
        prefix='setsid',
        arguments=['joint_state_broadcaster', 'wheel_velocity_controller',
                   '--controller-manager-timeout', '120',
                   '--switch-timeout', '120', '--service-call-timeout', '120'], output='screen')
    bridge_arguments = [
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        '/sim_odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan']
    if model.find(".//sensor[@name='tg30_lidar_back']") is not None:
        bridge_arguments.append('/back_scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan')
    bridge_remappings = []
    point_bridges = {}
    for sensor in model.findall('.//sensor'):
        topic = sensor.findtext('topic')
        sensor_type = sensor.get('type')
        if not topic:
            continue
        if sensor_type in ('camera', 'rgbd_camera', 'depth_camera'):
            info = sensor.findtext('camera/camera_info_topic')
            if info:
                bridge_arguments.append(info + '@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo')
            if sensor_type == 'camera':
                bridge_arguments.append(topic + '@sensor_msgs/msg/Image[gz.msgs.Image')
            else:
                depth_topic = topic + '/depth_image' if sensor_type == 'rgbd_camera' else topic
                bridge_arguments.append(depth_topic + '@sensor_msgs/msg/Image[gz.msgs.Image')
                if sensor_type == 'rgbd_camera':
                    bridge_remappings.append((depth_topic, topic + '/image_raw'))
                    optical_frame = sensor.findtext('camera/optical_frame_id')
                    reference_frame = next(
                        item.get('reference') for item in model.findall('gazebo')
                        if sensor in item)
                    depth_frame = next(
                        (joint.find('parent').get('link') for joint in model.findall('joint')
                         if joint.find('child').get('link') == optical_frame), reference_frame)
                    # Native Gazebo points use the physical camera's X-forward axes.
                    key = 'depth_points_' + str(len(point_bridges))
                    point_bridges[key] = {
                        'ros_topic_name': topic + '/color/points',
                        'gz_topic_name': topic + '/points',
                        'ros_type_name': 'sensor_msgs/msg/PointCloud2',
                        'gz_type_name': 'gz.msgs.PointCloudPacked',
                        'direction': 'GZ_TO_ROS',
                        'frame_id': depth_frame,
                    }
        elif sensor_type == 'imu':
            bridge_arguments.append(topic + '@sensor_msgs/msg/Imu[gz.msgs.IMU')
    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge', prefix='setsid',
        arguments=bridge_arguments, remappings=bridge_remappings,
        parameters=[{'use_sim_time': True}], output='screen')
    point_nodes = []
    if point_bridges:
        # Parameter-defined bridges initialize when no CLI bridge already exists.
        point_nodes.append(Node(
            package='ros_gz_bridge', executable='parameter_bridge', prefix='setsid',
            name='megarover_depth_bridge',
            parameters=[{'bridge_names': list(point_bridges), 'bridges': point_bridges}],
            output='screen'))
    relay = Node(
        package='megarover_description', executable='rover_twist_relay.py',
        prefix='setsid',
        name='rover_twist_relay', output='screen', parameters=[os.path.join(
            get_package_share_directory('megarover_description'),
            'params', 'rover_twist_relay.yaml'),
            {'rover': rover, 'use_sim_time': True}])
    shutdown_handler = RegisterEventHandler(OnProcessExit(on_exit=_gazebo_exited))
    return [
        shutdown_handler, *gz_groups, rsp, spawn, controllers,
        bridge, *point_nodes, relay,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'rover', default_value='mega3', choices=['mega3', 'mega3_outdoor', 'f120a', 's40a_lb']),
        DeclareLaunchArgument('gui', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('spawn_z', default_value='0.03'),
        OpaqueFunction(function=_setup)])
