#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Docker Entrypoint — ROS Noetic Server
# ══════════════════════════════════════════════════════════════
set -e

# libgomp TLS 할당 오류 방지 (ARM64/M1 Pro + PyTorch)
# 시스템 libgomp를 먼저 찾아서 preload
GOMP_PATH=$(find /usr/lib -name "libgomp.so.1" 2>/dev/null | head -1)
if [ -n "$GOMP_PATH" ]; then
    export LD_PRELOAD="$GOMP_PATH"
    echo "[entrypoint] LD_PRELOAD=$GOMP_PATH"
fi

# ROS 환경 소싱
source /opt/ros/noetic/setup.bash
source /catkin_ws/devel/setup.bash

# ROS_MASTER_URI 설정 (환경변수로 오버라이드 가능)
export ROS_MASTER_URI=${ROS_MASTER_URI:-http://localhost:11311}
export ROS_IP=${ROS_IP:-0.0.0.0}

echo "══════════════════════════════════════════════════════════"
echo "  Onboard Detector Server — Docker Container"
echo "══════════════════════════════════════════════════════════"
echo "  ROS_MASTER_URI : ${ROS_MASTER_URI}"
echo "  ROS_IP         : ${ROS_IP}"
echo "  ROS_HOSTNAME   : ${ROS_HOSTNAME:-$(hostname)}"
echo "══════════════════════════════════════════════════════════"

exec "$@"
