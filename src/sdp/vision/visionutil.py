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

from math import pi, cos, sin, tan, atan2, sqrt, pow
import cv
import math
import datetime

def contour_iterator(contour):
  while contour:
    yield contour
    contour = contour.h_next()

def flip_coordinates(x, y, width=244, height=122):
  return (width - x, height - y)

def normalize_rotation(rotation):
  full_circle = 2 * pi
  while rotation < 0:           rotation += full_circle
  while rotation > full_circle: rotation -= full_circle
  return rotation   

def flip_rotation(rotation):
  return normalize_rotation(pi + rotation)

def euclidean_distance(vec_a, vec_b):
  """
  Calculates the Euclidean distance between two given vectors. 
  """
  return sqrt(pow(vec_a[0] - vec_b[0], 2) + pow(vec_a[1] - vec_b[1], 2))

def points_with_dist(point1, point2, dist=25.0):
  il_pt     = (point1[0] - point2[0], point1[1] - point2[1])
  edist     = euclidean_distance(point1, point2)
  if edist == 0:
    return None
  else:
    dist_pt   = (dist / edist)
    il_pt_dis = (il_pt[0] * dist_pt, il_pt[1] * dist_pt)
    return (point2[0] - il_pt_dis[0], point2[1] - il_pt_dis[1])  

def calc_angle(v1, v2):
  """
  Used in order to calculate the angle of a robot relative to the field.
  """
  return normalize_rotation(-atan2(v1[0] - v2[0], v1[1] - v2[1]))

def round_pts(pt):
  return (cv.Round(pt[0]), cv.Round(pt[1]))

def find_line_coefficients(pt1, pt2):
  a = pt2[1] - pt1[1]
  b = pt1[0] - pt2[0]
  c = b * pt1[1] + a * pt1[0]

  return (a,b,c)

def solve_intersection(coefs1, coefs2):
  det = coefs1[0] * coefs2[1] - coefs2[0] * coefs1[1]

  if det == 0:
    return None

  x = (coefs2[1] * coefs1[2] - coefs1[1] * coefs2[2]) / det
  y = (coefs1[0] * coefs2[2] - coefs2[0] * coefs1[2]) / det

  return (x,y)

class AngleStabilizer():
  def __init__(self):
    self._elements = []
    self._max_angles_threshold     = 3
    self._max_angle_diff_threshold = 0.5 * math.pi
    self._max_time_diff_threshold  = datetime.timedelta(seconds=0.3)
    
  def set_threshold_values(self, value, name):
    setattr(self, "_%s_threshold" % (name,), value)

  def get_threshold_values(self, name):
    return getattr(self, "_%s_threshold" % (name,))
  
  def _get_elements(self):
    self.update_elements(datetime.datetime.now())
    return self._elements
    
  @staticmethod
  def calc_diff(first_angle, second_angle):
    if first_angle or second_angle is None: return 0
    difference = second_angle - first_angle
    while (difference < -math.pi): difference += 2 * math.pi
    while (difference >  math.pi): difference -= 2 * math.pi
    return difference
    
  def _normalize_rotation(self, rotation):
    full_circle = 2 * math.pi
    while rotation < 0:           rotation += full_circle
    while rotation > full_circle: rotation -= full_circle
    return rotation
  
  def update_elements(self, timestamp):
    if self._elements:
      if timestamp - self._elements[-1][1] > self._max_time_diff_threshold:
        del self._elements[:]
    
  def add(self, rotation, timestamp):
    if len(self._elements) == self._max_angles_threshold:
      self._elements.pop(0)
    
    self.update_elements(timestamp)
    
    if self._elements:
      if abs(AngleStabilizer.calc_diff(rotation, self.get())) < self._max_angle_diff_threshold:
        self._elements.append((self._normalize_rotation(-rotation), timestamp))
    else:
      self._elements.append((self._normalize_rotation(-rotation), timestamp))
                
  def get(self):
    self.update_elements(datetime.datetime.now())
    
    if len(self._elements) == 0: 
      return None
    if len(self._elements) == 1: 
      return self._normalize_rotation(-self._elements[0][0])
    
    x_sum = 0
    y_sum = 0
    num = len(self._elements)
    res = None
    
    for i in range(num):
      angle = self._elements[num - i - 1][0]
      x_sum += math.sin(angle)
      y_sum += math.cos(angle)
      if x_sum != 0 or y_sum:
        res = self._normalize_rotation(-math.atan2(x_sum, y_sum))
      
    return res
    
 
if __name__ == '__main__':
  from time import sleep
  
  angles = AngleStabilizer()
  angles.add(math.pi, datetime.datetime.now())
  print "The angle after adding Pi:", angles.get()  
    
  angles.add(0, datetime.datetime.now())
  print "The angle after adding another 0 * Pi:", angles.get()
  
  
  angles02 = AngleStabilizer()
  angles02.add(math.pi, datetime.datetime.now())
  print "The angle after adding Pi:", angles02.get()  
    
  sleep(2)
  
  angles02.add(0, datetime.datetime.now())
  print "The angle after adding another 0 * Pi:", angles02.get()
  


