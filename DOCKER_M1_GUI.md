# ROS1 Noetic on Apple Silicon (M1/M2) with GUI

이 설정은 Apple Silicon에서 `linux/amd64` 에뮬레이션으로 Ubuntu 20.04 + ROS Noetic을 실행합니다.

## 1) XQuartz 설치 및 설정 (macOS)

1. XQuartz 설치
```bash
brew install --cask xquartz
```
2. XQuartz 실행 후 `Preferences > Security`에서 `Allow connections from network clients` 체크
3. XQuartz 재시작
4. 터미널에서 X11 접근 허용
```bash
xhost + 127.0.0.1
```

## 2) 컨테이너 빌드/실행

프로젝트 루트에서:

```bash
docker compose -f docker-compose.m1.yml build
docker compose -f docker-compose.m1.yml up -d
docker compose -f docker-compose.m1.yml exec ros-noetic bash
```

컨테이너 내부에서 최초 1회:
```bash
cd /catkin_ws
catkin_make
source devel/setup.bash
```

## 3) 데모 실행

`docker compose up` 후 `roscore`는 자동 실행됩니다. 로그 확인:
```bash
docker compose -f docker-compose.m1.yml logs -f
```

그 다음 컨테이너 내부에서 아래를 각각 다른 터미널(또는 tmux)로 실행:

```bash
source /catkin_ws/devel/setup.bash
rosbag play -l /catkin_ws/src/LV-DOT/corridor_demo.bag
```

```bash
source /catkin_ws/devel/setup.bash
roslaunch onboard_detector run_detector.launch
```

```bash
source /catkin_ws/devel/setup.bash
rviz
```

`rviz` 창이 macOS로 뜨면 GUI 연동이 정상입니다.

## 4) 종료

```bash
docker compose -f docker-compose.m1.yml down
```
