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
from common.synchronized_print import SynchronizedPrint
from optparse import OptionParser
import common.message_proxy
import common.host_finder
import subprocess
import os.path
import time
import sys
import re

class PingResponder(common.message_proxy.ServerToStream):
    def _handle_msg(self, msg, received):
        match = self._ping_regex.match(msg)
        if match != None:
            received = int(round(received * 1e3))
            self._message_proxy.outgoing.put_nowait('/general/vision/pong ' + match.group(1) + ' ' + str(received) + ' ' + str(int(round(time.time() * 1e3))))
            return True
        return False
    
    def run(self):
        self._message_proxy.outgoing.put_nowait('Vision ping responder ready')
        self._ping_regex = re.compile('/general/vision/ping\s+([0-9]+)$')
        
        while self._message_proxy.keep_running and self._message_proxy.isAlive():
            if not self._message_proxy.incoming.empty():
                received = time.time()
                msg = self._message_proxy.incoming.get(True).rstrip()
                self._handle_msg(msg, received)
            else:
                time.sleep(0.001)

if __name__ == "__main__":
    parser = OptionParser()
    parser.disable_interspersed_args()
    parser.set_usage('Usage: %prog [options] program')
    parser.add_option('--host', dest = 'host', help = 'connect to HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('-p', '--port', dest = 'port', help = 'connect to PORT (default read from host.txt line 2, otherwise 9999)', type = 'int',
        default = common.host_finder.get_port())
    parser.add_option('-c', '--client', dest = 'incoming', help = 'shows messages from the client', action = 'store_true', default = False)
    parser.add_option('-s', '--server', dest = 'outgoing', help = 'shows messages from the server', action = 'store_true', default = False)
    parser.add_option('--add_incoming', dest = 'add_incoming', help = 'sends INCOMING as the first message to the client')
    parser.add_option('--add_outgoing', dest = 'add_outgoing', help = 'sends OUTGOING as the first message to the server')
    (options, args) = parser.parse_args()
    
    if len(args) == 0:
        parser.print_help()
        sys.exit()
    
    proc = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, universal_newlines = True, shell = False)
    
    SynchronizedPrint(True).start()
    message_proxy = common.message_proxy.MessageProxy(options.host, options.port, show_incoming = options.incoming, show_outgoing = options.outgoing)
    if options.add_incoming != None:
        message_proxy.incoming.put_nowait(options.add_incoming)
    if options.add_outgoing != None:
        message_proxy.outgoing.put_nowait(options.add_outgoing)
    message_proxy.start()
    
    PingResponder(message_proxy, proc.stdin).start()
    common.message_proxy.StreamToServer(message_proxy, proc.stdout).start()
    
    while message_proxy.keep_running and message_proxy.isAlive():
        time.sleep(0.05)
    
    proc.stdin.close()
    proc.stdout.close()