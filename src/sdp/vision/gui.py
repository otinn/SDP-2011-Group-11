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

import gtk, string, datetime, cv, gobject, yaml

class Gui:
  def __init__(self, events_pipe, locations_pipe, feed_pipe, config, get_shapes_pipe = None, set_shapes_pipe = None):
    self._events_pipe     = events_pipe
    self._locations_pipe  = locations_pipe
    self._feed_pipe       = feed_pipe
    self._get_shapes_pipe = get_shapes_pipe
    self._set_shapes_pipe = set_shapes_pipe
    self._advanced        = self._get_shapes_pipe and self._set_shapes_pipe

    self._pitch = "main"
    
    builder = gtk.Builder()
    builder.add_from_file("control.glade")
    builder.add_from_file("feed.glade")
    if self._advanced: builder.add_from_file("shapes_sizes.glade")

    self._control               = builder.get_object("control")
    self._feed                  = builder.get_object("feed")
    self._shapes                = builder.get_object("shapes_sizes")
    self._show_window_checkbox  = builder.get_object("thresholds_show_window")
    self._file_name             = builder.get_object("save_custom_filename_entry")
    self._we_are_label          = builder.get_object("we_are_colour")
    self._we_are_shooting_label = builder.get_object("we_are_shooting")
    self._thresholds_notebook   = builder.get_object("thresholds_notebook")
    self._feed_image            = builder.get_object("feed_image")
    self._foreground_connected  = builder.get_object("thresholds_foreground_connected")


    self._location = {
      "us" : {
        "x" : builder.get_object("locations_us_x"),
        "y" : builder.get_object("locations_us_y"),
        "r" : builder.get_object("locations_us_r")
      },
      "them" : {
        "x" : builder.get_object("locations_them_x"),
        "y" : builder.get_object("locations_them_y"),
        "r" : builder.get_object("locations_them_r")
      },
      "ball" : {
        "x" : builder.get_object("locations_ball_x"),
        "y" : builder.get_object("locations_ball_y")
      },
      "fps" : {
        "fps" : builder.get_object("locations_fps_fps")
      }
    }

    if self._advanced:
      self._builder = builder

      self._shapes_text = {
        "_pnp_dist_thresh"           : None,
        "_cc_area_thresh"            : None,
        "_max_foreground_obj_thresh" : None,
        "_robot_area_threshold"      : None,
        "_black_dot_area_threshold"  : None,
        "_black_dot_dist_threshold"  : None,
        "_ball_radius_threshold"     : None,
        "_ball_area_threshold"       : None,
        "_plate_area_threshold"      : None,
        "_blob_area_threshold"       : None,
        "_ball_centre"               : ("(%s", ", %s)"),
        "_ball_radius"               : "%s",
        "_ball_roundness_metric"     : "%.3f",
        "_blue_robot_centre"         : ("(%.2f", ", %.2f)"),
        "_blue_robot_black_dot"      : ("(%.2f", ", %.2f)"),
        "_blue_robot_t_area"         : "%s",
        "_blue_plate_area"           : "%s",
        "_yellow_robot_centre"       : ("(%.2f", ", %.2f)"),
        "_yellow_robot_black_dot"    : ("(%.2f", ", %.2f)"),
        "_yellow_robot_t_area"       : "%s",
        "_yellow_plate_area"         : "%s",
        "_offset_top"       : None,
        "_offset_bottom"       : None,
        "_offset_left"       : None,
        "_offset_right"       : None
      }

    self._position_windows()

    self._thresholds_notebook.set_current_page(6)
    
    self._control                              .connect("destroy",           self._close)
    self._feed                                 .connect("destroy",           self._close)
    self._thresholds_notebook                  .connect("switch-page",       self._change_window)
    self._foreground_connected                 .connect("toggled",           self._change_connected)
    self._show_window_checkbox                 .connect("toggled",           self._show_window)
    builder.get_object("game_mode_play")       .connect("clicked",           self._game_mode,                "play")
    builder.get_object("game_mode_take")       .connect("clicked",           self._game_mode,                "kick_penalty")
    builder.get_object("game_mode_defend")     .connect("clicked",           self._game_mode,                "defend_penalty")
    builder.get_object("game_mode_wait")       .connect("clicked",           self._game_mode,                "wait")
    builder.get_object("we_are_blue")          .connect("toggled",           self._our_colour,               "blue")
    builder.get_object("we_are_yellow")        .connect("toggled",           self._our_colour,               "yellow")
    builder.get_object("we_are_shooting_left") .connect("toggled",           self._shooting_direction,       "left")
    builder.get_object("we_are_shooting_right").connect("toggled",           self._shooting_direction,       "right")
    builder.get_object("save_button")          .connect("clicked",           self._save)
    builder.get_object("thresholds_file_save") .connect("clicked",           self._save_file)
    builder.get_object("thresholds_file_load") .connect("selection-changed", self._load_file)

    builder.get_object("_ball_area_threshold0").set_property('width-request', 200)

    if self._advanced:
      self._shapes                               .connect("destroy",           self._close)
      temp = [
        "_pnp_dist_thresh",
        "_robot_area_threshold0"      ,
        "_robot_area_threshold1"      ,
        "_black_dot_area_threshold0"  ,
        "_black_dot_area_threshold1"  ,
        "_black_dot_dist_threshold0"  ,
        "_black_dot_dist_threshold1"  ,
        "_ball_area_threshold0"       ,
        "_ball_area_threshold1"       ,
        "_plate_area_threshold0"      ,
        "_plate_area_threshold1"      ,
        "_blob_area_threshold0"       ,
        "_blob_area_threshold1"       ,
        "_max_foreground_obj_thresh"  ,
        "_cc_area_thresh"             ,
        "_offset_bottom"              ,
        "_offset_top"                 ,
        "_offset_left"                ,
        "_offset_right"
      ]
      for obj in temp:
        builder.get_object(obj).connect("value-changed", self._change_shape, obj)

    self._config = config
    
    self._col = ["blue", "yellow", "black", "red", "green"]
    self._hsv = ["hue", "saturation", "value"]
    self._m   = ["min", "max"]

    self._thresholds = {}
    for col in self._col:
      self._thresholds[col] = {}
      self._thresholds[col]["inverse"] = builder.get_object("thresholds_%s_inverse" % col)
      self._thresholds[col]["inverse"].connect("toggled", self._thresholds_invert, col)
      for hsv in self._hsv:
        self._thresholds[col][hsv] = {}
        for m in self._m:
          self._thresholds[col][hsv][m] = builder.get_object("thresholds_%s_%s_%s" % (col, hsv, m))
          self._thresholds[col][hsv][m].set_value(255)
          self._thresholds[col][hsv][m].connect("value-changed", self._change_threshold, col, hsv, m)
      manual = builder.get_object("thresholds_%s_manual" % col)
      manual.connect("toggled", self._enable_manual_thresholds, col)
      manual.set_active(False)
    for col in self._col:
      for hsv in self._hsv:
        for m in self._m:
          self._thresholds[col][hsv][m].set_value(self._config["colours"][col]["%s_hsv" % m][self._hsv.index(hsv)])
    
    self._control.show()
    self._feed   .show()
    if self._advanced: self._shapes .show()

    gobject.io_add_watch(self._locations_pipe , gobject.IO_IN, self._update_locations)
    gobject.io_add_watch(self._feed_pipe      , gobject.IO_IN, self._update_image)
    if self._advanced: gobject.io_add_watch(self._get_shapes_pipe, gobject.IO_IN, self._shapes_values)
    gtk.main()
  
  def _position_windows(self, x = 0, y = 0, pad = 30):
    if self._advanced:
      self._shapes.resize(2000, 1)
      self._shapes.move(0,2000)
    cx, cy = self._control.get_size()
    self._control.move(           x,            y)
    self._feed   .move(cx + pad + x,            y)

  # If you are expecting a response, just use _send() and then while not received keep checking _pipe.poll()
  # This is very rudimentary and would not work with threading, but we are not using threading
  def _send(self, msg, *args):
    self._events_pipe.send((msg, args))
  
  # Event handlers
  def _close(self, window):
    if window is self._feed:
      builder = gtk.Builder()
      builder.add_from_file("feed.glade")
      self._feed = builder.get_object("feed")
      self._feed.set_position(gtk.WIN_POS_NONE)
      self._feed.connect("destroy", self._close)
      self._feed_image = builder.get_object("feed_image")
      self._show_window_checkbox.set_active(False)
    else:
      self._send("quit")
      self._control.destroy()
      self._feed   .destroy()
      if self._advanced: self._shapes.destroy()
  
  def _change_window(self, notebook, page, page_num):
    window = {
      "Blue"       : "threshed_blue",
      "Yellow"     : "threshed_yellow",
      "Black"      : "threshed_black",
      "Red"        : "threshed_red",
      "Green"      : "threshed_green",
      "Foreground" : "foreground",
      "Frame"      : "source"
    }[notebook.get_tab_label(notebook.get_nth_page(page_num)).get_label()]
    if window == "foreground" and self._foreground_connected.get_active():
      window += "_connected"
    self._send("change_window", window)

  def _change_connected(self, checkbox):
    connected = "_connected" if checkbox.get_active() else ""
    self._send("change_window", "foreground%s" % connected)
  
  def _show_window(self, checkbox):
    show = checkbox.get_active()
    self._thresholds_notebook.set_sensitive(show)
    self._send("show_window", show)
    if show:
      xpos, ypos = self._control.get_position()
      xsiz, ysiz = self._control.get_size()
      self._feed.move(xpos + xsiz + 10, ypos)
      self._feed.show()
    else:
      self._feed.hide()
  
  def _enable_manual_thresholds(self, checkbox, colour):
    enabled = checkbox.get_active()
    self._thresholds[colour]["inverse"].set_sensitive(enabled)
    for hsv in self._hsv:
      for m in self._m:
        slider = self._thresholds[colour][hsv][m]
        slider.set_sensitive(enabled)
        if not enabled:
          # Set the value to 0/255 accordingly first so min always <= max
          slider.set_value({ "min" : 0, "max" : 255 }[m])
          # Set the value to defaults as defined in self._config
          slider.set_value(self._config["colours"][colour]["%s_hsv" % m][self._hsv.index(hsv)])
  
  def _game_mode(self, button, mode):
    self._send("game_mode", mode)
  
  def _our_colour(self, radiobutton, colour):
    if radiobutton.get_active():
      self._we_are_label.set_alignment(0.50, {"blue":0.00, "yellow":1.00}[colour])
      self._send("our_colour", colour)
  
  def _shooting_direction(self, radiobutton, direction):
    if radiobutton.get_active():
      self._we_are_shooting_label.set_alignment(0.50, {"left":0.00, "right":1.00}[direction])
      self._send("shooting_direction", direction)
  
  def _save(self, *args):
    custom = string.strip(self._file_name.get_text()) 
    if(custom):
      name = custom
    else:
      name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    self._send("save_as", name)
  
  def _change_threshold(self, slider, colour, hsv, m):
    other = self._thresholds[colour][hsv][{"max" : "min", "min" : "max"}[m]]

    v1 = slider.get_value()
    v2 = other .get_value()
    if {"max" : v2 > v1, "min" : v2 < v1}[m]:
      slider.set_value(v2)

    self._send(
      "set_hsv_values",
      int(self._thresholds[colour]["hue"       ][m].get_value()),
      int(self._thresholds[colour]["saturation"][m].get_value()),
      int(self._thresholds[colour]["value"     ][m].get_value()),
      colour,
      m
    )

  def _update_locations(self, *args):
    while self._locations_pipe.poll():
      recv = self._locations_pipe.recv()
      if recv == "quit":
        gtk.main_quit()
        return False
      elif recv[0] == "pitch":
        self._pitch = recv[1]
      else:
        who, xyr, val = recv
        val = round(val,2) if xyr in ["r"] else int(val)
        self._location[who][xyr].set_label("%s: %s" % (xyr.upper(), str(val)))
    return True

  def _update_image(self, *args):
    while self._feed_pipe.poll():
      self._feed_image.set_from_pixbuf(gtk.gdk.pixbuf_new_from_data(*self._feed_pipe.recv()))
    return True

  def _thresholds_invert(self, checkbox, col):
    self._send("threhsolds_invert", col, checkbox.get_active())
  
  def _load_file(self, filechooser):
    self._config = yaml.load(file(filechooser.get_filename(), 'r'))
    for col in self._col:
      for hsv in self._hsv:
        for m in self._m:
          self._thresholds[col][hsv][m].set_value(self._config["colours"][col]["%s_hsv" % m][self._hsv.index(hsv)])
    if self._advanced:
      temp = {
        "robot_area_threshold"      : self._config['physical_thresholds']['robot_area'],
        "black_dot_area_threshold"  : self._config['physical_thresholds']['black_dot_area'],
        "black_dot_dist_threshold"  : self._config['physical_thresholds']['black_dot_dist'],
        "ball_area_threshold"       : self._config['physical_thresholds']['ball_area'],
        "plate_area_threshold"      : self._config['physical_thresholds']['plate_area'],
        "blob_area_threshold"       : self._config['physical_thresholds']['blob_area']
      }
      for t in temp:
        for i in range(len(temp[t])):
          self._builder.get_object("_"+t+str(i)).set_value(float(temp[t][i]))
      temp = {
        "pnp_dist_thresh"           : self._config['physical_thresholds']['pnp_dist'],
        "cc_area_thresh"            : self._config['physical_thresholds']['cc_area'],
        "max_foreground_obj_thresh" : self._config['physical_thresholds']['max_foreground_obj']
      }
      for t in temp:
        self._builder.get_object("_"+t).set_value(float(temp[t]))


  def _save_file(self, button):
    for col in self._col:
      for hsv in self._hsv:
        for m in self._m:
          self._config["colours"][col]["%s_hsv" % m][self._hsv.index(hsv)] = self._thresholds[col][hsv][m].get_value()
    if self._advanced:
      for i in ["robot_area", "black_dot_area", "black_dot_dist", "ball_area", "plate_area", "blob_area"]:
        self._config['physical_thresholds'][i] = (
          self._builder.get_object("_"+i+"_threshold0").get_value(),
          self._builder.get_object("_"+i+"_threshold1").get_value()
        )
      for i in ["pnp_dist", "cc_area", "max_foreground_obj"]:
        self._config['physical_thresholds'][i] = self._builder.get_object("_"+i+"_thresh").get_value()
      self._config['physical_thresholds']["max_foreground_obj"] = int(self._config['physical_thresholds']["max_foreground_obj"])
    f = file("config/%s_%s_pitch.yaml" % (datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f"), self._pitch), "w")
    f.write(yaml.dump(self._config))
    f.close()

  def _shapes_values(self, *args):
    while self._get_shapes_pipe.poll():
      var, val = self._get_shapes_pipe.recv()
      if val is not None:
        if val.__class__ == tuple and val[0] is not None:
          for i in range(len(val)):
            if self._shapes_text[var] is not None:
              self._builder.get_object(var+str(i)).set_label(self._shapes_text[var][i] % val[i])
            else:
              self._builder.get_object(var+str(i)).set_value(float(val[i]))
        else:
          if self._shapes_text[var] is not None:
            self._builder.get_object(var).set_label(self._shapes_text[var] % val)
          else:
            self._builder.get_object(var).set_value(float(val))
    return True

  def _change_shape(self, slider, *args):
    self._set_shapes_pipe.send((args[0],slider.get_value()))

if __name__ == "__main__":
  print "Please run startgui.py instead"
