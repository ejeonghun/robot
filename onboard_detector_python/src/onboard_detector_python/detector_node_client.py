#!/usr/bin/env python3
import rospy
from onboard_detector_python.dynamic_detector_client import DynamicDetectorClient


def main():
    rospy.init_node("onboard_detector_client", anonymous=False)
    client = DynamicDetectorClient()
    rospy.loginfo("[Client] Node ready. Heavy processing delegated to server.")
    rospy.spin()


if __name__ == "__main__":
    main()
