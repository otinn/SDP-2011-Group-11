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
import time
import sys
import re

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--host', dest = 'host', help = 'connect to HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('-p', '--port', dest = 'port', help = 'connect to PORT (default read from host.txt line 2, otherwise 9999)', type = 'int',
        default = common.host_finder.get_port())
    options = parser.parse_args()[0]
    
    print 'The actual commands sent to the server will be timestamped automatically'
    print '/vision/xy (us|ball|enemy) x y (x and y are real numbers)'
    print '/vision/rotation (us|enemy) r (r is in radians)'
    print ''
    
    message_proxy = common.message_proxy.MessageProxy(options.host, options.port)
    message_proxy.start()
    message_proxy.outgoing.put('/general/identify vision secondary ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ' vision simulator')
    
    while message_proxy.isAlive():
        str = sys.stdin.readline().strip()
        
        match = re.match('/vision/xy\s+(ball|us|enemy)\s+(-?[0-9]+(\.[0-9]+)?)\s+(-?[0-9]+(\.[0-9]+)?)$', str)
        if(match != None):
            message_proxy.outgoing.put_nowait('/vision/xy ' + match.group(1) + ' ' + match.group(2) + ' ' + match.group(4) + ' ' +
                datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
            continue
        
        match = re.match('/vision/rotation\s+(us|enemy)\s+([0-9]+(\.[0-9]+)?)$', str)
        if(match != None):
            message_proxy.outgoing.put_nowait('/vision/rotation ' + match.group(1) + ' ' + match.group(2) + ' ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
            continue
        
        match = re.match('#sleep\s+([0-9]+(\.[0-9]+)?)$', str)
        if(match != None):
            time.sleep(float(match.group(1)))
            continue
        
        print 'Unrecognised command', str