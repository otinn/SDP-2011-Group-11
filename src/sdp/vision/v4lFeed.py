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

import pyv4l2
import cv 
import time
from ctypes import string_at

class Capture():
  def __init__(self, pipe=None):
    self.pipe = pipe

    (self.width, self.height) = (640,480)
    # Capture settings
    self.device = pyv4l2.Device("/dev/video0")              # Cam is /dev/video0
    self.device.SetInput(2)                                 # Always V4L input 2 (SVIDEO)
    self.device.SetStandard(self.device.standards["PAL"])   # PAL video standard
    self.device.SetField(self.device.fields["Interlaced"]) 	# ???
    self.device.SetPixelFormat("BGR3")                      # 24bit BGR format
    self.device.SetResolution(self.width, self.height)      # 640x480 resolution
    
    # Create output image in OpenCV format
    self.img = cv.CreateImage((self.width, self.height),8,3)

    # Set up buffers
    self.device.MapBuffers(self.device.RequestBuffers(2)) # 2 Buffers used
    self.buff = pyv4l2.Buffer()
    self.buff.type = 1
    self.buff.memory = 1
        
    # Queue buffers:
    for i in xrange(0, len(self.device.buffers)):
      self.buff.index = i
      self.device.QueueBuffer(self.buff)

    # Start streaming
    self.device.StreamOn()

    if pipe:
      self._loop()

  def pull(self):
    """Return an OpenCV format frame from the capture device"""
    self.device.DequeueBuffer(self.buff)
    data = string_at(self.device.buffers[self.buff.index][1],self.device.buffers[self.buff.index][2])
    
    if self.pipe: return data

    cv.SetData(self.img, data)

    self.device.QueueBuffer(self.buff)
    return self.img
  
  def _loop(self):
    while 1:
      if self.pipe.poll():
        if self.pipe.recv() == "quit":
          break
        else:
          self.pipe.send(self.pull())
          self.device.QueueBuffer(self.buff)
        

if __name__ == '__main__':
  cap = Capture()
  while 1:
    frame = cap.pull()
    cv.ShowImage('test-v4l', frame)
    cv.WaitKey(2)


