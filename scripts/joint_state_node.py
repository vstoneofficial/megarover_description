#!/usr/bin/env python3
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

"""Run the installed joint publisher without interrupting import or teardown."""
import signal

requested = []


def stop(signum, _frame):
    requested.append(signum)


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


def main():
    import argparse
    import sys

    import rclpy
    from rclpy.signals import SignalHandlerOptions
    from joint_state_publisher.joint_state_publisher import JointStatePublisher

    if requested:
        return 0
    # A Python handler alone still interrupts native DDS socket initialization.
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
    try:
        if requested:
            return 0
        rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
        parser = argparse.ArgumentParser()
        parser.add_argument('description_file', nargs='?', default=None)
        args = parser.parse_args(rclpy.utilities.remove_ros_args(args=sys.argv)[1:])
        publisher = JointStatePublisher(args.description_file)
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    try:
        while not requested and rclpy.ok():
            rclpy.spin_once(publisher, timeout_sec=.1)
        return 0
    finally:
        publisher.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
