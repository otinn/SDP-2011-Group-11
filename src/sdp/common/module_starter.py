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

import subprocess
import threading
import time
import os

class ModuleStarter(threading.Thread):
    def __init__(self, cmd, shell = False):
        threading.Thread.__init__(self)
        if isinstance(cmd, str) and cmd[0:5] != 'xterm':
            cmd = cmd.split(' ')
        self._cmd = cmd
        self._stop = False
        self._shell = shell
    
    def stop(self):
        self._stop = True
    
    def run(self):
        fnull = open(os.devnull, 'w')
        proc = subprocess.Popen(self._cmd, stdin = subprocess.PIPE, stdout = fnull, shell = self._shell)
        
        while not self._stop:
            try:
                proc.poll()
                if proc.returncode != None:
                    break
            except:
                break
            time.sleep(0.1)
        
        try:
            try:
                proc.stdin.write('/central/exit')
                proc.stdin.flush()
                time.sleep(0.5)
            except:
                pass
            proc.kill()
        except:
            pass
