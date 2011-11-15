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
import os.path
import sys

START_TIME = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
FILENAME = '../../logs/' + START_TIME.replace(':', '_') + '.log'
print '/general/identify logger primary ' + START_TIME + ' python logger'
sys.stdout.flush()

if not os.path.exists('../../logs'):
    os.makedirs('../../logs')

with open(FILENAME, 'w') as file:
    while True:
        msg = sys.stdin.readline().rstrip()
        file.write(msg + '\n')
        file.flush()
        if msg == '/central/exit':
            print '/general/exiting obeying exit message'
            sys.stdout.flush()
            break
        elif msg == '':
            print '/general/exiting received empty message'
            sys.stdout.flush()
            break