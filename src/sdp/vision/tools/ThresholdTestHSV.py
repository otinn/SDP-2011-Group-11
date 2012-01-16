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
  def __init__(self):
    # self._black_dot_colour_min_hsv = cv.Scalar(43,32,42)
    # self._black_dot_colour_max_hsv = cv.Scalar(73,91,69)
    # 41 38 37 73 115 60
    # 29 28 57 64 111 94
    # 29 28 37 77 101 76
    # self._black_dot_colour_min_hsv = cv.Scalar(29,21,37)
    # self._black_dot_colour_max_hsv = cv.Scalar(77,198,69)
    
    # self.minH = 0
    # self.minS = 0
    # self.minV = 0
    # self.maxH = 179
    # self.maxS = 255
    # self.maxV = 135
    # 29 21 22 74 198 32
    # self._ball_colour_min_hsv      = cv.Scalar(0,114,40)
    # self._ball_colour_max_hsv      = cv.Scalar(13,255,255)
    # 0 104 40 15 255 255
    self.minH = 0
    self.minS = 98
    self.minV = 52
    self.maxH = 14
    self.maxS = 255
    self.maxV = 255
    
    self.storage = cv.CreateMemStorage()
    
    cv.NamedWindow("Threshold", 0)

    cv.CreateTrackbar("min-Hue", "Threshold",  self.minH, 179, self.set_minH)
    cv.CreateTrackbar("min-Saturation", "Threshold",  self.minS, 255, self.set_minS)    
    cv.CreateTrackbar("min-Value", "Threshold", self.minV, 255, self.set_minV)

    cv.CreateTrackbar("max-Hue", "Threshold",  self.maxH, 179, self.set_maxH)    
    cv.CreateTrackbar("max-Saturation", "Threshold",  self.maxS, 255, self.set_maxS)
    cv.CreateTrackbar("max-Value", "Threshold", self.maxV, 255, self.set_maxV)  
    
    self.image0      = None
    self.imgThreshed = None
    self._capture    = None
    
  def set_minH(self, val):
    self.minH = val
    self.on_thresh()

  def set_minS(self, val):
    self.minS = val
    self.on_thresh()

  def set_minV(self, val):
    self.minV = val
    self.on_thresh()

      
  def set_maxH(self, val):
    self.maxH = val
    self.on_thresh()

  def set_maxS(self, val):
    self.maxS = val
    self.on_thresh()

  def set_maxV(self, val):
    self.maxV = val
    self.on_thresh()
  
  
  def on_thresh(self):
    cv.InRangeS(self.image0, cv.Scalar(self.minH,self.minS,self.minV), cv.Scalar(self.maxH,self.maxS,self.maxV), self.imgThreshed)
    cv.ShowImage("Threshold", self.imgThreshed)
    
    print self.minH, self.minS, self.minV, self.maxH, self.maxS, self.maxV
    
  def run(self):
    self.on_thresh()
    cv.WaitKey(0)
    
  def update_im(self, im, hsv=True):
    if hsv:
      self.image0 = cv.CreateImage(cv.GetSize(im), 8, 3)
      cv.CvtColor(im, self.image0, cv.CV_BGR2HSV)
    else:
      self.image0 = im
    self.imgThreshed = cv.CreateImage(cv.GetSize(self.image0), 8, 1)    
    
    self.on_thresh()
  
  def sortFeed(self):
    while(True):
      frame = cv.QueryFrame(self._capture)

      cv.ShowImage("Feed", frame)
      self._capture = cv.CaptureFromCAM(0)
      c = cv.WaitKey(10) % 0x100
      if c != -1:
        if c == 27 or chr(c) == 'q':          
          exit()
        if chr(c) == 'w':
          break
      
    
  def run_vid(self):
    self._capture = cv.CaptureFromCAM(0)
    self.sortFeed()
    while True:
      frame = cv.QueryFrame(self._capture)
      self.update_im(frame)
      self.on_thresh()
      if cv.WaitKey(2) == 27:
          break
    
    
if __name__ == "__main__":
    # im = cv.LoadImage("1234.jpg")
    # cv.ShowImage('Source', im)
    
    # imgHSV = cv.CreateImage(cv.GetSize(im), 8, 3)
    # cv.CvtColor(im, imgHSV, cv.CV_BGR2HSV)
    # smoothed_img = cv.CreateImage(cv.GetSize(imgHSV),8 , 3)
    # cv.Smooth(imgHSV, smoothed_img, smoothtype=cv.CV_GAUSSIAN, param1=5)
    # 
    ThresholdTest().run_vid()
    
    
