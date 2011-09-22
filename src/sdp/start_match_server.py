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
from common.utility import current_time
from optparse import OptionParser
import common.module_starter
import common.host_finder
import multi_io_server
import time
import os

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--multi_host', dest = 'multi_host', help = 'simulator server host MULTI_HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('--multi_port', dest = 'multi_port', help = 'simulator server port MULTI_PORT (default 19999)', type = 'int', default = 19999)
    parser.add_option('-v', '--verbose', dest = 'verbose', help = 'show more information', action = 'store_true', default = False)
    options = parser.parse_args()[0]
    
    SynchronizedPrint(options.verbose).start()
    multi_io_server = multi_io_server.MultiIOServer(options.multi_host, options.multi_port, options.verbose)
    multi_io_server.start()
    
    SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' Waiting for the MultiIOServer to start')
    while not multi_io_server.ready:
        time.sleep(0.001)
    SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' MultiIOServer started')
    
    simulator_cmd = ['python', 'proxy.py']
    simulator_cmd.append('--host')
    simulator_cmd.append(options.multi_host)
    simulator_cmd.append('--port')
    simulator_cmd.append(str(options.multi_port))
    simulator_cmd.append('--add_outgoing')
    simulator_cmd.append('/general/multi_io_server/identify vision')
    simulator_cmd.append('./simulator/simulator' + ('.exe' if os.name == 'nt' else ''))
    
    try:
        simulator = common.module_starter.ModuleStarter(simulator_cmd)
        simulator.start()
        
        while multi_io_server.isAlive() and simulator.isAlive():
            time.sleep(0.05)
    finally:
        pass
    multi_io_server.ready = False
    simulator.stop()