#!/usr/bin/env python3
"""
dynamic_detector_client.py
--------------------------
Jetson(Robot)에서 실행되는 클라이언트 노드.
YOLO 추론은 수행하지만, 무거운 연산(DBSCAN, KF 등)은 Mac 서버에 맡기고 결과만 수신합니다.
"""

import threading
import numpy as np
import rospy
from vision_msgs.msg import Detection2DArray
from visualization_msgs.msg import MarkerArray
from sensor_msgs.msg import Image, PointCloud2

# 기존 DynamicDetector 상속 (파라미터 로딩 및 기본적인 설정 유지)
from onboard_detector_python.dynamic_detector import DynamicDetector

class DynamicDetectorClient(DynamicDetector):
    def __init__(self):
        super().__init__()
        rospy.loginfo(f"{self.HINT}: Running in CLIENT mode (Delegating heavy tasks to Server)")

    def _register_callback(self):
        """
        기존 콜백을 재정의하여 필요한 데이터만 구독하고 
        무거운 연산(Timer 기반)은 주석 처리합니다.
        """
        # 1. 센서 데이터 발행은 그대로 유지 (서버가 이를 구독하게 됨)
        # depth_sub, lidar_sub 등은 부모 클래스에서 처리됨.
        
        # 2. YOLO 결과 발행 및 센서 동기화 로직은 그대로 유지 (서버로 데이터 전달용)
        super()._register_callback()

        # 3. [추가] 서버에서 처리된 최종 결과를 받는 구독자 등록
        rospy.Subscriber("onboard_detector/server_processed_obstacles", MarkerArray, self._server_result_cb)

    def _server_result_cb(self, msg):
        """서버에서 계산된 장애물 정보를 수신하여 로컬 변수에 업데이트"""
        # MarkerArray를 다시 Box3D 객체 리스트로 역직렬화하는 과정이 필요할 수 있습니다.
        # 여기서는 예시로 로깅만 남기고, 실제로는 self.dynamic_bboxes를 업데이트합니다.
        # rospy.logdebug("Received processed obstacles from Server")
        pass

    # ------------------------------------------------------------------
    # 무거운 연산 타이머 콜백들 - 주석 처리 (서버에서 수행)
    # ------------------------------------------------------------------
    def _detection_cb(self, event):
        """기존: DBSCAN + UV Detector 연산 -> 주석 처리 (서버에서 수행)"""
        # self._run_server_check() # 서버 연결 상태 체크 등으로 대체 가능
        pass

    def _lidar_detection_cb(self, event):
        """기존: LiDAR Clustering 연산 -> 주석 처리 (서버에서 수행)"""
        pass

    def _tracking_cb(self, event):
        """기존: Kalman Filter Tracking 연산 -> 주석 처리 (서버에서 수행)"""
        pass

    def _classification_cb(self, event):
        """기존: Dynamic/Static Classification -> 주석 처리 (서버에서 수행)"""
        pass

    # 시각화(_vis_cb)는 로컬(Jetson)에서 디버깅이 필요할 경우 유지하거나, 
    # 서버에서 보낸 결과만 그리도록 수정 가능합니다.
