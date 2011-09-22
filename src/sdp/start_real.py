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
import central
import time

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--host', dest = 'host', help = 'central server HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('-p', '--port', dest = 'port', help = 'central server PORT (default 9999)', type = 'int', default = 9999)
    parser.add_option('-z', '--zoom', dest = 'zoom', help = 'pitch zoom (positive integers only); default is 4', type = 'int', default = 4)
    parser.add_option('-v', '--verbose', dest = 'verbose', help = 'show more information', action = 'store_true', default = False)
    options = parser.parse_args()[0]
    
    SynchronizedPrint(options.verbose).start()
    knowledge_server = central.KnowledgeServer(options.host, options.port, options.verbose)
    knowledge_server.start()
    
    SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' Waiting for the knowledge server to start')
    while not knowledge_server.ready:
        time.sleep(0.001)
    SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' Knowledge server started')
    
    modules = {
        'logger': ['python proxy.py --host ' + options.host + ' -p ' + str(options.port) + ' python logger.py', None],
        'kicker': ['python proxy.py --host ' + options.host + ' -p ' + str(options.port) + ' python kicker.py', None],
    }
    
    try:
        common.module_starter.ModuleStarter('python visualiser.py --host ' + options.host + ' -p ' + str(options.port) + ' -z ' + str(options.zoom)).start()
        
        while knowledge_server.isAlive():
            for (module, module_data) in modules.items():
                if knowledge_server.have_module(module):
                    continue
                if module_data[1] == None or not module_data[1].isAlive():
                    module_data[1] = common.module_starter.ModuleStarter(module_data[0])
                    module_data[1].start()
            
            time.sleep(0.05)
    except:
        print 'Exception, exiting'
        pass
    finally:
        knowledge_server.ready = False
        for (module, module_data) in modules.items():
            if module_data[1] != None:
                module_data[1].stop()