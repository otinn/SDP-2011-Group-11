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

from __future__ import with_statement
import __init__ # uses psyco if available @UnusedImport
from optparse import OptionParser
import common.message_proxy
import common.host_finder
import pygame.gfxdraw
import threading
import datetime
import time
import math
import sys
import re

def scale(f):
    return pitch_zoom * f

def scale_round(f):
    return int(round(scale(f)))

def init_display():
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('Visualiser')
    pygame.mouse.set_visible(1)
    return screen

class robot_shape(object):
    def __init__(self, colour):
        self._colour = colour
        self._x = None
        self._y = None
        self._rotation = math.pi / 2
	self._line = robot_path(colour)    

    def set_xy(self, x, y):
        self._x = x
        self._y = y
        self._line.set_xy(x,y) 

    def set_rotation(self, rotation):
        self._rotation = rotation
	self._line.set_rotation(rotation)
    
    def draw(self, pitch):
        if self._x != None and self._y != None:
	    self._line.draw(pitch)
            robot = pygame.Surface((scale_round(robot_width), scale_round(robot_height)))
            robot.fill((0, 0, 255))
            
            longT = robot.subsurface(pygame.Rect(scale_round(robot_longT_offset[0]), scale_round(robot_longT_offset[1]), scale_round(robot_longT_size[0]),
                scale_round(robot_longT_size[1])))
            longT.fill(self._colour)
            
            shortT = robot.subsurface(pygame.Rect(scale_round(robot_shortT_offset[0]), scale_round(robot_shortT_offset[1]), scale_round(robot_shortT_size[0]),
                scale_round(robot_shortT_size[1])))
            shortT.fill(self._colour)
            
            pygame.gfxdraw.filled_circle(robot, scale_round(robot_circle_offset[0]), scale_round(robot_circle_offset[1]), scale_round(robot_circle_radius), (0, 0, 0))
            
            robot.set_alpha(200)
            robot.set_colorkey((255, 0, 255))
            robot = pygame.transform.rotate(robot, -180 * self._rotation / math.pi)
            pitch.blit(robot, (scale_round(self._x - robot.get_width() / 2.0 / pitch_zoom + wall_thickness),
                scale_round(pitch_height - self._y - robot.get_height() / 2.0 / pitch_zoom + wall_thickness)))
	    


class kicker_shape(object):
    def __init__(self, colour):
        self._colour = colour
        self._x = None
        self._y = None
        self._rotation = math.pi / 2
    
    def set_xy(self, x, y):
        self._x = x
        self._y = y
    
    def set_rotation(self, rotation):
        self._rotation = rotation
    
    def draw(self, pitch):
        if self._x != None and self._y != None:
            robot = pygame.Surface((scale_round(kicker_width), scale_round(kicker_height)))
            robot.fill((163, 73, 163))
            
            robot.set_alpha(200)
            robot.set_colorkey((255, 0, 255))
            robot = pygame.transform.rotate(robot, -180 * self._rotation / math.pi)
            pitch.blit(robot, (scale_round(self._x - robot.get_width() / 2.0 / pitch_zoom + wall_thickness),
                scale_round(pitch_height - self._y - robot.get_height() / 2.0 / pitch_zoom + wall_thickness)))


            

class MoveOrder(object):
    def __init__(self, us):
        self._points = []
        self._final_rotation = None
        self._us = us
    
    def set_cmd(self, cmd):
        pieces = cmd.split(' ')
        n = int(pieces[0])
        self._points = []
        for i in range(n):
            self._points.append((float(pieces[2 * i + 1]), float(pieces[2 * i + 2])))
        
        rotation = pieces[len(pieces) - 1]
        if rotation != 'not_important':
            self._final_rotation = float(rotation)
        else:
            self._final_rotation = None
    
    def _draw_mark(self, x, y, rotation, pitch):
        area = pygame.Surface((scale_round(2 * waypoint_radius), scale_round(2 * waypoint_radius)))
        area.fill((255, 0, 255))
        area.set_colorkey((255, 0, 255))
        area.set_alpha(200)
        pygame.gfxdraw.filled_circle(area, scale_round(waypoint_radius), scale_round(waypoint_radius), scale_round(waypoint_radius - 0.5), (255, 0, 0, 200))
        
        if rotation != None:
            dir = area.subsurface(pygame.Rect(scale_round(waypoint_radius - 0.5), scale_round(0.5), scale_round(1.25), scale_round(waypoint_radius - 0.5)))
            dir.fill((0, 0, 0))
            area = pygame.transform.rotate(area, -180 * rotation / math.pi)
        
        pitch.blit(area, (scale_round(x - area.get_width() / 2.0 / pitch_zoom + wall_thickness),
            scale_round(pitch_height - y - area.get_height() / 2.0 / pitch_zoom + wall_thickness)))
    
    def draw(self, pitch):
        for i in range(len(self._points)):
            point = self._points[i]
            if i + 1 == len(self._points):
                self._draw_mark(point[0], point[1], self._final_rotation, pitch)
            else:
                self._draw_mark(point[0], point[1], None, pitch)
        
        if len(self._points) == 0 and self._final_rotation != None and self._us._x != None and self._us._y != None:
            self._draw_mark(self._us._x, self._us._y, self._final_rotation, pitch)

