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
from datetime import datetime
import common.message_proxy
import common.host_finder
import pygame.locals
import threading
import time
import copy
import sys

class Controller(threading.Thread):
    def __init__(self, message_proxy, key_state, gear):
        threading.Thread.__init__(self, name = 'stream->server')
        self.daemon = True
        self.message_proxy = message_proxy
        self.key_state = key_state
        self.last_state = {}
        self.gear = gear
        self.old_gear = copy.deepcopy(gear[0])
        self.last_moving = {'A': False, 'B': False, 'C': False}
    
    def control_separate(self, motor):
        if self.old_gear != 0 and self.last_state[motor + '_fow'][0] and not self.last_state[motor + '_back'][0]:
            # forwards
            self.message_proxy.outgoing.put_nowait('/movement/order/run_inf ' + motor + ' ' + str(127 * self.old_gear / 9))
            self.last_moving[motor] = True
        elif self.old_gear != 0 and not self.last_state[motor + '_fow'][0] and self.last_state[motor + '_back'][0]:
            # backwards
            self.message_proxy.outgoing.put_nowait('/movement/order/run_inf ' + motor + ' ' + str(-127 * self.old_gear / 9))
            self.last_moving[motor] = True
        elif self.last_state[motor + '_fow'][0] and self.last_state[motor + '_back'][0]:
            if self.last_moving[motor]:
                self.message_proxy.outgoing.put_nowait('/movement/order/brake ' + motor)
                self.last_moving[motor] = False
        else:
            if self.last_moving[motor]:
                self.message_proxy.outgoing.put_nowait('/movement/order/idle ' + motor)
                self.last_moving[motor] = False
    
    def run(self):
        with input_lock:
            for key in self.key_state.keys():
                self.last_state[key] = [False, False]
        
        while True:
            different = False
            changed_gear = False
            with input_lock:
                new_state = copy.deepcopy(self.key_state)
            
            # make arrow keys emulate pressing the specific motor control keys
            if new_state['up']:
                if new_state['left']:
                    new_state[right_motor + '_fow'] = True
                    new_state[right_motor + '_back'] = False
                    new_state[left_motor + '_fow'] = False
                    new_state[left_motor + '_back'] = False
                elif new_state['right']:
                    new_state[right_motor + '_fow'] = False
                    new_state[right_motor + '_back'] = False
                    new_state[left_motor + '_fow'] = True
                    new_state[left_motor + '_back'] = False
                else:
                    new_state[right_motor + '_fow'] = True
                    new_state[right_motor + '_back'] = False
                    new_state[left_motor + '_fow'] = True
                    new_state[left_motor + '_back'] = False
            elif new_state['down']:
                if new_state['left']:
                    new_state[right_motor + '_fow'] = False
                    new_state[right_motor + '_back'] = True
                    new_state[left_motor + '_fow'] = False
                    new_state[left_motor + '_back'] = False
                elif new_state['right']:
                    new_state[right_motor + '_fow'] = False
                    new_state[right_motor + '_back'] = False
                    new_state[left_motor + '_fow'] = False
                    new_state[left_motor + '_back'] = True
                else:
                    new_state[right_motor + '_fow'] = False
                    new_state[right_motor + '_back'] = True
                    new_state[left_motor + '_fow'] = False
                    new_state[left_motor + '_back'] = True
            
            for key in self.last_state.keys():
                if self.last_state[key][0] != new_state[key]:
                    self.last_state[key][0] = copy.deepcopy(new_state[key])
                    self.last_state[key][1] = True
                    different = True
                else:
                    self.last_state[key][1] = False
            
            if self.last_state['kick'][1] and new_state['kick']:
                self.message_proxy.outgoing.put_nowait('/planner/kick')
            
            if self.old_gear != self.gear[0]:
                self.old_gear = copy.deepcopy(self.gear[0])
                changed_gear = True
            
            if different or changed_gear:
                if self.last_state['A_fow'][1] or self.last_state['A_back'][1] or changed_gear:
                    self.control_separate('A')
                if self.last_state['B_fow'][1] or self.last_state['B_back'][1] or changed_gear:
                    self.control_separate('B')
                if self.last_state['C_fow'][1] or self.last_state['C_back'][1] or changed_gear:
                    self.control_separate('C')
            else:
                time.sleep(0.001)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--host', dest = 'host', help = 'connect to HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('-p', '--port', dest = 'port', help = 'connect to PORT (default read from host.txt line 2, otherwise 9999)', type = 'int',
        default = common.host_finder.get_port())
    options = parser.parse_args()[0]
    
    left_motor = 'B'
    right_motor = 'C'
    input_lock = threading.Lock()
    
    print 'Use the small window to capture keyboard events'
    print 'Use arrow keys if the left motor is in port', left_motor, 'and the right motor is in port', right_motor
    print 'Motor A forward: q, backward: a'
    print 'Motor B forward: w, backward: s'
    print 'Motor C forward: e, backward: d'
    print 'Use [space] to kick'
    print 'Use 0-9 for gears'
    
    message_proxy = common.message_proxy.MessageProxy(options.host, options.port)
    message_proxy.start()
    message_proxy.outgoing.put('/general/identify manual secondary ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ' manual motor control')
    
    pygame.init()
    screen = pygame.display.set_mode((150, 150))
    pygame.display.set_caption('RC')
    pygame.mouse.set_visible(1)
    key_state = {'A_fow': False, 'A_back': False, 'B_fow': False, 'B_back': False, 'C_fow': False, 'C_back': False, 'up': False, 'down': False, 'left': False,
        'right': False, 'kick': False}
    key_num = {pygame.locals.K_q: 'A_fow', pygame.locals.K_a: 'A_back', pygame.locals.K_w: 'B_fow', pygame.locals.K_s: 'B_back', pygame.locals.K_e: 'C_fow',
        pygame.locals.K_d: 'C_back', pygame.locals.K_UP: 'up', pygame.locals.K_DOWN: 'down', pygame.locals.K_LEFT: 'left', pygame.locals.K_RIGHT: 'right',
        pygame.locals.K_SPACE: 'kick'}
    gear = [9]
    Controller(message_proxy, key_state, gear).start()
    
    while message_proxy.isAlive():
        for event in pygame.event.get():
            with input_lock:
                if (event.type == pygame.locals.KEYUP) or (event.type == pygame.locals.KEYDOWN):
                    if event.key in key_num:
                        key_state[key_num[event.key]] = event.type == pygame.locals.KEYDOWN
                    elif event.type == pygame.locals.KEYDOWN and pygame.locals.K_0 <= event.key <= pygame.locals.K_9:
                        gear[0] = event.key - pygame.locals.K_0
                        print 'Switching to gear', gear
                if event.type == pygame.QUIT:
                    gear[0] = 0
                    sys.exit();
        time.sleep(0.001)