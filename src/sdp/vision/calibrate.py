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

"""
Based on the OpenCV Test Suit as well as Ali Shck's "Calibrating & Undistorting 
with OpenCV in C++ (Oh yeah)" and Max Grosse tutorials.
"""
import cv
import yaml
from math import sin, cos, tan, sqrt, pi

class Calibrate:
  def __init__(self, chessboard_dim):
    self.chessboard_dim          = chessboard_dim
    self.num_pts                 = chessboard_dim[0] * chessboard_dim[1]
    self.intrinsics              = cv.CreateMat(3, 3, cv.CV_64FC1)
    self.distortion              = cv.CreateMat(4, 1, cv.CV_64FC1)
    self._points                 = None
    (self._param1, self._param2) = (9,10)
    
    cv.SetZero(self.intrinsics)
    cv.SetZero(self.distortion)
  
  def mk_point_counts(self, nimages):
    npts = cv.CreateMat(nimages, 1, cv.CV_32SC1)
    for i in range(nimages):
      npts[i, 0] = self.num_pts
    return npts

  def mk_image_points(self, goodcorners):
    ipts = cv.CreateMat(len(goodcorners) * self.num_pts, 2, cv.CV_32FC1)
    for (i, co) in enumerate(goodcorners):
      for j in range(self.num_pts):
        ipts[i * self.num_pts + j, 0] = co[j][0]
        ipts[i * self.num_pts + j, 1] = co[j][1]
    return ipts

  def mk_object_points(self, nimages, squaresize = 1):
    opts = cv.CreateMat(nimages * self.num_pts, 3, cv.CV_32FC1)
    for i in range(nimages):
      for j in range(self.num_pts):
        opts[i * self.num_pts + j, 0] = (j / self.chessboard_dim[0]) * squaresize
        opts[i * self.num_pts + j, 1] = (j % self.chessboard_dim[0]) * squaresize
        opts[i * self.num_pts + j, 2] = 0
    return opts

  def get_corners(self, mono):
    (found_all, corners) = cv.FindChessboardCorners(mono, chessboard_dim, cv.CV_CALIB_CB_ADAPTIVE_THRESH + cv.CV_CALIB_CB_NORMALIZE_IMAGE + cv.CV_CALIB_CB_FILTER_QUADS)
    return (found_all, corners)
  
  def calibrate_camera(self, images, save_data=False):
    corners = [self.get_corners(im) for im in images] # all corners
    goodcorners = [co for (im, (found_all, co)) in zip(images, corners) if found_all]

    ipts = self.mk_image_points(goodcorners)
    opts = self.mk_object_points(len(goodcorners), .1)
    npts = self.mk_point_counts(len(goodcorners))

    # Elements (0,0) and (1,1) are the focal lengths along the X and Y axis. 
    # The camera's aspect ratio is (usually) 1/1, Please change if otherwise.
    self.intrinsics[0,0] = 1.0
    self.intrinsics[1,1] = 1.0

    cv.CalibrateCamera2(opts, ipts, npts,
                        cv.GetSize(images[0]),
                        self.intrinsics,
                        self.distortion,
                        cv.CreateMat(len(goodcorners), 3, cv.CV_32FC1),
                        cv.CreateMat(len(goodcorners), 3, cv.CV_32FC1),
                        flags = 0)

    if save_data:
      cv.Save("calibration_data/intrinsics.yml", self.intrinsics)
      cv.Save("calibration_data/distortion.yml", self.distortion)

  def calibrate_camera_from_mem(self, path):
    self.intrinsics = cv.GetMat(cv.Load(path + "intrinsics.yml"))
    self.distortion = cv.GetMat(cv.Load(path + "distortion.yml"))
    
      
  def draw_corners(self, source_image):
    im = cv.CloneImage(source_image)
    (found_all, corners) = self.get_corners(im)
    cv.DrawChessboardCorners(im, self.chessboard_dim, corners, found_all)
    return im
    
  def undist_fisheye(self, src_im):
    im = cv.CreateImage((src_im.width + 40, src_im.height + 40),8,3)
    cv.CopyMakeBorder(src_im, im, (20,20), 0)

    newK = cv.CreateMat(3, 3, cv.CV_64FC1)
    cv.GetOptimalNewCameraMatrix(self.intrinsics, self.distortion, cv.GetSize(im), 1.0, newK)

    mapx = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_32F, 1)
    mapy = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_32F, 1)
    
    cv.InitUndistortMap(self.intrinsics, self.distortion, mapx, mapy)
    undistdim = cv.CloneMat(cv.GetMat(im))
    cv.Remap(im, undistdim, mapx, mapy)
    
    cv_im = cv.GetImage(undistdim)
    
    return cv_im
  
  def crop_frame(self, img):
    left  = 0
    right = img.width
    up    = 20
    down  = img.height - 40
    #left  = int((53 / 640.0) * img.width)
    #right = int((626 / 640.0) * img.width)
    #up    = int((17 / 480.0) * img.height)
    #down  = int((475 / 480.0) * img.height)

    cv.SetImageROI(img, (left, up, right - left, down - up))
    tmp_im = cv.CreateImage(cv.GetSize(img),8,3)
    cv.Copy(img, tmp_im, None)
    cv.ResetImageROI(img) 

    return tmp_im
    
  def undist_perspective(self, im_in, corners_from_mem=False, width=700, height=350):
    im = cv.CreateImage((width,height), cv.IPL_DEPTH_8U, 3)
    cv.Resize(im_in, im)
    
    if corners_from_mem:
      self._points = yaml.load(file.read('calibration_data/corners.yaml', 'r'))
    else:
      (self._param1, self._param2) = self.detect_corners(im, self._param1, self._param2)
    
    homo = self.calculate_homography(im_in.width, im_in.height, im.width, im.height)
    
    out = cv.CloneImage(im_in)
    cv.WarpPerspective(im_in, out, homo)
    out_small = cv.CloneImage(im)
    cv.Resize(out, out_small)

    return out_small
    
  def calculate_homography(self, real_width, real_height, width, height):
      if len(self._points)!=4:
        raise Exception('need exactly four points')
      
      p   = cv.CreateMat(2, 4, cv.CV_64FC1)
      h   = cv.CreateMat(2, 4, cv.CV_64FC1)
      p2h = cv.CreateMat(3, 3, cv.CV_64FC1)

      cv.Zero(p)
      cv.Zero(h)
      cv.Zero(p2h)

      for i in range(4):
        (x,y) = self._points[i]
        p[0,i] = (float(real_width) / float(width)) * x
        p[1,i] = (float(real_height) / float(height)) * y

      h[0,0] = 0
      h[1,0] = real_height

      h[0,1] = real_width
      h[1,1] = real_height

      h[0,2] = real_width
      h[1,2] = 0

      h[0,3] = 0
      h[1,3] = 0

      cv.FindHomography(p, h, p2h)

      return p2h
  
  def detect_corners(self, img_src, param1, param2, save_corners=True):
    if self._points is not None:
      return (self._param1, self._param2)
    
    img = cv.CreateImage(cv.GetSize(img_src),8,1)
    cv.CvtColor(img_src, img, cv.CV_BGR2GRAY)
    
    imgSize = cv.GetSize(img)

    detected = cv.CreateImage(imgSize, cv.IPL_DEPTH_8U, 1)
    cv.AdaptiveThreshold(img, detected, 255, cv.CV_ADAPTIVE_THRESH_MEAN_C, cv.CV_THRESH_BINARY_INV, param1, param2)
    tmp = cv.CreateImage(imgSize, 8, 1)
    element = cv.CreateStructuringElementEx(2,2,1,1,cv.CV_SHAPE_RECT)
    cv.MorphologyEx(detected, detected, tmp, element , cv.CV_MOP_OPEN, 1)

    dst = cv.CreateImage(imgSize, 8, 1)
    color_dst = cv.CreateImage(imgSize, 8, 3)
    storage = cv.CreateMemStorage(0)
    lines = 0

    cv.CvtColor(detected, color_dst, cv.CV_GRAY2BGR)

    lines = cv.HoughLines2(detected, storage, cv.CV_HOUGH_STANDARD, 1, pi / 180, 77, 0, 0)
    
    left1   = [0, 0]
    left2   = [0, 0]
    right1  = [0, 0]
    right2  = [0, 0]
    top1    = [0, 0]
    top2    = [0, 0]
    bottom1 = [0, 0]
    bottom2 = [0, 0]

    numLines  = len(lines)
    numTop    = 0
    numBottom = 0
    numLeft   = 0
    numRight  = 0

    for (rho, theta) in lines:
      if(theta == 0.0):
        continue

      degrees = theta * 180 / pi

      pt1 = (0, rho / sin(theta))
      pt2 = (imgSize[0], (-imgSize[0] / tan(theta)) + rho / sin(theta))
      
      if(abs(rho) < 90): # TOP + LEFT
        if(degrees > 75 and degrees < 105): # TOP
          numTop += 1

          # The line is horizontal and near the top
          top1[0] += pt1[0]
          top1[1] += pt1[1]

          top2[0] += pt2[0]
          top2[1] += pt2[1]
        elif(degrees > 135 and degrees < 180): # LEFT
          numLeft += 1

          # The line is vertical and near the left
          left1[0] += pt1[0]
          left1[1] += pt1[1]

          left2[0] += pt2[0]
          left2[1] += pt2[1]
      else: # BOTTOM + RIGHT
        if(degrees > 75 and degrees < 105): # BOTTOM
          numBottom += 1

          # The line is horizontal and near the bottom
          bottom1[0] += pt1[0]
          bottom1[1] += pt1[1]

          bottom2[0] += pt2[0]
          bottom2[1] += pt2[1]
        else: # RIGHT
          numRight += 1

          # The line is vertical and near the right
          right1[0] += pt1[0]
          right1[1] += pt1[1]

          right2[0] += pt2[0]
          right2[1] += pt2[1]
    
    if numLeft != 0:
      left_pt1 = (cv.Round(left1[0] / numLeft), cv.Round(left1[1] / numLeft))
      left_pt2 = (cv.Round(left2[0] / numLeft), cv.Round(left2[1] / numLeft))
    else:
      left_pt1 = (0, -616)
      left_pt2 = (700, 23886)
    
    if numRight != 0:
      right_pt1 = (cv.Round(right1[0] / numRight), cv.Round(right1[1] / numRight))
      right_pt2 = (cv.Round(right2[0] / numRight), cv.Round(right2[1] / numRight))
    else:
      right_pt1 = (0, 39479)
      right_pt2 = (700, -624)

    try:
      top_pt1 = (cv.Round(top1[0] / numTop), cv.Round(top1[1] / numTop))
      top_pt2 = (cv.Round(top2[0] / numTop), cv.Round(top2[1] / numTop))

      bottom_pt1 = (cv.Round(bottom1[0] / numBottom), cv.Round(bottom1[1] / numBottom))
      bottom_pt2 = (cv.Round(bottom2[0] / numBottom), cv.Round(bottom2[1] / numBottom))
    except:
      if param2 > 0:
        self.detect_corners(img_src, param1, param2 - 1)
        return (self._param1, self._param2)
      else:
        raise Exception("Top or bottom corners was not found.")
    
    left_coef   = self.find_line_coefficients(left_pt1, left_pt2)
    top_coef    = self.find_line_coefficients(top_pt1, top_pt2)
    bottom_coef = self.find_line_coefficients(bottom_pt1, bottom_pt2)
    right_coef  = self.find_line_coefficients(right_pt1, right_pt2)

    ptTopLeft     = self.solve_intersection(left_coef, top_coef)
    ptTopRight    = self.solve_intersection(right_coef, top_coef)
    ptBottomRight = self.solve_intersection(right_coef, bottom_coef)
    ptBottomLeft  = self.solve_intersection(left_coef, bottom_coef)
    
    ptBottomLeft  = (0, int(ptBottomLeft[1] + 15) if ptBottomLeft[1] + 15 <= img_src.height else ptBottomLeft[1])
    ptBottomRight = (img_src.width, int(ptBottomRight[1] + 15) if ptBottomRight[1] + 15 <= img_src.height else ptBottomRight[1]) 
    ptTopRight    = (img_src.width, int(ptTopRight[1] ) if ptTopRight[1] - 15 <= img_src.width else ptTopRight[1])
    ptTopLeft     = (0, int(ptTopLeft[1] ) if ptTopLeft[1] - 15 <= img_src.width else ptTopLeft[1])
    
    self._points = [ptBottomLeft, ptBottomRight, ptTopRight, ptTopLeft]
    
    if save_corners:
      corners_file = file('calibration_data/corners.yaml', 'w')
      corners_file.write(yaml.dump(self._points))
      corners_file.close()
      
    return (param1, param2)
    
  def find_line_coefficients(self, pt1, pt2):
    a = pt2[1] - pt1[1]
    b = pt1[0] - pt2[0]
    c = b * pt1[1] + a * pt1[0]

    return (a,b,c)

  def solve_intersection(self, coefs1, coefs2):
    det = coefs1[0] * coefs2[1] - coefs2[0] * coefs1[1]

    if det == 0:
      return None

    x = (coefs2[1] * coefs1[2] - coefs1[1] * coefs2[2]) / det
    y = (coefs1[0] * coefs2[2] - coefs2[0] * coefs1[2]) / det

    return (x,y)
  

if __name__ == "__main__":
  chessboard_dim = (9,6)

  img = cv.LoadImage('b05.jpg')
  cal = Calibrate(chessboard_dim)
  # cal.calibrate_camera(images, save_data=True)
  cal.calibrate_camera_from_mem("calibration_data/")

  undist_fisheye_im = cal.undist_fisheye(img)
  # cim = cal.draw_corners(images[0])
  cropped_frame = cal.crop_frame(undist_fisheye_im)
  undist_perspective_im = cal.undist_perspective(cropped_frame)
  
  # cv.ShowImage("Fisheye Undistorted Image", undist_fisheye_im)
  # cv.ShowImage("Cropped Image", cropped_frame)
  cv.ShowImage("Perspective + Fisheye Undistorted Image", undist_perspective_im)
  # cv.ShowImage("Finding Corners in Image", cim)
  # cv.ShowImage("Original Image", img)
  
  cv.WaitKey()

