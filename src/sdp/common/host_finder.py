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

import socket
import sys
import re

path = ''
if sys.argv[0].rfind('/') != -1:
    path = sys.argv[0][: sys.argv[0].rfind('/') + 1]

try:
    file = open(path + 'host.txt', 'r')
    host = file.readline().strip()
    port = 9999
    if host == '':
        host = socket.gethostname()
    
    try:
        next_line = file.readline().strip()
        match = re.match('[0-9]+$', next_line)
        if match != None:
            port = int(match.group(0))
    except:
        port = 9999
except:
    host = socket.gethostname()
    port = 9999

def get_host():
    return host

def get_port():
    return port