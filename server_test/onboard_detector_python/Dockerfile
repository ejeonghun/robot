# ══════════════════════════════════════════════════════════════
# Dockerfile — ROS Noetic Server for M1 Pro (ARM64)
# ══════════════════════════════════════════════════════════════
# 이 Dockerfile은 Mac M1 Pro에서 Docker를 통해 ROS Noetic 서버를
# 실행하기 위한 이미지를 빌드합니다.
#
# 빌드: docker compose build
# 실행: docker compose up
# ══════════════════════════════════════════════════════════════

FROM ros:noetic-ros-base

LABEL maintainer="onboard_detector_server"
LABEL description="ROS Noetic server for distributed obstacle detection (M1 Pro ARM64)"

# ── 환경 변수 ──
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_WS=/catkin_ws
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# libgomp TLS 할당 오류 방지 (ARM64/M1 Pro + PyTorch)
ENV LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1

# ── 시스템 패키지 설치 ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    python3-catkin-tools \
    python3-osrf-pycommon \
    ros-noetic-cv-bridge \
    ros-noetic-vision-msgs \
    ros-noetic-message-filters \
    ros-noetic-tf \
    ros-noetic-rosbridge-server \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Python 패키지 설치 ──
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# ── Catkin 워크스페이스 구성 ──
RUN mkdir -p ${ROS_WS}/src
WORKDIR ${ROS_WS}

# 패키지 소스 복사
COPY . ${ROS_WS}/src/onboard_detector_python/

# ── Catkin 빌드 ──
SHELL ["/bin/bash", "-c"]
RUN source /opt/ros/noetic/setup.bash && \
    cd ${ROS_WS} && \
    catkin_make -DCMAKE_BUILD_TYPE=Release && \
    echo "source ${ROS_WS}/devel/setup.bash" >> /root/.bashrc

# ── 서버 노드 실행 권한 부여 ──
RUN chmod +x ${ROS_WS}/src/onboard_detector_python/src/onboard_detector_python/detector_node_server.py && \
    chmod +x ${ROS_WS}/src/onboard_detector_python/docker-entrypoint.sh

# ── 엔트리포인트 ──
ENTRYPOINT ["/catkin_ws/src/onboard_detector_python/docker-entrypoint.sh"]
CMD ["roslaunch", "onboard_detector_python", "run_detector_server.launch"]
