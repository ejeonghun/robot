#!/usr/bin/env python3
import rospy
from onboard_detector_python.dynamic_detector import DynamicDetector


class DynamicDetectorClient(DynamicDetector):
    """Jetson(Robot)에서 실행. 무거운 연산은 서버에 위임.

    서버(DynamicDetectorServer)가 같은 ROS 네트워크에서 센서 토픽을 구독하여
    DBSCAN/KF/분류를 수행하고, 표준 토픽(/onboard_detector/dynamic_bboxes 등)에
    결과를 발행합니다. 클라이언트는 해당 콜백을 비활성화하여 이중 처리를 방지합니다.
    """

    def __init__(self):
        super().__init__()
        rospy.loginfo(
            f"{self.HINT}: Running in CLIENT mode (heavy processing delegated to server)"
        )

    def _detection_cb(self, event):
        pass

    def _lidar_detection_cb(self, event):
        pass

    def _tracking_cb(self, event):
        pass

    def _classification_cb(self, event):
        pass

    def _vis_cb(self, event):
        pass
