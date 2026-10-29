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

"""Run the installed joint GUI with orderly Qt, worker and ROS teardown."""
import signal

# Keep shutdown requests while the SDK imports and Qt initialization run.
# The SDK console entrypoint has no handler during import and later selects
# SIG_DFL; neither path performs the GUI's closeEvent / worker shutdown.
requested = []


def stop(signum, _frame):
    requested.append(signum)


signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)


def main():
    import argparse
    import sys
    import threading

    import rclpy
    from rclpy.signals import SignalHandlerOptions
    from joint_state_publisher.joint_state_publisher import JointStatePublisher
    from joint_state_publisher_gui.joint_state_publisher_gui import JointStatePublisherGui
    from python_qt_binding.QtCore import QTimer
    from python_qt_binding.QtWidgets import QApplication

    if requested:
        return 0
    # A Python handler alone still interrupts native DDS socket initialization.
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})
    try:
        if requested:
            return 0
        rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
        parser = argparse.ArgumentParser()
        parser.add_argument('urdf_file', nargs='?', default=None)
        args = parser.parse_args(rclpy.utilities.remove_ros_args(args=sys.argv)[1:])
        app = QApplication(sys.argv)
        publisher = JointStatePublisher(args.urdf_file)
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    window = JointStatePublisherGui('Joint State Publisher', publisher)
    worker = threading.Thread(target=window.loop)

    def check_stop():
        if requested:
            window.close()
            app.quit()

    timer = QTimer()
    timer.timeout.connect(check_stop)
    timer.start(100)
    window.show()
    worker.start()
    try:
        return app.exec() if hasattr(app, 'exec') else app.exec_()
    finally:
        window.running = False
        worker.join(timeout=2)
        if worker.is_alive():
            raise RuntimeError('Joint state GUI worker did not stop')
        publisher.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    raise SystemExit(main())
