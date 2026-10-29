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


from geometry_msgs.msg import Twist
import signal
import rclpy
from rclpy.signals import SignalHandlerOptions
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import Float64MultiArray


class RoverTwistRelay(Node):

    def __init__(self):
        super().__init__('rover_twist_relay')

        # ----------------------------
        # Parameters
        # ----------------------------
        self.publish_rate = self.declare_parameter('publish_rate', 30.0).value

        # rover selector
        self.rover = self.declare_parameter('rover', 'mega3').value

        # fallback geometry
        self.wheel_radius = self.declare_parameter('wheel_radius', 0.07).value
        self.wheel_separation = self.declare_parameter('wheel_separation', 0.272).value

        # per-rover parameters (fwdsrover-style)
        self.declare_parameter('mega3.wheel_radius', 0.07)
        self.declare_parameter('mega3.wheel_separation', 0.272)

        self.declare_parameter('mega3_outdoor.wheel_radius', 0.07)
        self.declare_parameter('mega3_outdoor.wheel_separation', 0.500)

        self.declare_parameter('f120a.wheel_radius', 0.085)
        self.declare_parameter('f120a.wheel_separation', 0.404)

        self.declare_parameter('s40a_lb.wheel_separation', 0.340)

        self.apply_rover_parameters()

        # ----------------------------
        # Topics
        # ----------------------------
        self.cmd_topic = self.declare_parameter(
            'cmd_topic', '/rover_twist'
        ).value

        self.wheel_cmd_topic = self.declare_parameter(
            'wheel_cmd_topic',
            '/wheel_velocity_controller/commands'
        ).value

        # ----------------------------
        # ROS interfaces
        # ----------------------------
        self.sub = self.create_subscription(
            Twist, self.cmd_topic, self.on_twist, 10
        )

        self.pub = self.create_publisher(
            Float64MultiArray, self.wheel_cmd_topic, 10
        )

        self.last_twist = Twist()

        self.timer = self.create_timer(
            1.0 / self.publish_rate, self.on_timer
        )

        self.get_logger().info(
            f'rover_twist_relay active: rover={self.rover}, '
            f'wheel_radius={self.wheel_radius}, '
            f'wheel_separation={self.wheel_separation}'
        )

    # ----------------------------
    def apply_rover_parameters(self):
        prefix = f'{self.rover}.'
        params = self._parameters

        def get_param(name, default):
            full = prefix + name
            if full in params:
                return params[full].value
            return default

        wr = get_param('wheel_radius', self.wheel_radius)
        ws = get_param('wheel_separation', self.wheel_separation)

        self.set_parameters([
            Parameter('wheel_radius', Parameter.Type.DOUBLE, wr),
            Parameter('wheel_separation', Parameter.Type.DOUBLE, ws),
        ])

        self.wheel_radius = wr
        self.wheel_separation = ws

    # ----------------------------
    def on_twist(self, msg: Twist):
        self.last_twist = msg

    # ----------------------------
    def on_timer(self):
        v = float(self.last_twist.linear.x)
        w = float(self.last_twist.angular.z)

        # Differential drive kinematics
        # v_l = v - (w * L / 2)
        # v_r = v + (w * L / 2)
        v_l = v - (w * self.wheel_separation * 0.5)
        v_r = v + (w * self.wheel_separation * 0.5)

        if self.wheel_radius > 0.0:
            w_l = v_l / self.wheel_radius
            w_r = v_r / self.wheel_radius
        else:
            w_l = 0.0
            w_r = 0.0

        msg = Float64MultiArray()
        # Joint order: [left, right]
        msg.data = [w_l, w_r]

        self.pub.publish(msg)


def main():
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = RoverTwistRelay()
    try:
        while not stopping and node.context.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
