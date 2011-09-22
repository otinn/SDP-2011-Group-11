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
from datetime import datetime
import threading
import copy
import math
import time
import sys
import re

START_TIME = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
print '/general/identify movement primary ' + START_TIME + ' simple movement module'
sys.stdout.flush()

def normalize_rotation(rotation):
    full_circle = 2 * math.pi
    while rotation < 0:
        rotation += full_circle
    while rotation > full_circle:
        rotation -= full_circle
    return rotation

class WorldSituation(object):
    def __init__(self, x, y, rotation):
        self.x = x
        self.y = y
        self.rotation = rotation
    
    def known(self):
        return self.x != None and self.y != None and self.rotation != None

    def __str__(self):
        return 'WorldSituation: ' + str(self.x) + ', ' + str(self.y) + ' (' + str(self.rotation) + ')'

class OrderNode(object):
    def __init__(self):
        self._last_left = ''
        self._last_right = ''
    
    def _send_msg(self, do_left, do_right):
        any = False
        if self._last_left != do_left:
            self._last_left = do_left
            print do_left
            any = True
        if self._last_right != do_right:
            self._last_right = do_right
            print do_right
            any = True
        if any:
            sys.stdout.flush()
    
    def _change_speed(self, left, right):
        if left == 0:
            do_left = '/movement/order/idle left'
        else:
            do_left = '/movement/order/run_inf left ' + str(left)
        if right == 0:
            do_right = '/movement/order/idle right'
        else:
            do_right = '/movement/order/run_inf right ' + str(right)
        self._send_msg(do_left, do_right)
    
    def _brake(self):
        self._send_msg('/movement/order/brake left', '/movement/order/brake right')
    
    def _idle(self):
        self._send_msg('/movement/order/idle left', '/movement/order/idle right')

def scale_speed(speed):
    speed = int(round(speed * 10))
    if speed < -128:
        speed = -128
    if speed > 127:
        speed = 127
    if speed < 0:
        if speed > -30:
            speed = -30
    if speed > 0:
        if speed < 30:
            speed = 30
    return speed

class MovementNode(OrderNode):
    def __init__(self, x, y, stop):
        OrderNode.__init__(self)
        self.x = x
        self.y = y
        self.stop = stop
    
    # returns True if the work has been done
    def execute(self, state):
        if not state.known():
            return False
        
        dist = math.sqrt((state.x - self.x) ** 2 + (state.y - self.y) ** 2)
        if dist < 3:
            return True
        speed = scale_speed(25)
        if dist > 70:
            speed = scale_speed(40)
        elif dist > 40:
            speed = scale_speed(30)
        
        target_rotation = normalize_rotation(math.atan2(self.x - state.x, self.y - state.y))
        angle = normalize_rotation(target_rotation - state.rotation)
        difference = min(angle, 2 * math.pi - angle)
        max_diff = 0.3
        
        if difference > max_diff:
            #speed = min(speed, scale_speed(25))
            if angle < math.pi:
                self._change_speed(speed, -speed)
            else:
                self._change_speed(-speed, speed)
            if difference < 0.1:
                time.sleep(0.04)
                self._idle()
        else:
            max_diff_percent = 0.2
            diff = int(math.floor(speed * max_diff_percent * difference / max_diff))
            
            if angle < math.pi:
                self._change_speed(speed, speed - diff)
            else:
                self._change_speed(speed - diff, speed)
            
            if dist < 8 and self.stop:
                time.sleep(0.04)
                self._idle()
        
        return False
    
    def __str__(self):
        return 'MovementNode: ' + str(self.x) + ', ' + str(self.y) + (' (final move)' if self.stop else ' (not final move)')

class TurningNode(OrderNode):
    def __init__(self, rotation):
        OrderNode.__init__(self)
        self.rotation = rotation
    
    # returns True if the work has been done
    def execute(self, state):
        if not state.known():
            return False
        
        angle = normalize_rotation(self.rotation - state.rotation)
        difference = min(angle, 2 * math.pi - angle)
        if difference < 0.05:
            return True
        
        speed = scale_speed(25)
        if angle < math.pi:
            self._change_speed(speed, -speed)
        else:
            self._change_speed(-speed, speed)
        
        if difference < 0.5:
            time.sleep(0.04)
            self._idle()
        return False
    
    def __str__(self):
        return 'TurningNode: ' + str(self.rotation)

