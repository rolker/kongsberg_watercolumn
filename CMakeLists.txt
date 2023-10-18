cmake_minimum_required(VERSION 2.8.3)
project(kongsberg_watercolumn)

find_package(catkin REQUIRED COMPONENTS
  rospy
  marine_acoustic_msgs
)

catkin_python_setup()

catkin_package(
#  INCLUDE_DIRS include
#  LIBRARIES 
  CATKIN_DEPENDS rospy marine_acoustic_msgs
#  DEPENDS system_lib
)

include_directories(
# include
  ${catkin_INCLUDE_DIRS}
)

