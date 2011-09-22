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

from visionutil          import AngleStabilizer
from backgroundaveraging import BackgroundAveraging
from math                import sqrt, pi, atan2, degrees
from visionutil          import *
import threading
import cv
import datetime

class Vision():
  def __init__(self, bg, calibrate, config, fix_distortions=True, main_pitch=False, corners_from_mem=False):
    self._bg                 = bg
    self._corners_from_mem   = corners_from_mem
    self._frame              = None
    self._frme_hsv           = None
    self._foreground         = None
    self._annotated_mask     = None
    self._frame_dim          = None
    self._im_threshed_red    = None
    self._im_threshed_yellow = None
    self._im_threshed_blue   = None
    self._im_threshed_green  = None
    self._im_threshed_black  = None
    
    self._ba              = None    
    self._calibrate       = calibrate
    self._fix_distortions = fix_distortions
    self._main_pitch      = main_pitch
    
    # Load colours default threshold values.
    try:
      colours = config['colours']
      (self._red_colour_min_hsv, self._red_colour_max_hsv, self._red_colour_inv_hsv) = self.__load_colour('red', colours)
      (self._yellow_colour_min_hsv, self._yellow_colour_max_hsv, self._yellow_colour_inv_hsv) = self.__load_colour('yellow', colours)
      (self._blue_colour_min_hsv, self._blue_colour_max_hsv, self._blue_colour_inv_hsv) = self.__load_colour('blue', colours)
      (self._black_colour_min_hsv, self._black_colour_max_hsv, self._black_dot_colour_inv_hsv) = self.__load_colour('black', colours)
      (self._green_colour_min_hsv, self._green_colour_max_hsv, self._green_colour_inv_hsv) = self.__load_colour('green', colours)
    except:
      print 'incomlete config hashmap'
      exit()

    try:
      # TODO Add AngleStabilizer thresholds.
      self._robot_area_threshold      = config['physical_thresholds']['robot_area']
      self._black_dot_area_threshold  = config['physical_thresholds']['black_dot_area']
      self._black_dot_dist_threshold  = config['physical_thresholds']['black_dot_dist']
      self._ball_radius_threshold     = config['physical_thresholds']['ball_radius']
      self._ball_area_threshold       = config['physical_thresholds']['ball_area']
      self._plate_area_threshold      = config['physical_thresholds']['plate_area']
      self._blob_area_threshold       = config['physical_thresholds']['blob_area']
      self._pnp_dist_thresh           = config['physical_thresholds']['pnp_dist']
      self._cc_area_thresh            = config['physical_thresholds']['cc_area']
      self._max_foreground_obj_thresh = config['physical_thresholds']['max_foreground_obj']
      (self._offset_top, self._offset_bottom, self._offset_left, self._offset_right) = config['physical_thresholds']['offsets']
    except:
      print 'incomlete config hashmap'
      exit()
    
    self._abs_diff_thresh = 30 if self._main_pitch else 20
    self._ball_centre      = None
    self._ball_radius      = None
    
    # consider initialising angle depending on starting location.
    self._yellow_robot_centre    = None
    self._yellow_robot_black_dot = None
    self._yellow_robot_t_contour = None 
    self._yellow_robot_as        = AngleStabilizer()

    self._blue_robot_centre      = None
    self._blue_robot_black_dot   = None
    self._blue_robot_t_contour   = None
    self._blue_robot_as          = AngleStabilizer()
    
    self._CVX_WHITE = cv.Scalar(255,255,255)
    
    
  def __load_colour(self, colour_name, colours):
    colour = colours.get(colour_name, None)
    if colour:
      return (cv.Scalar(*colour['min_hsv']), cv.Scalar(*colour['max_hsv']), colour['inv_hsv'])
  
  def avg_bg_frames(self, frames, load_from_mem=False):
    if load_from_mem:
      self._ba = BackgroundAveraging(frames[i])
      self._ba.load_bg_model()
      return;
    
    for i in xrange(len(frames)):
      frames[i] = self._calibrate.undist_fisheye(frames[i])
      frames[i] = self._calibrate.crop_frame(frames[i])
      frames[i] = self._calibrate.undist_perspective(frames[i], corners_from_mem=self._corners_from_mem)
            
      if i == 0: self._ba = BackgroundAveraging(frames[i])
      self._ba.accumulate_background(frames[i])
    self._ba.create_models_from_stats()
  
  def update(self, frame):
    self._frame                       = frame
    
    self._foreground                  = None
    self._foreground_connected        = None
    self._annotated_mask              = None
    self._im_threshed_red             = None
    self._im_threshed_yellow          = None
    self._im_threshed_blue            = None
    self._im_threshed_green           = None
    self._im_threshed_black           = None
                                      
    self._prev_ball_centre            = self._ball_centre
    self._ball_centre                 = None
    self._ball_radius                 = None
    self._ball_roundness_metric       = None
                                      
    self._prev_yellow_robot_centre    = self._yellow_robot_centre
    self._yellow_robot_centre         = None
    self._prev_yellow_robot_black_dot = self._yellow_robot_black_dot
    self._yellow_robot_black_dot      = None
    self._yellow_robot_t_contour      = None 
    self._yellow_robot_t_area         = None
    self._yellow_plate_area           = None
                                      
    self._prev_blue_robot_centre      = self._blue_robot_centre
    self._blue_robot_centre           = None
    self._prev_blue_robot_black_dot   = self._blue_robot_black_dot
    self._blue_robot_black_dot        = None
    self._blue_robot_t_contour        = None
    self._blue_robot_t_area           = None    
    self._blue_plate_area             = None
    
    if self._fix_distortions:
      self._frame = self._calibrate.undist_fisheye(self._frame)
      self._frame = self._calibrate.crop_frame(self._frame)
      self._frame = self._calibrate.undist_perspective(self._frame, corners_from_mem=self._corners_from_mem)
    
    self._frame_dim = cv.GetSize(self._frame)
    self._annotated_mask = cv.CreateImage(self._frame_dim, 8, 3)
    cv.XorS(self._annotated_mask, self._CVX_WHITE, self._annotated_mask)    
    
    self._frame_hsv                   = cv.CreateImage(self._frame_dim,8,3)
    cv.CvtColor(self._frame, self._frame_hsv, cv.CV_BGR2HSV)
    
    self.find_ball(self._frame_hsv)
    cont = self.retrieve_foreground_contours()
    self.classify_contours(cont)
  
  
  def get_frame(self, name='source', annotated=True):
    """
    name [optional] - the image name. can be chosen from:
      bg, source, foreground
    """
    
    if name == 'bg':
      output_image = cv.CreateImage(self._frame_dim, 8, 3)
      
      if annotated:
        output_image = cv.CloneImage(self._bg)
        self.draw_circle(output_image, self._ball_centre, self._ball_radius, colour=cv.CV_RGB(0,255,0))
        self.draw_plate(output_image, self._blue_robot_t_contour, self._blue_robot_black_dot, self._blue_robot_centre, colour=cv.CV_RGB(0,0,255))
        self.draw_plate(output_image, self._yellow_robot_t_contour, self._yellow_robot_black_dot, self._yellow_robot_centre, colour=cv.CV_RGB(0,255,0))
      else: output_image = self._bg
      
      return output_image
      
    elif name == 'source':
      output_image = cv.CreateImage(self._frame_dim, 8, 3)
      
      if annotated:
        cv.Line(self._frame, (self._offset_left,0), (self._offset_left, int(self._frame_dim[1])), cv.CV_RGB(0,255,255), 1)
        cv.Line(self._frame, (int(self._frame_dim[0])-self._offset_right,0), (int(self._frame_dim[0])-self._offset_right, int(self._frame_dim[1])), cv.CV_RGB(0,255,255), 1)
        cv.Line(self._frame, (0,self._offset_top), (int(self._frame_dim[0]), self._offset_top), cv.CV_RGB(0,255,255), 1)
        cv.Line(self._frame, (0,int(self._frame_dim[1])-self._offset_bottom), (int(self._frame_dim[0]), int(self._frame_dim[1])-self._offset_bottom), cv.CV_RGB(0,255,255), 1)
        #if self._ball_centre:
        #  dcentre = self.correct_height_dist(self._ball_centre[0], self._ball_centre[1])
        #  cv.Line(self._frame, (cv.Round(dcentre[0]), cv.Round(dcentre[1])), (cv.Round(dcentre[0]), cv.Round(dcentre[1])), cv.CV_RGB(0,255,255), 9)
        # 
        #if self._blue_robot_centre:
        #  dcentre = self.correct_height_dist(self._blue_robot_centre[0], self._blue_robot_centre[1])
        #  cv.Line(self._frame, (cv.Round(dcentre[0]), cv.Round(dcentre[1])), (cv.Round(dcentre[0]), cv.Round(dcentre[1])), cv.CV_RGB(255,0,0), 9)
        output_image = cv.CloneImage(self._frame)

        self.draw_circle(output_image, self._ball_centre, self._ball_radius, colour=cv.CV_RGB(0,255,0))
        self.draw_plate(output_image, self._blue_robot_t_contour, self._blue_robot_black_dot, self._blue_robot_centre, colour=cv.CV_RGB(255,255,0))
        self.draw_plate(output_image, self._yellow_robot_t_contour, self._yellow_robot_black_dot, self._yellow_robot_centre, colour=cv.CV_RGB(0,0,255))
      else: output_image = self._frame
      
      return output_image
    elif name == 'threshed_red': return self._im_threshed_red
    elif name == 'threshed_yellow':
      im_threshed = cv.CreateImage(self._frame_dim,8,1)
      cv.InRangeS(self._frame_hsv, self._yellow_colour_min_hsv, self._yellow_colour_max_hsv, im_threshed)
      return im_threshed
    elif name == 'threshed_blue':
      im_threshed = cv.CreateImage(self._frame_dim,8,1)
      cv.InRangeS(self._frame_hsv, self._blue_colour_min_hsv, self._blue_colour_max_hsv, im_threshed)
      return im_threshed
    elif name == 'threshed_black':
      im_threshed = cv.CreateImage(self._frame_dim,8,1)
      cv.InRangeS(self._frame_hsv, self._black_colour_min_hsv, self._black_colour_max_hsv, im_threshed)
      return im_threshed
    elif name == 'threshed_green':
      im_threshed = cv.CreateImage(self._frame_dim,8,1)
      cv.InRangeS(self._frame_hsv, self._green_colour_min_hsv, self._green_colour_max_hsv, im_threshed)
      return im_threshed
    elif name == 'foreground': return self._foreground
    elif name == 'foreground_connected': return self._foreground_connected
  
  def correct_height_dist(self, x, y):
    (width,height) = (self._frame_dim[0] / 2.0, self._frame_dim[1] / 2.0) 
    return (width + ((x - width)*self._pnp_dist_thresh), height + ((y - height)*self._pnp_dist_thresh)) 
     
  def convert_xy(self, xy):
    (pitch_width, pitch_height)                            = (244, 122)
    (x, y)                                                 = (xy[0], xy[1])
    
    x = (x - self._offset_left) / 1.0 / (self._frame_dim[0] - self._offset_left - self._offset_right) * pitch_width
    y = (y - self._offset_top) / 1.0 / (self._frame_dim[1] - self._offset_top - self._offset_bottom) * pitch_height
    return (x, pitch_height - y)
  
  def __ball_found(self):
    return self._ball_centre is not None and self._ball_radius is not None
  
  def ___robot_found(self, colour='blue'):
    if colour == 'blue':     return self._blue_robot_centre is not None
    elif colour == 'yellow': return self._yellow_robot_centre is not None
  
  def get_ball(self):
    """
    The following function returns the current location of the ball.
    """
    if self.__ball_found(): return (self.convert_xy(self._ball_centre), self._ball_radius)
    else:                   return None
    
  def get_robot(self, colour='blue'): # (blue | yellow)
    """
    Given a robot colour, returns a tuple where the first element is the centre
    of the robot while the second element is the robot's angle.  
    """
    if colour == 'blue' and self.___robot_found(colour='blue'):
      return (self.convert_xy(self.correct_height_dist(*self._blue_robot_centre)), self._blue_robot_as.get())
    elif colour == 'yellow' and self.___robot_found(colour='yellow'):
      return (self.convert_xy(self.correct_height_dist(*self._yellow_robot_centre)), self._yellow_robot_as.get())
    else: return (None,None)

  def is_round(self, blob, threshold):
    """
    The method estimates the perimeter of a given blob and makes an educated guess
    on how round is the object.

    Since we know that the perimeter of a circle is given by: 
    Perimeter = 2 * Pi * Radius

    And that the Area of a circle is given by:
    Area = Pi * Radios^2

    Combining the two formulas we get:
    Perimeter^2 = 2^2 * Pi^2 * Radios^2
    Perimeter^2 = 4 * Pi * Area
    1 = (4 * Pi * Area) / Perimeter^2

    That said, this formula designed for perfect circle. As we are usually working
    with pixelated, noisy, and fragmentary images we would use the last formula
    as a metric of how round is an object as opposed to whether it is round or 
    not.
    """
    area = cv.ContourArea(blob)
    perimeter = sum([euclidean_distance(blob[i - 1], blob[i]) for i in xrange(1, len(blob))])
    metric = 4 * pi * area / (perimeter * perimeter)

    if(metric > threshold):
      (a, center, radius) = cv.MinEnclosingCircle(blob)
      return ((cv.Round(center[0]), cv.Round(center[1])), cv.Round(radius), metric)
    else: return None
  
  def retrieve_foreground_contours(self):
    if self._ba is None:
      foreground = cv.CreateImage(self._frame_dim,8,3)
      cv.AbsDiff(self._frame, self._bg, foreground)
    
      foreground_gray = cv.CreateImage(self._frame_dim, 8, 1)
      cv.CvtColor(foreground, foreground_gray, cv.CV_RGB2GRAY)
    
      self._foreground = cv.CreateImage(self._frame_dim, 8, 3)
      cv.CvtColor(foreground_gray, self._foreground, cv.CV_GRAY2BGR)
    
      # Threshold the image
      foreground_bw = cv.CreateImage(self._frame_dim, 8, 1)
      cv.Threshold(foreground_gray, foreground_bw, self._abs_diff_thresh, 255, cv.CV_THRESH_BINARY)

      # Preform morphology operations in order to clean the thresholded image.
      tmp = cv.CreateImage(self._frame_dim, 8, 1)
      element = cv.CreateStructuringElementEx(3,3,1,1,cv.CV_SHAPE_RECT)
      cv.MorphologyEx(foreground_bw, foreground_bw, tmp, element , cv.CV_MOP_CLOSE, 3)
    else:
      foreground_bw = cv.CreateImage(self._frame_dim,8,1)
      self._ba.background_diff(self._frame, foreground_bw)
      self._foreground = cv.CloneImage(foreground_bw)
      self._ba.connect_components(foreground_bw, area_threshold=self._cc_area_thresh)
      self._foreground_connected = cv.CloneImage(foreground_bw)
      
    # Find the blobs in the thresholded image. 
    storage = cv.CreateMemStorage(0)
    contours = cv.FindContours(foreground_bw, storage, cv.CV_RETR_EXTERNAL, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))

    return contours
    
  def classify_contours(self, contours):
    found_ball         = False
    found_blue_robot   = False
    found_yellow_robot = False
    
    contourList = sorted(list(contour_iterator(contours)), key=lambda blob: cv.ContourArea(blob), reverse=True)
    if not contourList: return False
    
    for blob in contourList[:self._max_foreground_obj_thresh]:
      if len(blob) >= 6 and (cv.ContourArea(blob) >= self._blob_area_threshold[0] and cv.ContourArea(blob) <= self._blob_area_threshold[1]):          
        blobHSV = cv.CreateImage(self._frame_dim,8,3)
        
        (a, centre, radius) = cv.MinEnclosingCircle(blob)
        self.draw_circle(blobHSV, centre, int(radius*2), colour=self._CVX_WHITE, filled=True)
        cv.And(blobHSV, self._frame_hsv, blobHSV)

        if not found_yellow_robot:
          found_yellow_robot = self.find_robot(blobHSV, colour='yellow')
        if not found_blue_robot:
          found_blue_robot   = self.find_robot(blobHSV, colour='blue')
          
    if not found_yellow_robot:
      self._yellow_robot_centre    = None
      self._yellow_robot_black_dot = None
      self._yellow_robot_t_contour = None 
    if not found_blue_robot:
      self._blue_robot_centre      = None
      self._blue_robot_black_dot   = None
      self._blue_robot_t_contour   = None
        
  def morphologycal_cleaning(self, imbw):
    imbw_clean = cv.CreateImage(self._frame_dim,8,1)
    tmp = cv.CreateImage(self._frame_dim,8,1)
    element = cv.CreateStructuringElementEx(3,3,1,1,cv.CV_SHAPE_ELLIPSE)
    cv.MorphologyEx(imbw, imbw_clean, tmp, element , cv.CV_MOP_CLOSE, 2)
    cv.MorphologyEx(imbw_clean, imbw_clean, tmp, element , cv.CV_MOP_OPEN, 1)
    return imbw_clean
  
  def find_robot(self, imblob_hsv, colour='blue'):
    blobThreshed = cv.CreateImage(self._frame_dim,8,1)
    
    if colour == 'blue':
      cv.InRangeS(imblob_hsv, self._blue_colour_min_hsv, self._blue_colour_max_hsv, blobThreshed)
      blobThreshed02 = self.morphologycal_cleaning(blobThreshed)
      if self._blue_colour_inv_hsv: cv.XorS(blobThreshed02, self._CVX_WHITE, blobThreshed02)
      self._im_threshed_blue = cv.CloneImage(blobThreshed02)
            
    elif colour == 'yellow': 
      cv.InRangeS(imblob_hsv, self._yellow_colour_min_hsv, self._yellow_colour_max_hsv, blobThreshed)
      blobThreshed02 = self.morphologycal_cleaning(blobThreshed)  
      if self._yellow_colour_inv_hsv: cv.XorS(blobThreshed02, self._CVX_WHITE, blobThreshed02)
      self._im_threshed_yellow = cv.CloneImage(blobThreshed02)
      
    storage = cv.CreateMemStorage(0)
    contours = cv.FindContours(blobThreshed02, storage, cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))

    # Return if no robot was found, else sort the blobs by area.
    contourListTs = sorted((blob for blob in list(contour_iterator(contours)) if self._robot_area_threshold[1] >= cv.ContourArea(blob) >= self._robot_area_threshold[0]), reverse=True)
    if not contourListTs: return False
    
    angle = None
    # After we know a 'T' was found we can look for a black circle within the 
    # same blob.
    # TODO change behaviour if black dot wasn't found.
    if colour == 'blue':
      if self._prev_blue_robot_centre:
        self._blue_robot_t_contour = sorted(contourListTs, key=lambda contour: euclidean_distance(self.calc_contour_centre(contour), self._prev_blue_robot_centre))[0]    
      else: self._blue_robot_t_contour = contourListTs[0]
      
      self._blue_robot_t_area = cv.ContourArea(self._blue_robot_t_contour)
      (blue_plate_corners, self._blue_plate_area) = self.find_plate(imblob_hsv)

      if blue_plate_corners is not None:
        (side_a, side_b, angle) = self.find_plate_orientation(blue_plate_corners, self._blue_robot_t_contour)
        
        cv.Line(self._frame, (cv.Round(side_a[0][0]), cv.Round(side_a[0][1])), (cv.Round(side_a[0][0]), cv.Round(side_a[0][1])), cv.CV_RGB(0,255,0), 4)
        cv.Line(self._frame, (cv.Round(side_a[1][0]), cv.Round(side_a[1][1])), (cv.Round(side_a[1][0]), cv.Round(side_a[1][1])), cv.CV_RGB(255,0,0), 4)
        
        cv.Line(self._frame, (cv.Round(side_b[0][0]), cv.Round(side_b[0][1])), (cv.Round(side_b[0][0]), cv.Round(side_b[0][1])), cv.CV_RGB(0,255,0), 4)
        cv.Line(self._frame, (cv.Round(side_b[1][0]), cv.Round(side_b[1][1])), (cv.Round(side_b[1][0]), cv.Round(side_b[1][1])), cv.CV_RGB(255,0,0), 4)
       
      self._blue_robot_centre    = self.calc_contour_centre(self._blue_robot_t_contour)

      black_dot = self.find_black_dot(imblob_hsv, self._blue_robot_centre, 'blue')     

      if (not black_dot) and (angle is not None): self._blue_robot_as.add(angle,  datetime.datetime.now())
      return True
    
    elif colour == 'yellow': 
      if self._prev_yellow_robot_centre:
        self._yellow_robot_t_contour = sorted(contourListTs, key=lambda contour: euclidean_distance(self.calc_contour_centre(contour), self._prev_yellow_robot_centre))[0]    
      else: self._yellow_robot_t_contour = contourListTs[0]
      
      self._yellow_robot_t_area = cv.ContourArea(self._yellow_robot_t_contour)
      (yellow_plate_corners, self._yellow_plate_area) = self.find_plate(imblob_hsv)
      
      if yellow_plate_corners is not None:
        (side_a, side_b, angle) = self.find_plate_orientation(yellow_plate_corners, self._yellow_robot_t_contour)
        
        cv.Line(self._frame, (cv.Round(side_a[0][0]), cv.Round(side_a[0][1])), (cv.Round(side_a[0][0]), cv.Round(side_a[0][1])), cv.CV_RGB(0,255,0), 4)
        cv.Line(self._frame, (cv.Round(side_a[1][0]), cv.Round(side_a[1][1])), (cv.Round(side_a[1][0]), cv.Round(side_a[1][1])), cv.CV_RGB(255,0,0), 4)
        
        cv.Line(self._frame, (cv.Round(side_b[0][0]), cv.Round(side_b[0][1])), (cv.Round(side_b[0][0]), cv.Round(side_b[0][1])), cv.CV_RGB(0,255,0), 4)
        cv.Line(self._frame, (cv.Round(side_b[1][0]), cv.Round(side_b[1][1])), (cv.Round(side_b[1][0]), cv.Round(side_b[1][1])), cv.CV_RGB(255,0,0), 4)
      
      self._yellow_robot_centre    = self.calc_contour_centre(self._yellow_robot_t_contour)
                  
      black_dot = self.find_black_dot(imblob_hsv, self._yellow_robot_centre, 'yellow')    
      
      if (not black_dot) and (angle is not None): self._blue_robot_as.add(angle, datetime.datetime.now())
      return True
  
  def find_plate_orientation(self, plate_corners, t_contour):
    box = cv.MinAreaRect2(t_contour)
    points02 = [(cv.Round(pt[0]), cv.Round(pt[1])) for pt in cv.BoxPoints(box)]
    
    front_pt = min([(sum([euclidean_distance(pt1, pt2) for pt2 in points02]), pt1) for pt1 in plate_corners])
    plate_corners.remove(front_pt[1])
    back_pts = sorted([(euclidean_distance(point, front_pt[1]), point) for point in plate_corners], reverse=True)

    side_a = (front_pt[1], back_pts[1][1])
    side_b = (back_pts[-1][1], back_pts[0][1])
    
    angle = calc_angle(front_pt[1], back_pts[1][1])
    return (side_a, side_b, angle)
  
  def find_plate(self, imblob_hsv):
    thresholded = cv.CreateImage(self._frame_dim,8,1)

    cv.InRangeS(imblob_hsv, self._green_colour_min_hsv, self._green_colour_max_hsv, thresholded)

    tmp = cv.CreateImage(self._frame_dim,8,1)
    element = cv.CreateStructuringElementEx(3,3,1,1,cv.CV_SHAPE_RECT)
    cv.MorphologyEx(thresholded, thresholded, tmp, element , cv.CV_MOP_CLOSE, 1)
    cv.MorphologyEx(thresholded, thresholded, tmp, element , cv.CV_MOP_OPEN, 1)
    
    storage = cv.CreateMemStorage(0)
    contours = cv.FindContours(thresholded, storage, mode=cv.CV_RETR_EXTERNAL, method=cv.CV_CHAIN_APPROX_SIMPLE)

    #convexHullList = [cv.ConvexHull2(contour, storage, cv.CV_CLOCKWISE, 1) for contour in contour_iterator(contours)]
    
    #tmp_im = cv.CreateImage(self._frame_dim, 8, 1)
    #[cv.DrawContours(tmp_im, convex, self._CVX_WHITE, self._CVX_WHITE, -1, cv.CV_FILLED, 8) for convex in convexHullList]
    
    #del contours
    #contours = cv.FindContours(tmp_im, storage, mode=cv.CV_RETR_EXTERNAL, method=cv.CV_CHAIN_APPROX_SIMPLE)

    contourList = sorted((blob for blob in list(contour_iterator(contours)) if cv.ContourArea(blob) > self._plate_area_threshold[0] and cv.ContourArea(blob) < self._plate_area_threshold[1]), reverse=True)
    if contourList == []: return (None,None)

    box = cv.MinAreaRect2(contourList[0])
    points = [(cv.Round(pt[0]), cv.Round(pt[1])) for pt in cv.BoxPoints(box)]
    return (points, cv.ContourArea(contourList[0]))
  
  def find_black_dot(self, imblob_hsv, robot_centre, colour):
    smoothed_img = cv.CreateImage(self._frame_dim,8,3)
    cv.Smooth(imblob_hsv, smoothed_img, smoothtype=cv.CV_GAUSSIAN, param1=5)

    blobThreshed03 = cv.CreateImage(self._frame_dim,8,1)
    cv.InRangeS(smoothed_img, self._black_colour_min_hsv, self._black_colour_max_hsv, blobThreshed03)

    blobThreshed04 = self.morphologycal_cleaning(blobThreshed03)
    
    storage = cv.CreateMemStorage(0)
    contours = cv.FindContours(blobThreshed04, storage, cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE, (0,0))

    contourListCircles = sorted((blob for blob in list(contour_iterator(contours)) if self._black_dot_area_threshold[1] >= cv.ContourArea(blob) >= self._black_dot_area_threshold[0]))
    if not contourListCircles: return False
    
    possible_circles = []
    tmp_plate_circle = None
    for blob in contourListCircles:   
      if len(blob) >= 4:
        tmp_plate_circle = self.is_round(blob, 0.58)
      if tmp_plate_circle is not None: 
        if colour == 'blue':
          if self._black_dot_dist_threshold[1] >= euclidean_distance(tmp_plate_circle[0], self._blue_robot_centre) >= self._black_dot_dist_threshold[0]:
            possible_circles.append(tmp_plate_circle)
        elif colour == 'yellow':
          if self._black_dot_dist_threshold[1] >= euclidean_distance(tmp_plate_circle[0], self._yellow_robot_centre) >= self._black_dot_dist_threshold[0]:
            possible_circles.append(tmp_plate_circle)
    
    if possible_circles != []:      
      if colour == 'blue':
        if self._prev_blue_robot_black_dot is not None:
          possible_circles = sorted(possible_circles, key=lambda circle: euclidean_distance(circle[0], self._prev_blue_robot_black_dot[0])) 
          if possible_circles == []: return False
          self._blue_robot_black_dot = possible_circles[0]
          
          if euclidean_distance(self._blue_robot_black_dot[0], self._prev_blue_robot_black_dot[0]) <= 50.0:
            self._blue_robot_as.add(calc_angle(self._blue_robot_black_dot[0], self._blue_robot_centre), datetime.datetime.now())
        else: 
          self._blue_robot_black_dot = self.best_circle(possible_circles)
          self._blue_robot_as.add(calc_angle(self._blue_robot_black_dot[0], self._blue_robot_centre), datetime.datetime.now())
              
      if colour == 'yellow':
        if self._prev_yellow_robot_black_dot is not None:
          possible_circles = sorted(possible_circles, key=lambda circle: euclidean_distance(circle[0], self._prev_yellow_robot_black_dot[0]))    
          if possible_circles == []: return False
          self._yellow_robot_black_dot = possible_circles[0]

          if euclidean_distance(self._yellow_robot_black_dot[0], self._prev_yellow_robot_black_dot[0]) <= 50.0:
            self._yellow_robot_as.add(calc_angle(self._yellow_robot_black_dot[0], self._yellow_robot_centre), datetime.datetime.now())
        else: 
          self._yellow_robot_black_dot = self.best_circle(possible_circles)
          self._yellow_robot_as.add(calc_angle(self._yellow_robot_black_dot[0], self._yellow_robot_centre), datetime.datetime.now())
          
      return True
    else:
      if colour == 'blue':
        self._blue_robot_black_dot        = None
        return False        
      if colour == 'yellow':
        self._yellow_robot_black_dot      = None
        return False
  
  def best_circle(self, circles):
    return min((abs(1 - i[2]), (i[0], i[1])) for i in circles)[1]
  
  def calc_contour_centre(self, contour):
    """
    Used in order to calculate the location of a robot.
    """
    moments = cv.Moments(contour)
    return (moments.m10 / moments.m00, moments.m01 / moments.m00)
      
  def find_ball(self, frame_hsv):
    imgThreshed = cv.CreateImage(self._frame_dim, 8, 1)
    cv.InRangeS(frame_hsv, self._red_colour_min_hsv, self._red_colour_max_hsv, imgThreshed)
    
    smoothedThreshed = self.morphologycal_cleaning(imgThreshed)
    #smoothedThreshed = cv.CreateImage(self._frame_dim,8,1)
    #cv.Smooth(imgThreshed, smoothedThreshed, smoothtype=cv.CV_GAUSSIAN, param1=5)
    
    self._im_threshed_red = cv.CloneImage(smoothedThreshed)
    
    storage = cv.CreateMemStorage(0)
    cont = cv.FindContours(smoothedThreshed, storage, mode=cv.CV_RETR_LIST, method=cv.CV_CHAIN_APPROX_SIMPLE)

    possible_balls = []
    for blob in contour_iterator(cont):   
      if len(blob) >= 6:
        tmp_ball = self.is_round(blob, 0.6)
        if tmp_ball is not None and self._ball_area_threshold[1] >= cv.ContourArea(blob) >= self._ball_area_threshold[0]:
          possible_balls.append(tmp_ball)
      
    if possible_balls:      
      if self._prev_ball_centre: (self._ball_centre, self._ball_radius, self._ball_roundness_metric) = sorted(possible_balls, key=lambda ball: euclidean_distance(ball[0], self._prev_ball_centre))[0]  
      else: (self._ball_centre, self._ball_radius, self._ball_roundness_metric) = sorted(possible_balls, key=lambda ball: ball[2], reverse=True)[0]
      return True
    else: 
      (self._ball_centre, self._ball_radius) = (None,None)
      return False
  
  def round_coors(self, coors):
    return (cv.Round(coors[0]), cv.Round(coors[1]))
  
  def draw_plate(self, im, t_contour, black_dot, centre=None, colour=cv.CV_RGB(0,0,255)):
    if t_contour: cv.DrawContours(im, t_contour, colour, colour, 0, 1, 8)
    if black_dot: 
      cv.Line(im, self.round_coors(black_dot[0]), self.round_coors(centre), cv.CV_RGB(255,0,0))
      self.draw_circle(im, black_dot[0], black_dot[1], colour)
    
  def draw_circle(self, im, centre, radius, colour=cv.CV_RGB(255,255,0), filled=False):
    if centre is not None and radius is not None:
      cv.Circle(im, self.round_coors(centre), radius, colour, cv.CV_FILLED if filled else 1)

  def set_hsv_values(self, h, s, v, colour, minmax):
    setattr(self, "_%s_colour_%s_hsv" % (colour, minmax), cv.Scalar(h,s,v))
       
  def get_hsv_values(self, colour, minmax):
    return tuple(getattr(self, "_%s_colour_%s_hsv" % (colour, minmax)))
  
  def set_threshold_values(self, value, name):
    setattr(self, "_%s_threshold" % (name,), value)

  def get_threshold_values(self, name):
    return getattr(self, "_%s_threshold" % (name,))

  def get_vision_values(self, name):
    valid_names = [
      'prev_ball_centre','ball_centre','ball_radius','ball_roundness_metric',
      'prev_yellow_robot_centre','yellow_robot_centre','prev_yellow_robot_black_dot','yellow_robot_black_dot','yellow_robot_t_area',
      'prev_blue_robot_centre','blue_robot_centre','prev_blue_robot_black_dot','blue_robot_black_dot','blue_robot_t_area', 
      'plate_area',
      'offset_top', 'offset_bottom', 'offset_left', 'offset_right'
    ]
    
    if name in valid_names: return getattr(self, "_"+name)
    else:                   return None


