# 분산 처리 시스템 상세 구현 가이드

이 가이드는 `server_test` 폴더 내의 클라이언트/서버 코드를 작성할 때 준수해야 할 기술적 세부 사항입니다.

## 1. 통신 프로토콜 (Message Exchange)

서버(Mac)와 클라이언트(Jetson) 간에 교환되는 주요 토픽과 타입입니다.

| 데이터 유형 | 토픽명 (예시) | 메시지 타입 | 전송 방향 | 설명 |
| :--- | :--- | :--- | :--- | :--- |
| **BBox** | `/yolo_detector/detected_bounding_boxes` | `vision_msgs/Detection2DArray` | Robot -> Mac | YOLO 추론 결과 |
| **Depth** | `/camera/depth/image_raw/compressed` | `sensor_msgs/CompressedImage` | Robot -> Mac | 압축된 깊이 이미지 |
| **Result** | `/onboard_detector/server_processed_obstacles` | `visualization_msgs/MarkerArray` | Mac -> Robot | 최종 추적 결과 |

## 2. 서버 사이드 (Mac M1 Pro) 개발 지침

- **멀티스레딩 활용**: `DynamicDetectorServer` 클래스 내에서 데이터 수신(Subscriber)과 연산(Timer)이 서로의 루프에 방해되지 않도록 `Lock` 구조를 철저히 관리합니다.
- **성능 측정**: `rospy.Timer` 내에서 연산 시작과 끝의 시간을 측정하여 `std_msgs/Float64` 타입으로 발행, 전체 시스템 지연 시간을 실시간 모니터링합니다.
- **예외 처리**: 데이터 수신이 일정 시간(예: 0.2초) 이상 끊기면 경고 로그를 남기고, 마지막 상태를 보존합니다.

## 3. 클라이언트 사이드 (Jetson) 개발 지침

- **최소 코드 변경**: 기존 `DynamicDetector` 클래스를 상속받아 `_detection_cb`, `_tracking_cb` 등 무거운 연산을 담당하는 콜백 함수만 오버라이드(Override)하여 비워둡니다.
- **서버 결과 통합**: 서버에서 수신한 데이터를 로봇이 즉시 제어에 사용할 수 있도록 로컬 변수(예: `self.dynamic_bboxes`)를 갱신합니다.
- **안전 모드 (Fail-Safe)**: 서버의 응답이 없으면 Jetson 자체에서 간단한 장애물 회피 로직을 실행하도록 구성합니다.

## 4. 실행 커맨드

### Jetson (로봇 쪽)
```bash
rosrun onboard_detector_python detector_node_client.py
```

### Mac (서버 쪽)
```bash
rosrun onboard_detector_python detector_node_server.py
```
