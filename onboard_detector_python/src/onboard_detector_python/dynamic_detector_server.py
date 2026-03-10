#!/usr/bin/env python3
"""
dynamic_detector_server.py
--------------------------
Mac M1 Pro(Server)에서 실행되는 연산 전용 서버 노드.
Jetson으로부터 데이터를 받아 DBSCAN, KF, Fusion 연산을 수행하고 결과를 전송합니다.

[기능]
- 실시간 구조화 로그 시스템 (파이프라인 단계별 latency 측정)
- 데이터 수신 타임아웃 감지 및 경고
- 처리 결과 MarkerArray 패키징 및 로봇 전송
- M1 Pro 성능 모니터링 대시보드 로그
"""

import threading
import time
from collections import deque
from copy import deepcopy

import numpy as np
import rospy
from std_msgs.msg import Float64, Header
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point

from onboard_detector_python.dynamic_detector import DynamicDetector
from onboard_detector_python.utils import Box3D


# ──────────────────────────────────────────────────────────────
# Structured Logger for Real-Time Pipeline Monitoring
# ──────────────────────────────────────────────────────────────


class PipelineLogger:
    """실시간 파이프라인 성능 모니터링 로거.

    각 처리 단계의 latency를 측정하고, 이동 평균/최대값을 추적하며,
    주기적으로 구조화된 요약 로그를 출력합니다.
    """

    WINDOW = 100  # 이동 평균 윈도우 크기

    def __init__(self):
        self._stats = {}  # stage_name → deque[float_ms]
        self._lock = threading.Lock()
        self._log_interval = 5.0  # 초
        self._last_log_time = time.time()
        self._total_cycles = 0

    def record(self, stage: str, elapsed_ms: float):
        """단계별 latency 기록."""
        with self._lock:
            if stage not in self._stats:
                self._stats[stage] = deque(maxlen=self.WINDOW)
            self._stats[stage].append(elapsed_ms)

    def increment_cycle(self):
        """전체 처리 사이클 카운터 증가."""
        self._total_cycles += 1

    def should_log(self) -> bool:
        now = time.time()
        if now - self._last_log_time >= self._log_interval:
            self._last_log_time = now
            return True
        return False

    def format_summary(self) -> str:
        """구조화된 성능 요약 문자열 생성."""
        with self._lock:
            if not self._stats:
                return ""

            lines = []
            lines.append("")
            lines.append(
                "╔══════════════════════════════════════════════════════════════╗"
            )
            lines.append(
                "║           M1 Pro Server — Pipeline Performance              ║"
            )
            lines.append(
                "╠══════════════════════════════════════════════════════════════╣"
            )
            lines.append(
                "║  Stage                     │  Avg(ms) │  Max(ms) │ Count    ║"
            )
            lines.append(
                "╟────────────────────────────┼──────────┼──────────┼──────────╢"
            )

            for stage in sorted(self._stats.keys()):
                vals = list(self._stats[stage])
                if not vals:
                    continue
                avg = sum(vals) / len(vals)
                mx = max(vals)
                cnt = len(vals)
                name = stage[:27].ljust(27)
                lines.append(f"║  {name}│ {avg:7.2f}  │ {mx:7.2f}  │ {cnt:7d}  ║")

            lines.append(
                "╠══════════════════════════════════════════════════════════════╣"
            )
            lines.append(f"║  Total cycles processed: {self._total_cycles:<34d}║")
            lines.append(
                "╚══════════════════════════════════════════════════════════════╝"
            )
            return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Data Timeout Monitor
# ──────────────────────────────────────────────────────────────


class DataTimeoutMonitor:
    """센서 데이터 수신 타임아웃 모니터.

    각 데이터 소스별 마지막 수신 시각을 추적하고,
    timeout 초과 시 경고 로그를 발행합니다.
    """

    def __init__(self, timeout_sec: float = 0.2):
        self._timeout = timeout_sec
        self._last_recv = {}  # source_name → time.time()
        self._warned = {}  # source_name → bool (중복 경고 방지)
        self._lock = threading.Lock()

    def touch(self, source: str):
        """데이터 수신 시 호출."""
        with self._lock:
            self._last_recv[source] = time.time()
            if self._warned.get(source, False):
                rospy.loginfo(f"[M1 Server] ✓ {source} data resumed")
                self._warned[source] = False

    def check_all(self):
        """모든 소스의 타임아웃 검사. Timer 콜백에서 주기적으로 호출."""
        now = time.time()
        with self._lock:
            for source, last in self._last_recv.items():
                elapsed = now - last
                if elapsed > self._timeout and not self._warned.get(source, False):
                    rospy.logwarn(
                        f"[M1 Server] ⚠ {source} data timeout "
                        f"({elapsed:.3f}s > {self._timeout:.3f}s threshold)"
                    )
                    self._warned[source] = True


