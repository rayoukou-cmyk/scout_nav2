#!/usr/bin/env python3
"""
Nav2 Goal Sender for Scout Mini Assignment
Sends 3 predefined goal poses and records navigation results.
Usage:
    ros2 run scout_mini_nav2 send_goals.py

Goals:
    1. (3.0, 0.0, 0.0)     - Straight ahead
    2. (3.0, 3.0, 1.57)    - Right side, facing north
    3. (-2.0, -2.0, -1.57) - Left rear, facing south
"""

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
import time
import json
from datetime import datetime

class GoalSender(Node):
    def __init__(self):
        super().__init__('scout_mini_goal_sender')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Predefined goals (x, y, yaw in radians)
        self.goals = [
            {'x': 3.0, 'y': 0.0, 'yaw': 0.0, 'description': 'Straight ahead - East corridor'},
            {'x': 3.0, 'y': 3.0, 'yaw': 1.5708, 'description': 'Northeast corner - facing North'},
            {'x': -2.0, 'y': -2.0, 'yaw': -1.5708, 'description': 'Southwest area - facing South'},
        ]

        self.results = []
        self.current_goal_idx = 0

    def send_goal(self, goal_idx):
        goal_data = self.goals[goal_idx]

        # Wait for action server
        self.get_logger().info(f"Waiting for Nav2 action server...")
        if not self._action_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error("Action server not available!")
            return False

        # Create goal message
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = goal_data['x']
        goal_msg.pose.pose.position.y = goal_data['y']
        goal_msg.pose.pose.position.z = 0.0

        # Convert yaw to quaternion
        yaw = goal_data['yaw']
        goal_msg.pose.pose.orientation.x = 0.0
        goal_msg.pose.pose.orientation.y = 0.0
        goal_msg.pose.pose.orientation.z = sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = cos(yaw / 2.0)

        self.get_logger().info(
            f"Sending Goal {goal_idx + 1}: ({goal_data['x']}, {goal_data['y']}, {goal_data['yaw']}) - {goal_data['description']}"
        )

        start_time = time.time()
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(lambda future: self.goal_response_callback(future, goal_idx, start_time))

        return True

    def goal_response_callback(self, future, goal_idx, start_time):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warning(f'Goal {goal_idx + 1} rejected')
            self.results.append({
                'goal': goal_idx + 1,
                'status': 'REJECTED',
                'duration': 0.0,
                'description': self.goals[goal_idx]['description']
            })
            self.next_goal()
            return

        self.get_logger().info(f'Goal {goal_idx + 1} accepted')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(lambda future: self.get_result_callback(future, goal_idx, start_time))

    def get_result_callback(self, future, goal_idx, start_time):
        result = future.result()
        duration = time.time() - start_time
        status = result.status

        status_str = {
            0: 'UNKNOWN',
            1: 'ACCEPTED',
            2: 'EXECUTING',
            3: 'CANCELING',
            4: 'SUCCEEDED',
            5: 'CANCELED',
            6: 'ABORTED'
        }.get(status, f'UNKNOWN({status})')

        self.get_logger().info(f'Goal {goal_idx + 1} result: {status_str} in {duration:.1f}s')

        self.results.append({
            'goal': goal_idx + 1,
            'status': status_str,
            'duration': round(duration, 2),
            'description': self.goals[goal_idx]['description'],
            'target': {
                'x': self.goals[goal_idx]['x'],
                'y': self.goals[goal_idx]['y'],
                'yaw': self.goals[goal_idx]['yaw']
            }
        })

        self.next_goal()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        # Optional: log distance remaining
        pass

    def next_goal(self):
        self.current_goal_idx += 1
        if self.current_goal_idx < len(self.goals):
            # Small delay between goals
            time.sleep(2.0)
            self.send_goal(self.current_goal_idx)
        else:
            self.save_results()
            self.get_logger().info("All goals completed! Shutting down...")
            rclpy.shutdown()

    def save_results(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'/tmp/scout_mini_nav2_results_{timestamp}.json'

        output = {
            'timestamp': timestamp,
            'total_goals': len(self.goals),
            'completed_goals': len(self.results),
            'success_rate': sum(1 for r in self.results if r['status'] == 'SUCCEEDED') / len(self.results),
            'results': self.results
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        self.get_logger().info(f"Results saved to: {filename}")

        # Also print summary to console
        print("\n" + "="*60)
        print("NAVIGATION RESULTS SUMMARY")
        print("="*60)
        for r in self.results:
            status_icon = "✓" if r['status'] == 'SUCCEEDED' else "✗"
            print(f"{status_icon} Goal {r['goal']}: {r['status']} ({r['duration']}s) - {r['description']}")
        print("="*60)
        print(f"Success Rate: {output['success_rate']*100:.0f}%")
        print("="*60 + "\n")

from math import sin, cos

def main(args=None):
    rclpy.init(args=args)
    sender = GoalSender()

    # Send first goal
    sender.send_goal(0)

    try:
        rclpy.spin(sender)
    except KeyboardInterrupt:
        sender.get_logger().info("Interrupted by user")
    finally:
        sender.destroy_node()

if __name__ == '__main__':
    main()
