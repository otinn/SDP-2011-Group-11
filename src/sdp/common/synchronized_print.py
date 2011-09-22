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

import threading
import Queue
import time
import sys

class SynchronizedPrint(threading.Thread):
    important = Queue.Queue()
    queue = Queue.Queue()
    
    def __init__(self, verbose):
        threading.Thread.__init__(self)
        self.daemon = True
        self._verbose = verbose
    
    def run(self):
        while(True):
            any = False
            while not SynchronizedPrint.important.empty():
                print SynchronizedPrint.important.get()
                any = True
            
            while not SynchronizedPrint.queue.empty():
                if self._verbose:
                    print SynchronizedPrint.queue.get()
                else:
                    SynchronizedPrint.queue.get()
                any = True
            
            if not any:
                time.sleep(0.001)
            else:
                sys.stdout.flush()