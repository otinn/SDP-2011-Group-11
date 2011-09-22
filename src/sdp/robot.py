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

import __init__ # uses psyco if available @UnusedImport
from datetime import datetime
import nxt.locator
import threading
import Queue
import sys
import re

def translate_motor_name(name):
    if name == 'left':
        return 'B'
    elif name == 'right':
        return 'C'
    return name

class MotorHandler(threading.Thread):
    def __init__(self, brick, port):
        threading.Thread.__init__(self)
        if port == 'A':
            port = nxt.motor.PORT_A
        elif port == 'B':
            port = nxt.motor.PORT_B
        else:
            port = nxt.motor.PORT_C
        self._motor = nxt.motor.Motor(brick, port)
        self.daemon = True
        self._commands = Queue.Queue()
    
    def brake(self):
        self._commands.put_nowait(('brake', None))
    
    def idle(self):
        self._commands.put_nowait(('idle', None))
    
    def run_inf(self, speed):
        self._commands.put_nowait(('run_inf', speed))
    
    def run(self):
        while(True):
            (cmd, speed) = self._commands.get(True)
            if not self._commands.empty():
                continue
            try:
                if cmd == 'brake':
                    self._motor.brake()
                elif cmd == 'idle':
                    self._motor.idle()
                elif cmd == 'run_inf':
                    self._motor.run(speed)
            except:
                pass

def handle_msg(str):
    match = re.match('/movement/order/brake\s+(A|B|C|left|right)$', str)
    if(match != None):
        name = translate_motor_name(match.group(1))
        handlers[name].brake()
        return
    
    match = re.match('/movement/order/idle\s+(A|B|C|left|right)$', str)
    if(match != None):
        name = translate_motor_name(match.group(1))
        handlers[name].idle()
        return
    
    match = re.match('/movement/order/run_inf\s+(A|B|C|left|right)\s+(-?[0-9]+)$', str)
    if(match != None):
        name = translate_motor_name(match.group(1))
        speed = long(match.group(2))
        
        if speed < -128:
            speed = -128
        if speed > 127:
            speed = 127
        
        dir = -1
        if speed > 0:
            dir = 1
        speed = abs(speed)
        speed = dir * max(62, min(90, speed))
        
        handlers[name].run_inf(speed)
        return
    
    match = re.match('/kicker/order/brake$', str)
    if(match != None):
        handlers['A'].brake()
        return
    
    match = re.match('/kicker/order/run_inf\s+(-?[0-9]+)$', str)
    if(match != None):
        speed = long(match.group(1))
        if speed < -128:
            speed = 128
        if speed > 127:
            speed = 127
        speed = -speed
        
        handlers['A'].run_inf(speed)
        return

if __name__ == "__main__":
    print '/general/identify robot primary ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ' robot controller'
    sys.stdout.flush()
    
    brick = nxt.locator.find_one_brick(name = 'Group_11')
    handlers = {'A': MotorHandler(brick, 'A'), 'B': MotorHandler(brick, 'B'), 'C': MotorHandler(brick, 'C')}
    for handler in handlers.values():
        handler.brake()
        handler.start()
    
    print '/robot/info/connected'
    sys.stdout.flush()
    
    while True:
        msg = sys.stdin.readline().rstrip()
        print 'received', msg
        sys.stdout.flush()
        handle_msg(msg)
        
        if msg == '/central/exit':
            print '/general/exiting obeying exit message'
            sys.stdout.flush()
            break
        elif msg == '':
            print '/general/exiting received empty message'
            sys.stdout.flush()
            break