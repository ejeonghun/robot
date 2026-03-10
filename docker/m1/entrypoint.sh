#!/usr/bin/env bash
set -e

source /opt/ros/noetic/setup.bash

if [ -d "/catkin_ws/src/LV-DOT" ] && [ ! -f "/catkin_ws/devel/setup.bash" ]; then
  echo "[entrypoint] catkin workspace not built yet. Running catkin_make..."
  cd /catkin_ws
  catkin_make
fi

if [ -f "/catkin_ws/devel/setup.bash" ]; then
  source /catkin_ws/devel/setup.bash
fi

export ROS_MASTER_URI="${ROS_MASTER_URI:-http://localhost:11311}"
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1

exec "$@"
