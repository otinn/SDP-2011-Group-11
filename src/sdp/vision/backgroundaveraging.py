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

class BackgroundAveraging():
  def __init__(self, img):
    self._img = img
    self._sz = cv.GetSize(img)
    
    self._IavgF = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 3)
    self._IdiffF = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 3)
    self._IprevF = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 3)
    self._IhiF = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 3)
    self._IlowF = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 3)
    self._Ilow1 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    self._Ilow2 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    self._Ilow3 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    self._Ihi1 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    self._Ihi2 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    self._Ihi3 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    
    cv.Zero(self._IavgF)
    cv.Zero(self._IdiffF)
    cv.Zero(self._IprevF)
    cv.Zero(self._IhiF)
    cv.Zero(self._IlowF)
    
    self._Icount = 0.0001 # protect against divid by 0
    
    self._Iscratch= cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 3)
    self._Iscratch2 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 3)
    self._Igray1 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    self._Igray2 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    self._Igray3 = cv.CreateImage(self._sz, cv.IPL_DEPTH_32F, 1)
    self._Imaskt = cv.CreateImage(self._sz, cv.IPL_DEPTH_8U, 1)
    
    cv.Zero(self._Iscratch)
    cv.Zero(self._Iscratch2)
    
    self._high_threshold = 22.0
    self._low_threshold  = 6.0

  def set_threshold_values(self, value, degree):
    setattr(self, "_%s_threshold" % (degree,), value)
    
  def get_threshold_values(self, degree):
    return getattr(self, "_%s_threshold" % (degree,))
  
  # Learn the background statistics for one more frame
  def accumulate_background(self, img):
    cv.CvtScale(img, self._Iscratch, 1, 0)

    cv.Acc(self._Iscratch, self._IavgF)
    cv.AbsDiff(self._Iscratch, self._IprevF, self._Iscratch2)
    cv.Acc(self._Iscratch2, self._IdiffF)
    self._Icount += 1.0
  
    cv.Copy(self._Iscratch, self._IprevF)
  
  def create_models_from_stats(self, save_model=True):
    cv.ConvertScale(self._IavgF, self._IavgF, (1.0 / self._Icount))
    cv.ConvertScale(self._IdiffF, self._IdiffF, (1.0 / self._Icount))

    # Make sure diff is always something
    cv.AddS(self._IdiffF, cv.Scalar(1.0,1.0,1.0), self._IdiffF)
    self.set_high_threshold(self._high_threshold)
    self.set_low_threshold(self._low_threshold)
    
    if save_model:
      self.save_bg_model()

  def set_high_threshold(self, scale):
    cv.ConvertScale(self._IdiffF, self._Iscratch, scale)
    cv.Add(self._Iscratch, self._IavgF, self._IhiF)
    cv.Split(self._IhiF, self._Ihi1, self._Ihi2, self._Ihi3, None)

  def set_low_threshold(self, scale):
    cv.ConvertScale(self._IdiffF, self._Iscratch, scale)
    cv.Add(self._Iscratch, self._IavgF, self._IlowF)
    cv.Split(self._IlowF, self._Ilow1, self._Ilow2, self._Ilow3, None)
  
  def save_bg_model(self):
    cv.SaveImage("calibration_data/_Iscratch.jpg", self._Iscratch)
    cv.SaveImage("calibration_data/_Ilow1.jpg", self._Ilow1)
    cv.SaveImage("calibration_data/_Ihi1.jpg", self._Ihi1)
    cv.SaveImage("calibration_data/_Ilow2.jpg", self._Ilow2)
    cv.SaveImage("calibration_data/_Ihi2.jpg", self._Ihi2)
    cv.SaveImage("calibration_data/_Ilow3.jpg", self._Ilow3)
    cv.SaveImage("calibration_data/_Ihi3.jpg", self._Ihi3)
    cv.SaveImage("calibration_data/_Imaskt.jpg", self._Imaskt)
    
  def load_bg_model(self):
    self._Iscratch = cv.LoadImage("calibration_data/_Iscratch.jpg")
    self._Ilow1    = cv.LoadImage("calibration_data/_Ilow1.jpg")
    self._Ihi1     = cv.LoadImage("calibration_data/_Ihi1.jpg")
    self._Ilow2    = cv.LoadImage("calibration_data/_Ilow2.jpg")
    self._Ihi2     = cv.LoadImage("calibration_data/_Ihi2.jpg")
    self._Ilow3    = cv.LoadImage("calibration_data/_Ilow3.jpg")
    self._Ihi3     = cv.LoadImage("calibration_data/_Ihi3.jpg")
    self._Imaskt   = cv.LoadImage("calibration_data/_Imaskt.jpg")
  
  # Create a mask
  def background_diff(self, I, im_mask):
    cv.CvtScale(I, self._Iscratch, 1, 0)
    cv.Split(self._Iscratch, self._Igray1, self._Igray2, self._Igray3, None)

    # channel 1
    cv.InRange(self._Igray1, self._Ilow1, self._Ihi1, im_mask)
  
    # channel 2
    cv.InRange(self._Igray2, self._Ilow2, self._Ihi2, self._Imaskt)
    cv.Or(im_mask, self._Imaskt, im_mask)
  
    # channel 3
    cv.InRange(self._Igray3, self._Ilow3, self._Ihi3, self._Imaskt)
    cv.Or(im_mask, self._Imaskt, im_mask)

  def contour_iterator(self, contour):
    while contour:
      yield contour
      contour = contour.h_next()
 
  def connect_components(self, mask, poly_hull0=False, area_threshold=20):
    tmp = cv.CreateImage(cv.GetSize(mask), 8, 1)
    element = cv.CreateStructuringElementEx(3,3,1,1,cv.CV_SHAPE_ELLIPSE)
    cv.MorphologyEx(mask, mask, tmp, element, cv.CV_MOP_CLOSE, 6)
    cv.MorphologyEx(mask, mask, tmp, element, cv.CV_MOP_OPEN, 1)
    
    storage = cv.CreateMemStorage(0)
    contours = cv.FindContours(mask, storage, cv.CV_RETR_EXTERNAL, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))
    
    contourList = []

    for contour in self.contour_iterator(contours):
      if cv.ContourArea(contour) > area_threshold:
        if poly_hull0:
          c_new = cv.ApproxPoly(contour, storage, cv.CV_POLY_APPROX_DP, 2, 0)
        else:
          c_new = cv.ConvexHull2(contour, storage, cv.CV_CLOCKWISE, 1)
        
        contourList.append(c_new)

    CVX_WHITE = cv.CV_RGB(0xff,0xff,0xff)
    
    cv.Zero(mask)
    for contour in contourList:
      cv.DrawContours(mask, contour, CVX_WHITE, CVX_WHITE, -1, cv.CV_FILLED, 8)
    
    del contours
    
    