class StopNode(OrderNode):
    def __init__(self):
        OrderNode.__init__(self)
        self._done = False
    
    # returns True if the work has been done
    def execute(self, state):
        if self._done:
            return True
        self._brake()
        self._done = True
        return False
    
    def __str__(self):
        if self._done:
            return 'StopNode: done'
        return 'StopNode: not done'

class MovementOrder(object):
    def __init__(self, cmd):
        # /planner/move n coordinates (final_rotation|not_important)
        pieces = cmd.split(' ')
        n = int(pieces[0])
        self._parts = []
        for i in range(n):
            self._parts.append(MovementNode(float(pieces[2 * i + 1]), float(pieces[2 * i + 2]), i + 1 == n))
        rotation = pieces[len(pieces) - 1]
        if rotation != 'not_important':
            self._parts.append(TurningNode(float(rotation)))
        self._parts.append(StopNode())
        self._pos = 0
    
    def move(self, state):
        # passes control to the next order until it runs out or finds one that needs to do work
        while self._pos < len(self._parts) and self._parts[self._pos].execute(state):
            self._pos += 1
    
    def __str__(self):
        res = 'MovementOrder at ' + str(self._pos) + '/' + str(len(self._parts))
        for node in self._parts:
            res += '\n' + str(node)
        return res

class StreamListener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name = 'stream listener')
        self.daemon = True
        self._lock = threading.Lock()
        self._state = WorldSituation(None, None, None)
        self._cmd = None
    
    def run(self):
        time_format = '([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]+)' # 7 groups
        real_format = '-?[0-9]+(\.[0-9]+)?([eE]-?[0-9]+)?' # 2 groups
        regex_vision_xy = re.compile('/vision/xy\s+us\s+(' + real_format + ')\s+(' + real_format + ')\s+' + time_format + '$')
        regex_vision_rotation = re.compile('/vision/rotation\s+us\s+(' + real_format + ')\s+' + time_format + '$')
        planner_move_prefix = '/planner/move '
        planner_move_prefix2 = '/planner/move_rev '
        
        while True:
            msg = sys.stdin.readline().rstrip()
            if msg == '/central/exit':
                print '/general/exiting obeying exit message'
                sys.stdout.flush()
                break
            elif msg == '':
                print '/general/exiting received empty message'
                sys.stdout.flush()
                break
            else:
                with self._lock:
                    match = regex_vision_xy.match(msg)
                    if(match != None):
                        self._state.x = float(match.group(1))
                        self._state.y = float(match.group(4))
                        continue
                    
                    match = regex_vision_rotation.match(msg)
                    if(match != None):
                        self._state.rotation = float(match.group(1))
                        continue
                    
                    if msg[0: len(planner_move_prefix)] == planner_move_prefix:
                        self._cmd = msg[len(planner_move_prefix):].strip()
                        continue
                    elif msg[0: len(planner_move_prefix2)] == planner_move_prefix2:
                        self._cmd = msg[len(planner_move_prefix2):].strip()
                        continue
    
    def get_state(self):
        with self._lock:
            return copy.deepcopy(self._state)
    
    def take_cmd(self):
        with self._lock:
            t = copy.deepcopy(self._cmd)
            self._cmd = None
            return t

if __name__ == "__main__":
    stream_listener = StreamListener()
    stream_listener.start()
    order = MovementOrder('0 not_important')
    old_state = ''
    
    while True:
        state = stream_listener.get_state()
        cmd = stream_listener.take_cmd()
        if cmd != None:
            order = MovementOrder(cmd)
        elif str(state) == old_state:
            time.sleep(0.001)
            continue
        
        old_state = str(state)
        order.move(state)
        
        time.sleep(0.001)