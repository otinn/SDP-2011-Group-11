# ###################################################
# Copyright (C) 2011 SDP 2011 Group 11
# This file is part of SDP 2011 Group 11's SDP solution.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with This program.  If not, see <http://www.gnu.org/licenses/>.
# ###################################################

import sys
from datetime import datetime
from visionutil import flip_coordinates, normalize_rotation, flip_rotation

class VisionCom():
  def __init__(self, vision, colour='blue', side='right'):
    self._vision          = vision
    self._colour          = colour
    self._frame_timestamp = None
    self._side            = side
    print '/general/identify vision primary ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ' vision v 0.1'
    sys.stdout.flush()


  def transmit_ball_location(self):
    ball = self._vision.get_ball()
    if ball is not None:
      ball_centre = ball[0]
      
      if self._side == 'left':
        ball_centre = flip_coordinates(ball_centre[0], ball_centre[1])
        
      print '/vision/xy ball %f %f %s' % (ball_centre[0], ball_centre[1], self._frame_timestamp)

  def transmit_robot_location(self, colour):
    (robot_centre, robot_rotation) = self._vision.get_robot(colour)
  
    name  = 'us' if self._colour == colour else 'enemy'
    
    if robot_centre is not None:
      if self._side == 'left':
        robot_centre   = flip_coordinates(robot_centre[0], robot_centre[1])

      print '/vision/xy %s %f %f %s' % (name, robot_centre[0], robot_centre[1], self._frame_timestamp)
    if robot_rotation is not None: 
      if self._side == 'left':
        robot_rotation = flip_rotation(robot_rotation)
      print '/vision/rotation %s %f %s' % (name, robot_rotation, self._frame_timestamp)
    
    
  def transmit(self, frame_timestamp):
    self._frame_timestamp = frame_timestamp
    
    self.transmit_ball_location()
    self.transmit_robot_location('blue')
    self.transmit_robot_location('yellow')
    sys.stdout.flush()
  