if __name__ == '__main__':
  frameCount = 0
  capture = cv.CaptureFromCAM(-1)
  
  frame = cv.QueryFrame(capture)
  ba = BackgroundAveraging(frame)
  
  while(True):
    frameCount += 1
    frame = cv.QueryFrame(capture)
    
    if(not frame):
      break
      
    sz = cv.GetSize(frame)
    
    mask1 = cv.CreateImage(sz, cv.IPL_DEPTH_8U, 1)
    mask3 = cv.CreateImage(sz, cv.IPL_DEPTH_8U, 3)
    
    if(frameCount < 100):
      ba.accumulate_background(frame)
    elif(frameCount == 100):
      ba.create_models_from_stats()
    else:
      ba.background_diff(frame, mask1)
      ba.connect_components(mask1)
    
      cv.CvtColor(mask1, mask3, cv.CV_GRAY2BGR)
      cv.Norm(mask3, mask3, cv.CV_C, None)
      cv.Threshold(mask3, mask3, 100, 1, cv.CV_THRESH_BINARY)
      cv.Mul(frame, mask3, frame, 1.0)
  
      cv.ShowImage("Background Averaging1", mask1)
      cv.ShowImage("Background Averaging", frame)
  
      c = cv.WaitKey(20) 
      if c != -1:
        if c == 27 or chr(c) == 'q':
          break
        elif chr(c) == 'a': 
          ba._update_high_threshold_up()     
        elif chr(c) == 's':
          ba._update_high_threshold_down()
        elif chr(c) == 'z': 
          ba._update_low_threshold_up()     
        elif chr(c) == 'x':
          ba._update_low_threshold_down()

