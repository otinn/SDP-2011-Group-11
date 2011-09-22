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
import time
import yaml
import sys, os
from backgroundaveraging import BackgroundAveraging
from vision              import Vision
from visioncom           import VisionCom
from calibrate           import Calibrate
from datetime            import datetime
from v4lFeed             import Capture

class VisionWrapper:
  def __init__(self, draw=True, colour='blue', side='left', main_pitch=True, load_bg_model=False, corners_from_mem=False):
    _filepath                       = sys.argv[0]
    _relpath                        = os.path.split(_filepath)[0]
    if _relpath is not '': _relpath = _relpath + '/'
    
    self._bg                        = cv.LoadImage(_relpath + "b02.jpg")
    self._draw                      = draw
    self._colour                    = colour
    self._side                      = side
    self._n_avg_bg                  = 30
    self._corners_from_mem          = corners_from_mem
    
    self._last_update               = 0
    self._fps_update_interval       = 0.5
    self._num_frames                = 0
    self._fps                       = 0

    self._calibrate                 = Calibrate((9,6))
    self.calibrate_cam(from_mem     = True)
    self._config                    = yaml.load(file('config/020311-0830-main_pitch.yaml', 'r'))
    self._vision                    = Vision(self._bg, self._calibrate, self._config, fix_distortions = True, main_pitch=main_pitch, corners_from_mem=self._corners_from_mem)
    self._vision_com                = VisionCom(self._vision, colour=self._colour, side=self._side)
    self._ba                        = None
    self._load_bg_model             = load_bg_model
    
    self._frame_name                = 'annotated'
    self._capture                   = Capture()
    
    self._base_time = 0
  
  def online_feed(self): 
    frames = []
    if self._load_bg_model: frames = [self._capture.pull()]
    else: frames = [self._capture.pull() for i in range(self._n_avg_bg)]
    
    self._vision.avg_bg_frames(frames, load_from_mem=self._load_bg_model)
    
    reset_base  = False
    last_base_time = 0
    time_interval  = 60 
    while 1:
      lstart = time.time()
      if lstart - last_base_time >= time_interval:
        self.calc_baseline()
        last_base_time = time.time()
      
      frame = self._capture.pull()
      timestamp = datetime.fromtimestamp(self.correct_timestamp() / 1000.0).strftime('%Y-%m-%dT%H:%M:%S.%f')
      
      self._vision.update(frame)

      self._vision_com.transmit(timestamp)
      self.update_fps()

      try:
        if self._frame_name == 'annotated':
          vframe = self._vision.get_frame(name='source', annotated=True)
        else:
          vframe = self._vision.get_frame(name=self._frame_name, annotated=False)
      except:
        vframe   = self._vision.get_frame(name='annotated', annotated=True)      
      
      font = cv.InitFont(cv.CV_FONT_HERSHEY_PLAIN, 0.75, 0.75, 0.0, 1, cv.CV_AA)
      msg  = ">> FPS: %.2f" % (self._fps,)  
      cv.PutText(vframe, msg, (10,15), font, cv.Scalar(0,0,255))
      
      if self._draw:
        cv.ShowImage("Feed", vframe)
            
        c = cv.WaitKey(2) % 0x100
        if c != -1:
          if c == 27 or chr(c) == 'q' : break
          if chr(c) == 'p'            : cv.SaveImage(timestamp + ".jpg", vframe)
          if chr(c) == 'a'            : self._frame_name = 'annotated'
          if chr(c) == 's'            : self._frame_name = 'source'
          if chr(c) == 'r'            : self._frame_name = 'threshed_red'
          if chr(c) == 'y'            : self._frame_name = 'threshed_yellow'
          if chr(c) == 'b'            : self._frame_name = 'threshed_blue'
          if chr(c) == 'h'            : self._frame_name = 'threshed_black'
          if chr(c) == 'g'            : self._frame_name = 'threshed_green'
          if chr(c) == 'f'            : self._frame_name = 'foreground'
          if chr(c) == 'c'            : self._frame_name = 'foreground_connected'
      
  def offline_feed(self, filename):
    capture = cv.CaptureFromFile(filename)
    width   = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH))
    height  = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT))
    
    fps     = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FPS))
    frames  = int(cv.GetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_COUNT))
    
    for f in range(frames - 2):
      frame = cv.QueryFrame(capture)
      timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
      frame = self._calibrate.undistort_single_image(frame)

      self._vision.update(frame)
      self._vision_com.transmit(timestamp)
      self.update_fps()
      
      if self._draw:
        cv.ShowImage("Feed", frame)
      
      if cv.WaitKey(1000 / fps) == 27:
        break
  
  def calc_baseline(self):
    for i in range(3):
      self._capture.pull()
    self._base_time = int(round(time.time() * 1000))

  def correct_timestamp(self):
    t = int(round(time.time() * 1000))
    return t - (t - self._base_time) % 40

  def update_fps(self):
    self._num_frames += 1
    current_update    = time.time()

    if(current_update - self._last_update > self._fps_update_interval):
      self._fps         = self._num_frames / (current_update - self._last_update)
      self._last_update = current_update
      self._num_frames  = 0
      
  def calibrate_cam(self, from_mem=True, filenames=[]):
    if from_mem:
      self._calibrate.calibrate_camera_from_mem("calibration_data/")
    else:
      images = [cv.LoadImage(file) for file in filenames]
      self._calibrate.calibrate_camera(images, save_data=True)
 

if __name__ == '__main__':
  VisionWrapper().online_feed()

