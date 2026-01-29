#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose

def yaw_to_quaternion(yaw: float):
  """Convert yaw (rad) to geometry_msgs/Quaternion."""
  half = yaw * 0.5
  cz = math.cos(half)
  sz = math.sin(half)
  q = {
    "x": 0.0,
    "y": 0.0,
    "z": sz,
    "w": cz,
  }
  return q

class Nav2Navigator(Node):
  """
  Simple wrapper to drive a robot using Nav2 NavigateToPose.
  """

  def __init__(self, node_name: str = "nav2_navigator"):
    super().__init__(node_name)

    self._action_client = ActionClient(
      self,
      NavigateToPose,
      "navigate_to_pose"
    )

    self._goal_handle = None
    self._send_in_progress = False

    self.get_logger().info("Nav2Navigator node started")

  def wait_for_server(self, timeout_sec: float = 10.0) -> bool:
    """
    Wait for Nav2 action server.
    """
    available = self._action_client.wait_for_server(timeout_sec=timeout_sec)
    if not available:
      self.get_logger().error("navigate_to_pose action server not available")
    else:
      self.get_logger().info("navigate_to_pose action server is available")
    return available

  def build_pose(self,
                 x: float,
                 y: float,
                 yaw: float,
                 frame_id: str = "map") -> PoseStamped:
    """
    Build a PoseStamped in the given frame.
    """
    pose = PoseStamped()
    pose.header.stamp = self.get_clock().now().to_msg()
    pose.header.frame_id = frame_id

    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0

    q = yaw_to_quaternion(yaw)
    pose.pose.orientation.x = q["x"]
    pose.pose.orientation.y = q["y"]
    pose.pose.orientation.z = q["z"]
    pose.pose.orientation.w = q["w"]

    return pose

  def go_to_pose(self,
                 x: float,
                 y: float,
                 yaw: float,
                 frame_id: str = "map",
                 wait: bool = True):
    """
    Send a navigation goal. Optionally block until result.
    """
    if self._send_in_progress:
      self.get_logger().warn("A goal is already in progress, cancel or wait")
      return None

    if not self._action_client.server_is_ready():
      self.get_logger().error("navigate_to_pose server not ready; call wait_for_server() first")
      return None

    goal_msg = NavigateToPose.Goal()
    goal_msg.pose = self.build_pose(x, y, yaw, frame_id)

    self.get_logger().info(
      f"Sending goal to x={x:.3f}, y={y:.3f}, yaw={yaw:.3f} rad in {frame_id}"
    )

    self._send_in_progress = True
    send_future = self._action_client.send_goal_async(
      goal_msg,
      feedback_callback=self._feedback_callback
    )
    send_future.add_done_callback(self._goal_response_callback)

    if not wait:
      return None

    # Spin until result when wait=True
    result_future_container = {"future": None}

    def _result_ready_cb(goal_handle_future):
      goal_handle = goal_handle_future.result()
      if not goal_handle.accepted:
        self.get_logger().error("Goal was rejected by server")
        self._send_in_progress = False
        return
      self._goal_handle = goal_handle
      result_future = goal_handle.get_result_async()
      result_future_container["future"] = result_future
      result_future.add_done_callback(self._result_callback)

    # Override callback so that we hook into result
    send_future.remove_done_callback(self._goal_response_callback)
    send_future.add_done_callback(_result_ready_cb)

    while rclpy.ok() and self._send_in_progress:
      rclpy.spin_once(self, timeout_sec=0.1)

    return getattr(self, "_last_result", None)

  def _goal_response_callback(self, future):
    goal_handle = future.result()
    if not goal_handle.accepted:
      self.get_logger().error("Goal rejected")
      self._send_in_progress = False
      return
    self.get_logger().info("Goal accepted")
    self._goal_handle = goal_handle

    result_future = goal_handle.get_result_async()
    result_future.add_done_callback(self._result_callback)

  def _feedback_callback(self, feedback_msg):
    feedback = feedback_msg.feedback

    # Nav2 feedback has current_pose, navigation_time, etc.
    self.get_logger().debug(
      f"Feedback: distance_remaining={feedback.distance_remaining:.3f}, "
      f"estimated_time_remaining={feedback.estimated_time_remaining.sec}s"
    )

  def _result_callback(self, future):
    result = future.result().result
    status = future.result().status
    self.get_logger().info(f"Result received with status={status}")
    self._last_result = result
    self._send_in_progress = False

  def cancel_current_goal(self):
    """
    Cancel the current navigation goal if any.
    """
    if self._goal_handle is None:
      self.get_logger().warn("No active goal to cancel")
      return

    cancel_future = self._goal_handle.cancel_goal_async()
    cancel_future.add_done_callback(self._cancel_done_callback)

  def _cancel_done_callback(self, future):
    cancel_response = future.result()
    if len(cancel_response.goals_canceling) > 0:
      self.get_logger().info("Successfully requested goal cancellation")
    else:
      self.get_logger().warn("Goal cancellation request was rejected")

def main():
  import argparse
  
  parser = argparse.ArgumentParser(
    description='Send navigation goal to robot via Nav2',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''
Examples:
  # Navigate to x=2.0, y=1.5, facing 90 degrees (1.57 rad)
  ros2 run neo_nav2_bringup nav2_navigator.py --x 2.0 --y 1.5 --yaw 1.57
  
  # Navigate to origin facing east
  ros2 run neo_nav2_bringup nav2_navigator.py --x 0.0 --y 0.0 --yaw 0.0
  
  # Use different frame
  ros2 run neo_nav2_bringup nav2_navigator.py --x 1.0 --y 1.0 --yaw 0.0 --frame odom
    '''
  )
  
  parser.add_argument('--x', type=float, default=1.0,
                      help='Target X coordinate in meters (default: 1.0)')
  parser.add_argument('--y', type=float, default=0.0,
                      help='Target Y coordinate in meters (default: 0.0)')
  parser.add_argument('--yaw', type=float, default=0.0,
                      help='Target yaw angle in radians (default: 0.0)')
  parser.add_argument('--frame', type=str, default='map',
                      help='Reference frame (default: map)')
  parser.add_argument('--no-wait', action='store_true',
                      help='Do not wait for goal completion (non-blocking mode)')
  
  args = parser.parse_args()
  
  rclpy.init()

  navigator = Nav2Navigator()

  if not navigator.wait_for_server(10.0):
    print("ERROR: Nav2 server not available. Is navigation running?")
    rclpy.shutdown()
    return

  # Send navigation goal with user-provided coordinates
  print(f"\n{'='*60}")
  print(f"  Navigation Goal")
  print(f"{'='*60}")
  print(f"  Target: ({args.x:.3f}, {args.y:.3f}) m")
  print(f"  Yaw: {args.yaw:.3f} rad ({args.yaw * 57.2958:.1f}°)")
  print(f"  Frame: {args.frame}")
  print(f"  Mode: {'Non-blocking' if args.no_wait else 'Blocking'}")
  print(f"{'='*60}\n")
  
  navigator.go_to_pose(
    x=args.x,
    y=args.y,
    yaw=args.yaw,
    frame_id=args.frame,
    wait=not args.no_wait
  )

  if not args.no_wait:
    print("\n✓ Navigation goal completed!")
  else:
    print("\n✓ Navigation goal sent (non-blocking mode)")

  navigator.destroy_node()
  rclpy.shutdown()

if __name__ == "__main__":
  main()
