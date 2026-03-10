# 분산 처리 시스템 구축 계획 (Jetson-to-Mac M1 Pro)

## 1. 프로젝트 목표
Jetson Nano/Xavier 등의 로봇 온보드 컴퓨터에서 발생하는 연산 병목 현상을 해결하기 위해, 고성능 워크스테이션(Mac M1 Pro)을 활용한 **실시간 분산 처리 파이프라인**을 구축합니다.

## 2. 기기별 기능 정의

### [A] Client (Jetson - Robot Side)
- **YOLO 검출 (현행 유지)**: GPU를 활용한 실시간 객체 검출(Bounding Box 추출).
- **데이터 발행 (Publisher)**:
  - Raw Depth Image & LiDAR PointCloud.
  - YOLO 검출 결과 (`Detection2DArray`).
  - Robot Pose/Odometry.
- **최종 데이터 수신 (Subscriber)**:
  - Mac 서버에서 계산되어 돌아온 최적화된 장애물 궤적 및 속도 정보.
- **로컬 안전 제어**: 서버 지연 발생 시 로컬 데이터를 활용한 최소한의 충돌 방지 로직.

### [B] Server (Mac M1 Pro - Station Side)
- **고성능 연산 (Core Processing)**:
  - **DBSCAN 클러스터링**: 포인트클라우드 기반 정밀 객체 분리.
  - **Multi-Object Tracking (MOT)**: Kalman Filter를 이용한 다중 객체 추적.
  - **Dynamic/Static Classification**: 객체의 속도 및 이동 패턴 분석.
- **데이터 동기화**: 네트워크 지연을 고려한 센서 데이터 Time-Sync (Message Filters).
- **최종 결과 전송**: 추적된 장애물의 위치, 속도, 크기 정보를 로봇으로 재전송.

## 3. 구현 예정 기능 리스트 (Todo)
- [ ] **네트워크 대역폭 최적화**: `CompressedDepth` 전송 방식 적용.
- [ ] **서버 가용성 체크**: 서버 연결이 끊겼을 때 로봇이 안전하게 멈추거나 로컬 모드로 전환하는 로직.
- [ ] **M1 Pro 성능 모니터링**: 처리 단계별 Latency 측정 도구 구현.
- [ ] **Docker 환경 구성**: Mac과 Jetson 간의 환경 일치를 위한 Docker-compose 구축 (선택 사항).