# ──────────────────────────────────────────────────────────────
# DynamicDetectorServer
# ──────────────────────────────────────────────────────────────


class DynamicDetectorServer(DynamicDetector):
    """Mac M1 Pro 서버용 고성능 연산 노드.

    DynamicDetector를 상속하여 모든 센서 데이터를 수신하고,
    DBSCAN 클러스터링, Kalman Filter 추적, Dynamic/Static 분류를 수행합니다.

    [추가 기능]
    - 파이프라인 단계별 latency 실시간 로그
    - 데이터 수신 타임아웃 감지
    - 처리 결과 MarkerArray 로봇 전송
    - 성능 통계 Float64 발행
    """

    def __init__(self):
        # 로거 & 모니터 (부모 __init__ 전에 초기화해야 콜백에서 사용 가능)
        self._pipeline_logger = PipelineLogger()
        self._timeout_monitor = DataTimeoutMonitor(timeout_sec=0.2)
        self._server_start_time = time.time()

        # 부모 클래스 초기화 (파라미터 로딩 + 콜백 등록)
        super().__init__()

        rospy.loginfo(f"{self.HINT}: ════════════════════════════════════════")
        rospy.loginfo(f"{self.HINT}: Running in SERVER mode (M1 Pro)")
        rospy.loginfo(f"{self.HINT}: Heavy processing: DBSCAN + KF + MOT")
        rospy.loginfo(f"{self.HINT}: ════════════════════════════════════════")

        # ── 추가 퍼블리셔 ──
        # 최종 장애물 결과 → 로봇
        self._pub_server_result = rospy.Publisher(
            "onboard_detector/server_processed_obstacles", MarkerArray, queue_size=10
        )

        # 파이프라인 latency 발행 (모니터링용)
        self._pub_detection_latency = rospy.Publisher(
            "onboard_detector/server_detection_latency_ms", Float64, queue_size=10
        )
        self._pub_tracking_latency = rospy.Publisher(
            "onboard_detector/server_tracking_latency_ms", Float64, queue_size=10
        )
        self._pub_total_latency = rospy.Publisher(
            "onboard_detector/server_total_pipeline_latency_ms", Float64, queue_size=10
        )

        # ── 모니터링 타이머 ──
        rospy.Timer(rospy.Duration(1.0), self._timeout_check_cb)
        rospy.Timer(rospy.Duration(5.0), self._performance_log_cb)

    # ------------------------------------------------------------------
    # 센서 콜백 오버라이드 — 타임아웃 모니터링 추가
    # ------------------------------------------------------------------

    def _depth_pose_cb(self, img_msg, pose_msg):
        self._timeout_monitor.touch("Depth+Pose")
        super()._depth_pose_cb(img_msg, pose_msg)

    def _depth_odom_cb(self, img_msg, odom_msg):
        self._timeout_monitor.touch("Depth+Odom")
        super()._depth_odom_cb(img_msg, odom_msg)

    def _lidar_pose_cb(self, cloud_msg, pose_msg):
        self._timeout_monitor.touch("LiDAR+Pose")
        super()._lidar_pose_cb(cloud_msg, pose_msg)

    def _lidar_odom_cb(self, cloud_msg, odom_msg):
        self._timeout_monitor.touch("LiDAR+Odom")
        super()._lidar_odom_cb(cloud_msg, odom_msg)

    def _color_img_cb(self, img_msg):
        self._timeout_monitor.touch("ColorImage")
        super()._color_img_cb(img_msg)

    def _yolo_detection_cb(self, det_msg):
        self._timeout_monitor.touch("YOLO")
        super()._yolo_detection_cb(det_msg)

    # ------------------------------------------------------------------
    # Timer 콜백 오버라이드 — latency 계측 추가
    # ------------------------------------------------------------------

    def _detection_cb(self, event):
        """DBSCAN + UV Detection 파이프라인 (latency 계측)."""
        t0 = time.time()
        super()._detection_cb(event)
        elapsed_ms = (time.time() - t0) * 1000.0
        self._pipeline_logger.record("Detection(DBSCAN+UV)", elapsed_ms)
        self._pub_detection_latency.publish(Float64(data=elapsed_ms))

    def _lidar_detection_cb(self, event):
        """LiDAR DBSCAN 클러스터링 (latency 계측)."""
        t0 = time.time()
        super()._lidar_detection_cb(event)
        elapsed_ms = (time.time() - t0) * 1000.0
        self._pipeline_logger.record("LiDAR-DBSCAN", elapsed_ms)

    def _tracking_cb(self, event):
        """Kalman Filter 기반 다중 객체 추적 (latency 계측)."""
        t0 = time.time()
        super()._tracking_cb(event)
        elapsed_ms = (time.time() - t0) * 1000.0
        self._pipeline_logger.record("Tracking(KF+Assoc)", elapsed_ms)
        self._pub_tracking_latency.publish(Float64(data=elapsed_ms))

    def _classification_cb(self, event):
        """Dynamic/Static 분류 (latency 계측)."""
        t0 = time.time()
        super()._classification_cb(event)
        elapsed_ms = (time.time() - t0) * 1000.0
        self._pipeline_logger.record("Classification", elapsed_ms)
        self._pipeline_logger.increment_cycle()

    def _vis_cb(self, event):
        """시각화 + 결과 전송.

        1) 로컬 RViz 시각화 (부모 클래스)
        2) 로봇에게 최종 추적 결과 MarkerArray 전송
        """
        t0 = time.time()
        super()._vis_cb(event)

        # ── 최종 결과 패키징 및 로봇 전송 ──
        self._publish_server_result()

        elapsed_ms = (time.time() - t0) * 1000.0
        self._pipeline_logger.record("Visualization+Tx", elapsed_ms)
        self._pub_total_latency.publish(Float64(data=elapsed_ms))

    # ------------------------------------------------------------------
    # 결과 패키징 및 전송
    # ------------------------------------------------------------------

    def _publish_server_result(self):
        """dynamic_bboxes를 MarkerArray로 직렬화하여 로봇에게 전송.

        각 Marker에 다음 정보를 인코딩:
        - CUBE 타입으로 위치/크기
        - text 필드에 속도 정보 (Vx,Vy,Ax,Ay)
        - color: 동적(빨강) / 정적(파랑)
        """
        markers = MarkerArray()
        now = rospy.Time.now()

        with self._lock:
            bboxes = list(self.dynamic_bboxes)

        for i, bbox in enumerate(bboxes):
            m = Marker()
            m.header.frame_id = "map"
            m.header.stamp = now
            m.ns = "server_result"
            m.id = i
            m.type = Marker.CUBE
            m.action = Marker.ADD
            m.lifetime = rospy.Duration(0.3)

            # 위치
            m.pose.position.x = bbox.x
            m.pose.position.y = bbox.y
            m.pose.position.z = bbox.z
            m.pose.orientation.w = 1.0

            # 크기
            m.scale.x = max(bbox.x_width, 0.05)
            m.scale.y = max(bbox.y_width, 0.05)
            m.scale.z = max(bbox.z_width, 0.05)

            # 색상: 동적 장애물 = 빨강 반투명
            m.color.r = 1.0
            m.color.g = 0.2
            m.color.b = 0.2
            m.color.a = 0.5

            # 속도/가속도 정보를 text 필드에 인코딩 (클라이언트에서 파싱)
            m.text = f"{bbox.Vx:.4f},{bbox.Vy:.4f},{bbox.Ax:.4f},{bbox.Ay:.4f}"

            markers.markers.append(m)

        # DELETE_ALL 후 ADD 방식 대신 개수가 줄면 남은 마커 삭제
        # (MarkerArray에 DELETEALL marker 추가)
        if len(markers.markers) == 0:
            delete_m = Marker()
            delete_m.header.frame_id = "map"
            delete_m.header.stamp = now
            delete_m.ns = "server_result"
            delete_m.action = Marker.DELETEALL
            markers.markers.append(delete_m)

        self._pub_server_result.publish(markers)

    # ------------------------------------------------------------------
    # 모니터링 타이머 콜백
    # ------------------------------------------------------------------

    def _timeout_check_cb(self, event):
        """주기적 데이터 타임아웃 검사."""
        self._timeout_monitor.check_all()

    def _performance_log_cb(self, event):
        """주기적 성능 요약 로그 출력."""
        summary = self._pipeline_logger.format_summary()
        if summary:
            uptime = time.time() - self._server_start_time
            hours = int(uptime // 3600)
            mins = int((uptime % 3600) // 60)
            secs = int(uptime % 60)

            rospy.loginfo(f"[M1 Server] Uptime: {hours:02d}:{mins:02d}:{secs:02d}")
            rospy.loginfo(summary)

            # 현재 추적 중인 객체 수
            with self._lock:
                n_tracked = len(self.tracked_bboxes)
                n_dynamic = len(self.dynamic_bboxes)
                n_filtered = len(self.filtered_bboxes)

            rospy.loginfo(
                f"[M1 Server] Objects: "
                f"filtered={n_filtered} | tracked={n_tracked} | dynamic={n_dynamic}"
            )
