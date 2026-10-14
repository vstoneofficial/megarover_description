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

"""Check the standalone description launch, without creating command publishers."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.qos import DurabilityPolicy, qos_profile_sensor_data, QoSProfile
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from tf2_msgs.msg import TFMessage


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(source):
    assert not subprocess.check_output(
        ['git', '-C', str(source), 'status', '--porcelain'], text=True).strip(), source
    return {'path': str(source), 'clean': True, 'commit': subprocess.check_output(
        ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--helper-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rover', choices=['mega3', 'f120a', 's40a_lb'], default='mega3')
    parser.add_argument('--gui', choices=['true', 'false'], default='true')
    parser.add_argument('--mode', choices=['ready', 'early-sigint'], default='ready')
    args = parser.parse_args()
    assert os.environ.get('ROS_DOMAIN_ID') == '100'
    assert os.environ.get('DISPLAY') == ':1'
    sys.path.insert(0, str(args.helper_root / 'tools'))
    from verify_nonhardware_sequence import Case, capture, marked_processes, save

    share = Path(get_package_share_directory('megarover_description'))
    hashes = {}
    for directory in ('launch', 'urdf', 'params', 'rviz'):
        for path in sorted((share / directory).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                hashes[str(path)] = sha(path)
    for path in sorted((share.parent.parent / 'lib/megarover_description').glob('*')):
        if path.is_file():
            hashes[str(path)] = sha(path)
    launch = share / 'launch/display.launch.py'
    assert sha(launch) == sha(args.source / 'launch/display.launch.py')
    info = {'description': identity(args.source), 'helper': identity(args.helper_root),
            'fixture_sha256': sha(__file__), 'helper_sha256': sha(
                args.helper_root / 'tools/verify_nonhardware_sequence.py'),
            'installed_share': str(share), 'hashes': hashes,
            'target': 'Jazzy standalone model display / VNC :1 / domain100',
            'command_publishers_created': False, 'mode': args.mode}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = rclpy.create_node('description_qualification_' + str(os.getpid()))
    messages = {'description': None, 'joints': [], 'tf': {}, 'tf_static': {}}

    def description_cb(message):
        messages['description'] = message.data

    def tf_cb(message, key):
        for transform in message.transforms:
            messages[key][transform.child_frame_id] = {
                'parent': transform.header.frame_id,
                'xyz': [transform.transform.translation.x, transform.transform.translation.y,
                        transform.transform.translation.z],
                'xyzw': [transform.transform.rotation.x, transform.transform.rotation.y,
                         transform.transform.rotation.z, transform.transform.rotation.w]}

    transient = QoSProfile(depth=100, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    _subscriptions = [
        node.create_subscription(String, '/robot_description', description_cb, transient),
        node.create_subscription(
            JointState, '/joint_states',
            lambda m: messages['joints'].append({
                'names': list(m.name), 'position': list(m.position),
                'stamp': [m.header.stamp.sec, m.header.stamp.nanosec]}),
            qos_profile_sensor_data),
        node.create_subscription(
            TFMessage, '/tf', lambda m: tf_cb(m, 'tf'), qos_profile_sensor_data),
        node.create_subscription(
            TFMessage, '/tf_static', lambda m: tf_cb(m, 'tf_static'), transient),
    ]
    command = ['ros2', 'launch', 'megarover_description', 'display.launch.py',
               'rover:=' + args.rover, 'gui:=' + args.gui]
    case = Case(args.output.parent, args.output.name, command, identity=info)
    try:
        deadline = time.monotonic() + 20
        if args.mode == 'early-sigint':
            while time.monotonic() < deadline:
                processes = marked_processes(case.marker)
                rviz = [p for p in processes if '/rviz2/rviz2' in p['exe']
                        or p['exe'].endswith('/rviz_no_prompt')]
                if rviz:
                    case.result['rviz_before_early_stop'] = rviz
                    time.sleep(.15)
                    case.result['functional_pass'] = True
                    break
                time.sleep(.025)
            else:
                raise AssertionError('Owned RViz did not start before early SIGINT')
        else:
            expected = None
            while time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=.1)
                if messages['description']:
                    robot = ET.fromstring(messages['description'])
                    expected = {j.find('child').attrib['link'] for j in robot.findall('joint')}
                    available = set(messages['tf']) | set(messages['tf_static'])
                    if len(messages['joints']) >= 2 and expected <= available:
                        break
            else:
                raise AssertionError('Missing model/joint/TF data: ' + str({
                    'description': messages['description'] is not None,
                    'joint_samples': len(messages['joints']),
                    'missing_tf': sorted(
                        (expected or set()) - set(messages['tf']) - set(messages['tf_static']))}))
            models = [x.attrib['name'] for x in robot.findall('link')]
            resources = {}
            for mesh in robot.findall('.//mesh'):
                uri = mesh.attrib['filename']
                assert uri.startswith('package://'), uri
                package, rel = uri[len('package://'):].split('/', 1)
                path = Path(get_package_share_directory(package)) / rel
                assert path.is_file(), path
                resources[uri] = sha(path)
            end = time.monotonic() + 12
            while time.monotonic() < end:
                rclpy.spin_once(node, timeout_sec=.1)
            (case.root / 'robot_description.urdf').write_text(messages['description'])
            save(case.root / 'observations.json', {
                'rover': args.rover, 'gui': args.gui,
                'links': models, 'joint_samples': messages['joints'], 'tf': messages['tf'],
                'tf_static': messages['tf_static'], 'mesh_hashes': resources,
                'description_sha256': hashlib.sha256(
                    messages['description'].encode()).hexdigest()})
            case.result['desktop'] = capture(case.root / 'desktop.png')
            case.result['functional_pass'] = True
    except Exception:
        case.result['functional_exception'] = traceback.format_exc()
        print(case.result['functional_exception'], flush=True)
    finally:
        result = case.finish()
        result['identity_after'] = identity(args.source)
        result['installed_artifacts_unchanged'] = all(sha(p) == h for p, h in hashes.items())
        assert result['installed_artifacts_unchanged']
        save(case.root / 'result.json', result)
        for subscription in _subscriptions:
            node.destroy_subscription(subscription)
        node.destroy_node()
        rclpy.try_shutdown()
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
