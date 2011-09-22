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

from vision          import Vision
from visioncom       import VisionCom
from calibrate       import Calibrate
from datetime        import datetime
from multiprocessing import Pipe, Process
from v4lFeed         import Capture
from sys             import stdout
import cv, time, gui, gtk, yaml

class StartGui:
  def __init__(self, avg_bg_frames = 30, online = True, main = True, advanced = False, config = "config/020311-0830-secondary_pitch.yaml"):
    # Set up vision, visioncom
    calibrate           = Calibrate((9,6))
    calibrate.calibrate_camera_from_mem("calibration_data/")
    self._config        = yaml.load(file(config, 'r'))
    self._offline_img   = cv.LoadImage("b02.jpg")
    self._vision        = Vision(self._offline_img, calibrate, self._config, fix_distortions = True, main_pitch = main)
    self._visioncom     = VisionCom(self._vision)

    self._capture_pipe, capture_pipe = Pipe()
    self._capture       = Process(target=Capture, args = (capture_pipe,))
    self._capture.start()

    self._fps_then    = 0
    self._fps_frames  = 0
    self._fps         = 0
    self._base_time   = 0

    self._advanced = advanced

    self._online = online
    if self._online:
      if avg_bg_frames:
        frames = []
        for i in range(avg_bg_frames):
          frames.append(self.get_frame())
        self._vision.avg_bg_frames(frames)

    # Set up GUI and start process
    self._events_pipe    , events_pipe           = Pipe(False)
    set_shapes_pipe, get_shapes_pipe = False, False
    if advanced:
      self._set_shapes_pipe, set_shapes_pipe       = Pipe(False)
      get_shapes_pipe      , self._get_shapes_pipe = Pipe(False)
    feed_pipe            , self._feed_pipe       = Pipe(False)
    locations_pipe       , self._locations_pipe  = Pipe(False)

    self._gui_process = Process(target = gui.Gui, args = (events_pipe, locations_pipe, feed_pipe, self._config, get_shapes_pipe, set_shapes_pipe))
    self._gui_process.start()

    self._locations_pipe.send(("pitch",{True:"main",False:"other"}[main]))

    self._window      = "source"
    self._our_colour  = "blue"
    self._show_window = True
    self._run         = True
    self._loop()

  def get_frame(self):
    self._capture_pipe.send("")
    while not self._capture_pipe.poll():
      pass
    data = self._capture_pipe.recv()
    frame = cv.CreateImage((640,480),8,3)
    cv.SetData(frame, data)
    return frame
  
  def _loop(self):
    last_base_time = 0
    time_interval  = 60
    while self._run:
      lstart = time.time()
      if lstart - last_base_time >= time_interval:
        self.calc_baseline()
        last_base_time = time.time()
      
      # Update feed and locations
      self._current_frame = self.get_frame() if self._online else cv.CloneImage(self._offline_img)
      self._vision.update(self._current_frame)
      

      timestamp = datetime.fromtimestamp(self.correct_timestamp() / 1000.0).strftime('%Y-%m-%dT%H:%M:%S.%f')
      
      self._visioncom.transmit(timestamp)
      self._calc_fps()
      self._locations_pipe.send(("fps", "fps", self._fps))
      self._src_frame = self._vision.get_frame(self._window)
      if self._show_window:
        if self._src_frame:
          frame = cv.CreateImage(cv.GetSize(self._src_frame),8,3)
          if self._window == "source":
            cv.CvtColor(self._src_frame, frame, cv.CV_BGR2RGB)
          else:
            cv.CvtColor(self._src_frame, frame, cv.CV_GRAY2RGB)
          pixbuf = (
            frame.tostring(),
            gtk.gdk.COLORSPACE_RGB,
            False,
            8,
            frame.width,
            frame.height, 
            frame.width * frame.nChannels
          )
          self._feed_pipe.send(pixbuf)
      ball = self._vision.get_ball()
      if ball:
        self._locations_pipe.send(("ball", "x", ball[0][0]))
        self._locations_pipe.send(("ball", "y", ball[0][1]))
      (our_centre, our_rotation) = self._vision.get_robot(self._our_colour)
      if our_centre:
        self._locations_pipe.send(("us", "x", our_centre[0]))
        self._locations_pipe.send(("us", "y", our_centre[1]))
      if our_rotation:
        self._locations_pipe.send(("us", "r", our_rotation))
      their_colour = {"blue":"yellow", "yellow":"blue"}[self._our_colour]
      (their_centre, their_rotation) = self._vision.get_robot(their_colour)
      if their_centre:
        self._locations_pipe.send(("them", "x", their_centre[0]))
        self._locations_pipe.send(("them", "y", their_centre[1]))
      if their_rotation:
        self._locations_pipe.send(("them", "r", their_rotation))

      # Shapes and sizes
      if self._advanced:
        vals = [
          "_pnp_dist_thresh",
          "_cc_area_thresh",
          "_max_foreground_obj_thresh",
          "_robot_area_threshold",
          "_black_dot_area_threshold",
          "_black_dot_dist_threshold",
          "_ball_area_threshold",
          "_plate_area_threshold",
          "_blob_area_threshold",
          "_pnp_dist_thresh",
          "_ball_centre",
          "_ball_radius",
          "_ball_roundness_metric",
          "_blue_robot_centre",
          "_blue_robot_t_area",
          "_blue_plate_area",
          "_yellow_robot_centre",
          "_yellow_robot_t_area",
          "_yellow_plate_area",
          "_offset_bottom"              ,
          "_offset_top"                 ,
          "_offset_left"                ,
          "_offset_right"
        ]
        while self._set_shapes_pipe.poll():
          var, val = self._set_shapes_pipe.recv()
          if var == "_max_foreground_obj_thresh": val = int(val)
          if var == "_offset_bottom": val = int(val)
          if var == "_offset_top": val = int(val)
          if var == "_offset_left": val = int(val)
          if var == "_offset_right": val = int(val)
          if var[-1] not in ["0","1"]:
            setattr(self._vision, var, val)
          else:
            tup = getattr(self._vision, var[:-1])
            temp = (val, tup[1]) if var[-1] == "0" else (tup[0], val)
            setattr(self._vision, var[:-1], temp)
        for val in vals:
          self._get_shapes_pipe.send((val, getattr(self._vision, val)))

        vals = [
          "_blue_robot_black_dot",
          "_yellow_robot_black_dot"
        ]
        for val in vals:
          temp = getattr(self._vision, val)
          if temp is not None:
            self._get_shapes_pipe.send((val, temp[0]))

      # Handle Events
      while self._events_pipe.poll():
        m,a = self._events_pipe.recv()
        if m == "quit":
          self._run = False
        elif m == "change_window":
          self._window = a[0]
        elif m == "show_window":
          self._show_window = a[0]
        elif m == "game_mode":
          print "/general/state/" + a[0]
          stdout.flush()
        elif m == "our_colour":
          self._our_colour        = a[0]
          self._visioncom._colour = a[0]
        elif m == "shooting_direction":
          self._visioncom._side = a[0]
        elif m == "save_as":
          cv.SaveImage("%s.jpg" % a[0], self._current_frame)
        elif m == "set_hsv_values":
          self._vision.set_hsv_values(*a)
        elif m == "thresholds_invert":
          break
          # TODO Invert thresholds

    self._locations_pipe.send("quit")
  
  def _calc_fps(self):
    self._fps_frames += 1
    now = time.time()
    if(now - self._fps_then > 0.5):
      self._fps        = self._fps_frames / (now - self._fps_then)
      self._fps_then   = now
      self._fps_frames = 0
      
  def calc_baseline(self):
    for i in range(3):
      self.get_frame()
    self._base_time = int(round(time.time() * 1000))

  def correct_timestamp(self):
    t = int(round(time.time() * 1000))
    return t - (t - self._base_time) % 40

if __name__ == "__main__":
  from sys import argv as args
  avg_bg_frames = 30
  online        = True
  main          = True
  advanced      = False
  for arg in args:
    try:
      avg_bg_frames = int(arg)
    except ValueError:
      if arg == "offline":
        online = False
      elif arg == "other":
        main = False
      elif arg == "advanced":
        advanced = True
  StartGui(avg_bg_frames, online, main, advanced)