class robot_path(object):
    def __init__(self, colour):
        self._colour = colour
        self._x1 = None
        self._y1 = None
        self._x2 = None
        self._y2 = None
        self._thick = 3
        self._rotation = math.pi / 2
	self._prevLines = []
        
    def set_xy(self, x, y):
        self._x1 = self._x2
        self._y1 = self._y2
	#given the center of the robot computing the point behind the robot
        self._x2 = x - math.sin(self._rotation)*(robot_width / 2.0) - self._thick
        self._y2 = (pitch_height - y) + math.cos(self._rotation)*(robot_width / 2.0)
            
    def set_rotation(self, rotation):
        self._rotation = rotation
    
    def update_prevLines(self):
	newList = []
	dt = datetime.timedelta(seconds=path_time)
	for l,x,y,t in self._prevLines:
		if dt > datetime.datetime.now() - t:
			newList.append((l,x,y,t))
	return newList		

    def draw(self, pitch):
        if self._x1 != None and self._x2 != None and self._y1 != None and self._y2 != None:
            length = math.sqrt(math.pow(self._x2-self._x1,2) + math.pow(self._y2-self._y1, 2))
            line = pygame.Surface((scale_round(length),scale_round(self._thick)))
            line.fill(self._colour)
            line.set_alpha(200)
            line.set_colorkey((255, 0, 255))
            line = pygame.transform.rotate(line, (-180 * self._rotation / math.pi) + 90)
	    self._prevLines.append((line, self._x2, self._y2, datetime.datetime.now()))
	    self._prevLines = self.update_prevLines()    
            for (l,x,y,t) in self._prevLines:
            	pitch.blit(l, (scale_round(x),scale_round(y)))


