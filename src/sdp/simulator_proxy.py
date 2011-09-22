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
from optparse import OptionParser
from datetime import datetime
import common.message_proxy
import common.host_finder
import threading
import math
import time
import re

class MessageTranslator(threading.Thread):
    def __init__(self, flip, source_proxy, destination_proxy):
        threading.Thread.__init__(self)
        self.daemon = True
        self._flip = flip
        self._source_proxy = source_proxy
        self._destination_proxy = destination_proxy
        
        self._pitch_height = 122
        self._pitch_width = 244
        
        time_format = '([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]+)' # 7 groups
        real_format = '-?[0-9]+(\.[0-9]+)?([eE]-?[0-9]+)?' # 2 groups
        self._regex_vision_xy = re.compile('/vision/xy\s+(ball|us|enemy)\s+(' + real_format + ')\s+(' + real_format + ')\s+(' + time_format + ')$')
        self._regex_vision_rotation = re.compile('/vision/rotation\s+(us|enemy)\s+(' + real_format + ')\s+(' + time_format + ')$')
        self._regex_vision_kicker_xy = re.compile('/vision/kicker/xy\s+(us|enemy)\s+(' + real_format + ')\s+(' + real_format + ')\s+(' + time_format + ')$')
        self._regex_movement_run_inf = re.compile('/movement/order/run_inf\s+(A|B|C|left|right)\s+(-?[0-9]+)$')
        self._regex_movement_brake_idle = re.compile('/movement/order/(brake|idle)\s+(A|B|C|left|right)$')
        self._regex_kicker_run_inf = re.compile('/kicker/order/run_inf\s+(-?[0-9]+)$')
        self._regex_kicker_brake = re.compile('/kicker/order/brake$')
    
    def _flip_name(self, name):
        if name == 'us':
            return 'enemy'
        if name == 'enemy':
            return 'us'
        return name
    
    def _flip_coordinates(self, x, y):
        return (self._pitch_width - x, self._pitch_height - y)
    
    def _normalize_rotation(self, rotation):
        full_circle = 2 * math.pi
        while rotation > full_circle:
            rotation -= full_circle
        while rotation < 0:
            rotation += full_circle
        return rotation
    
    def _flip_rotation(self, rotation):
        return self._normalize_rotation(math.pi + rotation)
    
    def _translate(self, msg):
        if not self._flip:
            return msg
        
        match = self._regex_vision_xy.match(msg)
        if match != None:
            x, y = self._flip_coordinates(float(match.group(2)), float(match.group(5)))
            return '/vision/xy ' + self._flip_name(match.group(1)) + ' ' + str(x) + ' ' + str(y) + ' ' + match.group(8)
        
        match = self._regex_vision_rotation.match(msg)
        if match != None:
            return '/vision/rotation ' + self._flip_name(match.group(1)) + ' ' + str(self._flip_rotation(float(match.group(2)))) + ' ' + match.group(5)
        
        match = self._regex_vision_kicker_xy.match(msg)
        if match != None:
            x, y = self._flip_coordinates(float(match.group(2)), float(match.group(5)))
            return '/vision/kicker/xy ' + self._flip_name(match.group(1)) + ' ' + str(x) + ' ' + str(y) + ' ' + match.group(8)
        
        match = self._regex_movement_run_inf.match(msg)
        if match != None:
            return '/movement/order/run_inf enemy ' + match.group(1) + ' ' + match.group(2)
        
        match = self._regex_movement_brake_idle.match(msg)
        if match != None:
            return '/movement/order/' + match.group(1) + ' enemy ' + match.group(2)
        
        match = self._regex_kicker_run_inf.match(msg)
        if match != None:
            return '/kicker/order/run_inf enemy ' + match.group(1)
        
        match = self._regex_kicker_brake.match(msg)
        if match != None:
            return '/kicker/order/brake enemy'
        
        return msg
    
    def run(self):
        while self._source_proxy.isAlive() and self._destination_proxy.isAlive():
            if self._source_proxy.incoming.empty():
                time.sleep(0.001)
            else:
                msg = self._source_proxy.incoming.get()
                self._destination_proxy.outgoing.put_nowait(self._translate(msg))

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--host', dest = 'host', help = 'central server HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('-p', '--port', dest = 'port', help = 'central server PORT (default read from host.txt line 2, otherwise 9999)', type = 'int',
        default = common.host_finder.get_port())
    parser.add_option('--multi_host', dest = 'multi_host', help = 'simulator server host MULTI_HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('--multi_port', dest = 'multi_port', help = 'simulator server port MULTI_PORT (default 19999)', type = 'int', default = 19999)
    parser.add_option('-e', '--enemy', dest = 'enemy', help = 'play as the enemy', action = 'store_true', default = False)
    options = parser.parse_args()[0]
    
    multi_io_proxy = common.message_proxy.MessageProxy(options.multi_host, options.multi_port)
    multi_io_proxy.outgoing.put_nowait('/general/multi_io_server/identify robot')
    multi_io_proxy.start()
    central_proxy = common.message_proxy.MessageProxy(options.host, options.port)
    central_proxy.outgoing.put_nowait('/general/identify robot primary ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ' multiplayer simulator')
    central_proxy.start()
    
    multi_to_central = MessageTranslator(options.enemy, multi_io_proxy, central_proxy)
    multi_to_central.start()
    central_to_multi = MessageTranslator(options.enemy, central_proxy, multi_io_proxy)
    central_to_multi.start()
    
    while multi_io_proxy.keep_running and multi_io_proxy.isAlive() and central_proxy.keep_running and central_proxy.isAlive() and multi_to_central.isAlive() and central_to_multi.isAlive():
        time.sleep(0.05)