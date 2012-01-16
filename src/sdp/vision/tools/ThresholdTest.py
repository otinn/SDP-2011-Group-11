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

import cv

class ThresholdTest:
  """
  A simple tool used in order to manually check/visualise threshold values.
  """
  def __init__(self, im): 
    # 180,0,38), cv.Scalar(255,214,255 
    # 68,68,68), cv.Scalar(124,124,124
    # self._blue_colour_min_bgr      = cv.Scalar(180,0,38)
    # self._blue_colour_max_bgr      = cv.Scalar(255,214,255)
    # 100 116 0 255 141 118
    # 100 101 100 193 147 128
    # 10,0,165), cv.Scalar(255,110,255
    
    # 0 0 97 178 176 178
    self.minR = 0
    self.minG = 0
    self.minB = 97
    self.maxR = 178
    self.maxG = 178
    self.maxB = 178
    self.storage = cv.CreateMemStorage()
    cv.NamedWindow("Source", 0)
    cv.ShowImage("Source", im)
    cv.NamedWindow("Threshold", 0)
    
    cv.CreateTrackbar("min-Red", "Threshold", self.minR, 255, self.set_minR)
    cv.CreateTrackbar("min-Green", "Threshold",  self.minG, 255, self.set_minG)
    cv.CreateTrackbar("min-Blue", "Threshold",  self.minG, 255, self.set_minB)
    
    cv.CreateTrackbar("max-Red", "Threshold", self.maxR, 255, self.set_maxR)
    cv.CreateTrackbar("max-Green", "Threshold",  self.maxG, 255, self.set_maxG)
    cv.CreateTrackbar("max-Blue", "Threshold",  self.maxB, 255, self.set_maxB)
    
    self.image0 = cv.CloneImage(im)
    self.imgThreshed = cv.CreateImage(cv.GetSize(self.image0), 8, 1)
    cv.ShowImage("Threshold", self.imgThreshed)
  
  def set_minR(self, val):
    self.minR = val
    self.on_thresh()
    
  def set_minG(self, val):
    self.minG = val
    self.on_thresh()
      
  def set_minB(self, val):
    self.minB = val
    self.on_thresh()
  
  def set_maxR(self, val):
    self.maxR = val
    self.on_thresh()

  def set_maxG(self, val):
    self.maxG = val
    self.on_thresh()

  def set_maxB(self, val):
    self.maxB = val
    self.on_thresh()
  
  def on_thresh(self, verbose=False):
    cv.InRangeS(self.image0, cv.Scalar(self.minR,self.minG,self.minB), cv.Scalar(self.maxR,self.maxG,self.maxB), self.imgThreshed)
    cv.ShowImage("Threshold", self.imgThreshed)
    
    if verbose:
      print self.minR, self.minG, self.minB, self.maxR, self.maxG, self.maxB
    
  def run(self):
    self.on_thresh()
    cv.WaitKey(0)
    
    imbw_clean = cv.CreateImage(cv.GetSize(self.imgThreshed), 8, 1)
    tmp = cv.CreateImage(cv.GetSize(self.imgThreshed), 8, 1)
    element = cv.CreateStructuringElementEx(3,3,1,1,cv.CV_SHAPE_ELLIPSE)
    cv.MorphologyEx(self.imgThreshed, imbw_clean, tmp, element , cv.CV_MOP_CLOSE, 2)
    cv.MorphologyEx(imbw_clean, imbw_clean, tmp, element , cv.CV_MOP_OPEN, 1)
    cv.ShowImage('test', self.imgThreshed)
    cv.WaitKey(0)
    
    
if __name__ == "__main__":
    im = cv.LoadImage("../../../../fixtures/12.02.11/shot0012.jpg")
    
    ThresholdTest(im).run()