class EventDrawer(threading.Thread):
    def __init__(self, message_proxy, screen):
        threading.Thread.__init__(self, name = 'event drawer (server->stream)')
        self.daemon = True
        self._message_proxy = message_proxy
        self._screen = screen
        self._draw_static()
        self._us = robot_shape((0, 255, 0))
        self._enemy = robot_shape((255, 0, 0))
        self._location_ball = None
        self._kicker = kicker_shape((0, 255, 0))
        self._move_order = MoveOrder(self._us)
        self._update_screen()
        self._prepare_parser()
    
    def _update_screen(self):
        self._draw_pitch()
        self._enemy.draw(self._pitch)
        self._us.draw(self._pitch)
        self._move_order.draw(self._pitch)
        self._draw_ball()
        self._kicker.draw(self._pitch)
        self._screen.blit(self._pitch, (0, 0))
        pygame.display.flip()
    
    def _draw_static(self):
        self._background = pygame.Surface(self._screen.get_size())
        self._background = self._background.convert()
        self._background.fill((255, 255, 255))
    
    def _draw_pitch(self):
        self._pitch = self._background.subsurface(pygame.Rect(scale_round(pitch_offset_x), scale_round(pitch_offset_y), scale_round(pitch_width + 2 * wall_thickness),
            scale_round(pitch_height + 2 * wall_thickness)))
        self._pitch.fill((0, 0, 0))
        
        green_area = self._pitch.subsurface(pygame.Rect(scale_round(wall_thickness), scale_round(wall_thickness), scale_round(pitch_width), scale_round(pitch_height)))
        green_area.fill((34, 177, 76))
        
        side_height = (pitch_height - goal_height) / 2.0
        left_goal = self._pitch.subsurface(pygame.Rect(0, scale_round(wall_thickness + side_height), scale_round(wall_thickness), scale_round(goal_height)))
        left_goal.fill((192, 192, 192))
        right_goal = self._pitch.subsurface(pygame.Rect(scale_round(pitch_width + wall_thickness), scale_round(wall_thickness + side_height), scale_round(wall_thickness),
            scale_round(goal_height)))
        right_goal.fill((192, 192, 192))
        
        middle_line = self._pitch.subsurface(pygame.Rect(scale_round(pitch_width / 2.0 + wall_thickness - 1), scale_round(wall_thickness), scale_round(2),
            scale_round(pitch_height)))
        middle_line.fill((192, 192, 192))
            
    def _draw_ball(self):
        if self._location_ball != None:
            x = min(max(-1, float(self._location_ball[0])), pitch_width + 1)
            y = min(max(-1, pitch_height - float(self._location_ball[1])), pitch_height + 1)
            ball = pygame.Surface((scale_round(2 * ball_radius), scale_round(2 * ball_radius)), pygame.SRCALPHA, 32)
            pygame.gfxdraw.filled_circle(ball, scale_round(ball_radius), scale_round(ball_radius), scale_round(ball_radius), (255, 255, 0, 240))
            self._pitch.blit(ball, (scale_round(x + wall_thickness - ball_radius), scale_round(y + wall_thickness - ball_radius)))
    
    def _prepare_parser(self):
        time_format = '([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]+)' # 7 groups
        real_format = '-?[0-9]+(\.[0-9]+)?([eE]-?[0-9]+)?' # 2 groups
        self._prefix = '/central/received_message '
        self._regex_received = re.compile('/central/received_message\s+[a-z]+\s+([0-9]+)\s+' + time_format + '\s+(/(vision|planner)/.*)$')
        self._regex_vision_xy = re.compile('/vision/xy\s+(ball|us|enemy)\s+(' + real_format + ')\s+(' + real_format + ')\s+' + time_format + '$')
        self._regex_vision_rotation = re.compile('/vision/rotation\s+(us|enemy)\s+(' + real_format + ')\s+' + time_format + '$')
        self._regex_vision_kicker_xy = re.compile('/vision/kicker/xy\s+us\s+(' + real_format + ')\s+(' + real_format + ')\s+' + time_format + '$')
        self._regex_planner_move = re.compile('/planner/move\s+(.+)$')
        self._regex_planner_move2 = re.compile('/planner/move_rev\s+(.+)$')
    
    def handle_msg(self, msg):
        if msg[0: len(self._prefix)] != self._prefix:
            return False
        
        match = self._regex_received.match(msg)
        if(match == None):
            return False
        msg = match.group(9)
        
        match = self._regex_vision_xy.match(msg)
        if(match != None):
            if match.group(1) == 'ball':
                self._location_ball = (match.group(2), match.group(5))
            elif match.group(1) == 'us':
                self._us.set_xy(float(match.group(2)), float(match.group(5)))
            else:
                self._enemy.set_xy(float(match.group(2)), float(match.group(5)))
            return True
        
        match = self._regex_vision_rotation.match(msg)
        if(match != None):
            if match.group(1) == 'us':
                self._us.set_rotation(float(match.group(2)))
                self._kicker.set_rotation(float(match.group(2)))
                
            else:
                self._enemy.set_rotation(float(match.group(2)))
            return True
        
        match = self._regex_vision_kicker_xy.match(msg)
        if(match != None):
            self._kicker.set_xy(float(match.group(1)), float(match.group(4)))
            return True
        
        match = self._regex_planner_move.match(msg)
        if(match != None):
            self._move_order.set_cmd(match.group(1).strip())
            return True
        
        match = self._regex_planner_move2.match(msg)
        if(match != None):
            self._move_order.set_cmd(match.group(1).strip())
            return True
    
    def run(self):
        next_update = datetime.datetime.now()
        draw_interval = datetime.timedelta(milliseconds = 50)
        updated = False
        
        while self._message_proxy.keep_running and self._message_proxy.isAlive():
            if not self._message_proxy.incoming.empty():
                msg = self._message_proxy.incoming.get(True)
                if self.handle_msg(msg):
                    updated = True
            else:
                time.sleep(0.001)
            if updated and next_update < datetime.datetime.now():
                self._update_screen()
                next_update = datetime.datetime.now() + draw_interval
                updated = False

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--host', dest = 'host', help = 'connect to HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('-p', '--port', dest = 'port', help = 'connect to PORT (default read from host.txt line 2, otherwise 9999)', type = 'int',
        default = common.host_finder.get_port())
    parser.add_option('-z', '--zoom', dest = 'zoom', help = 'pitch zoom (positive integers only); default is 4', type = 'int', default = 4)
    parser.add_option('-t', '--time', dest = 'time', help = 'robot path (positive integers only); default is 4', type = 'int', default = 0)
    options = parser.parse_args()[0]
    
    pitch_height = 122
    pitch_width = 244
    goal_height = 60
    wall_thickness = 1
    pitch_zoom = options.zoom
    
    path_time = options.time
    ball_radius = 2.1
    robot_height = 20
    robot_width = 18
    robot_longT_offset = (7.5, 1)
    robot_longT_size = (3, 12.5)
    robot_shortT_offset = (4, 10.5)
    robot_shortT_size = (10, 3)
    robot_circle_offset = (9, 17)
    robot_circle_radius = 1.5
    kicker_height = 4.5
    kicker_width = robot_width - 1
    
    pitch_offset_x = 0
    pitch_offset_y = 0
    
    waypoint_radius = 4
    
    screen_width = scale_round(pitch_width + 2 * wall_thickness + 2 * pitch_offset_x)
    screen_height = scale_round(pitch_height + 2 * wall_thickness + 2 * pitch_offset_y)
    
    message_proxy = common.message_proxy.MessageProxy(options.host, options.port)
    message_proxy.start()
    message_proxy.outgoing.put('/general/identify logger secondary ' + datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ' visualiser')
    screen = init_display()
    EventDrawer(message_proxy, screen).start()
    
    while message_proxy.isAlive():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit();
        time.sleep(0.001)
