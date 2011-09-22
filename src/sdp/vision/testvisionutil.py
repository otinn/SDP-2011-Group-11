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

import unittest
import datetime
from visionutil import AngleStabilizer
from math import pi
from time import sleep

class TestAngleStabilizer(unittest.TestCase):
  def setUp(self):
    self.stabilizer = AngleStabilizer()
  
  def test_calc_diff_right_angle(self):
    self.assertEqual(self.stabilizer.calc_diff(0.25 * pi, 0.75 * pi), 0.5 * pi)
    
  def test_calc_diff_left_angle(self):
    self.assertEqual(self.stabilizer.calc_diff(0.75 * pi, 0.25 * pi), -0.5 * pi)
  
  def test_add_good_angles(self):
    self.assertEqual(len(self.stabilizer._get_elements()), 0)
    
    self.stabilizer.add(pi, datetime.datetime.now())
    self.assertEqual(len(self.stabilizer._get_elements()), 1)
    
    self.stabilizer.add(0.75 * pi, datetime.datetime.now())
    self.assertEqual(len(self.stabilizer._get_elements()), 2)
  
  def test_add_extreme_angle(self):
    self.stabilizer.add(pi, datetime.datetime.now())
    self.stabilizer.add(0, datetime.datetime.now())
    self.assertEqual(len(self.stabilizer._get_elements()), 1)
  
  def test_add_angle_after_time_thresh(self):
    self.stabilizer.add(pi, datetime.datetime.now())
    
    sleep(0.5)
    
    self.assertEqual(len(self.stabilizer._get_elements()), 0)
  
  def test_add_extreme_angle_after_time_thresh(self):
    self.stabilizer.add(pi, datetime.datetime.now())
    self.stabilizer.add(0.75 * pi, datetime.datetime.now())
    
    sleep(0.5)
    
    self.stabilizer.add(0, datetime.datetime.now())
    
    self.assertEqual(len(self.stabilizer._get_elements()), 1)


if __name__ == '__main__':
  unittest.main()