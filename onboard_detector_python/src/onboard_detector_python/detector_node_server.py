#!/usr/bin/env python3
"""
detector_node_server.py
-----------------------
ROS node entry point for DynamicDetectorServer (Mac M1 Pro server-side).
Jetson으로부터 센서 데이터를 수신하여 고성능 연산을 수행합니다.
"""

import rospy
from onboard_detector_python.dynamic_detector_server import DynamicDetectorServer


def main():
    rospy.init_node("onboard_detector_server", anonymous=False)

    rospy.loginfo("=" * 60)
    rospy.loginfo("  Onboard Detector — SERVER MODE (Mac M1 Pro)")
    rospy.loginfo("  Starting heavy processing pipeline...")
    rospy.loginfo("=" * 60)

    server = DynamicDetectorServer()

    rospy.loginfo("[Server] Node ready. Waiting for sensor data...")
    rospy.spin()


if __name__ == "__main__":
    main()
