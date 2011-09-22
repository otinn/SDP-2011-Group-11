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
import time
import sys

print '/general/identify kicker primary ' + datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f') + ' the kicker'
sys.stdout.flush()

def lower_kicker():
    print '/kicker/order/run_inf -80'
    sys.stdout.flush()
    time.sleep(0.3)
    print '/kicker/order/run_inf -60'
    sys.stdout.flush()
    time.sleep(0.1)
    print '/kicker/order/run_inf -50'
    sys.stdout.flush()
    time.sleep(0.1)
    print '/kicker/order/brake'
    sys.stdout.flush()

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
    elif msg == '/planner/kick':
        print '/kicker/order/run_inf 127'
        sys.stdout.flush()
        time.sleep(0.2)
        lower_kicker()
    elif msg == '/planner/lower_kicker':
        lower_kicker()