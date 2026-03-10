#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Docker Entrypoint — ROS Noetic Server
# ══════════════════════════════════════════════════════════════
set -e

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