if __name__ == '__main__':
 from calibrate import Calibrate
 
 calibrate = Calibrate((9,6))
 calibrate.calibrate_camera_from_mem("calibration_data/")
 
 src_bg = cv.LoadImage("../../../fixtures/12.02.11/empty.jpg")
 bg = cv.CreateImage((src_bg.width/2, src_bg.height/2),8,3)
 cv.Resize(src_bg,bg)
 src_frame = cv.LoadImage("../../../fixtures/12.02.11/shot0015.jpg")
 frame = cv.CreateImage((src_frame.width/2, src_frame.height/2),8,3)
 cv.Resize(src_frame,frame)
 v = Vision(bg, calibrate, fix_distortions=False, main_pitch=False)
 v.update(frame)
 
 ball = v.get_ball()
 print "Ball information:"
 print "> center: ", ball[0] if ball else None
 print "> radius: ", ball[1] if ball else None
 
 print "Robot information:"
 print "> Blue robot:", v.get_robot('blue')
 print "> Yellow robot:", v.get_robot('yellow')
 
 # cv.ShowImage("Annotated Frame", v.get_frame(name='source', annotated=True))
 # # cv.ShowImage("Foreground Objects", v.get_frame(name='foreground', annotated=False))
 # 
 # while True:
 #   if(cv.WaitKey(100) == 27): break

