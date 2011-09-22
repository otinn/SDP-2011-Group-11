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
import sys

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--host', dest = 'host', help = 'connect to HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('-p', '--port', dest = 'port', help = 'connect to PORT (default read from host.txt line 2, otherwise 9999)', type = 'int',
        default = common.host_finder.get_port())
    options = parser.parse_args()[0]
    
    print 'This is the ultimate control module'
    print 'Any commands entered will be sent to the server without any validation'
    print 'State change commands: /general/state/(play|wait|kick_penalty|defend_penalty)'
    print '/general/robot/power_multiplier real'
    print '/general/robot/max_soft_turn real'
    print '/general/robot/max_heading_stabilizer real'
    print '/general/robot/max_power_limiter_constant real'
    print '/general/robot/power_limit_zone [0, 99]'
    print '/general/robot/acceleration_interval [0, 99]'
    print '/general/robot/init_straight_power [0, 99]'
    print '/general/robot/init_mid_straight_turn_power [0, 99]'
    print '/general/robot/init_turn_power [0, 99]'
    print '/general/robot/magic_offset [0, 99]'
    
    message_proxy = common.message_proxy.MessageProxy(options.host, options.port)
    message_proxy.start()
    message_proxy.outgoing.put('/general/identify manual secondary ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ' ultimate manual control')
    
    while True:
        s = sys.stdin.readline()
        if s == '':
            break
        s = s.rstrip()
        message_proxy.outgoing.put_nowait(s)
        
