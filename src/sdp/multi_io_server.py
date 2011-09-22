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
from common.synchronized_print import SynchronizedPrint
from common.utility import current_time
from optparse import OptionParser
import common.host_finder
import SocketServer
import threading
import socket
import Queue
import time

class MultiIOServer(threading.Thread):
    client_group = {}
    message_queues = {}
    next_client_number = 1
    client_lock = threading.Lock()
    verbose = False
    
    def __init__(self, host, port, verbose):
        threading.Thread.__init__(self)
        self.daemon = True
        self.host = host
        self.port = port
        self.ready = False
        MultiIOServer.verbose = verbose
    
    class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
        def __init__(self, server_address, RequestHandlerClass):
            self.allow_reuse_address = True
            SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
    
    class TCPHandler(SocketServer.BaseRequestHandler):
        class MessageSender(threading.Thread):
            def __init__(self, client_id, sock):
                threading.Thread.__init__(self)
                self.daemon = True
                self._client_id = client_id
                self._sock = sock
                self.keep_running = True
            
            def run(self):
                msg_queue = MultiIOServer.message_queues[self._client_id]
                
                while self.keep_running:
                    try:
                        messages = ''
                        while not msg_queue.empty():
                            messages += msg_queue.get() + '\n'
                        if messages == '':
                            time.sleep(0.001)
                        else:
                            self._sock.send(messages)
                    except:
                        break
        
        def _handle_msg(self, from_id, msg):
            my_group = MultiIOServer.client_group[from_id]
            parts = msg.split(' ', 2)
            if len(parts) == 2 and parts[0] == '/general/multi_io_server/identify':
                MultiIOServer.client_group[from_id] = parts[1].strip()
                self._broadcast(from_id, '/multi_io_server/client_identified ' + str(from_id) + ' ' + parts[1].strip() + ' ' + current_time())
            else:
                for (client_id, client_group) in MultiIOServer.client_group.items():
                    if from_id == client_id or client_group == None or my_group == client_group:
                        continue
                    
                    if MultiIOServer.verbose:
                        SynchronizedPrint.queue.put_nowait(current_time()[11:-3] + ' ' + str(from_id) + '->' + str(client_id) + ': ' + msg)
                    MultiIOServer.message_queues[client_id].put_nowait(msg)
        
        def _broadcast(self, from_id, msg):
            for (client_id, client_group) in MultiIOServer.client_group.items():
                if from_id == client_id or client_group == None:
                    continue
                SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' Broadcast ' + str(from_id) + '->' + str(client_id) + ': ' + msg)
                MultiIOServer.message_queues[client_id].put_nowait(msg)
        
        def handle(self):
            sock = self.request
            sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            
            with MultiIOServer.client_lock:
                client_id = MultiIOServer.next_client_number
                self._broadcast(client_id, '/multi_io_server/client_connected ' + str(client_id) + ' ' + current_time())
                MultiIOServer.message_queues[client_id] = Queue.Queue()
                MultiIOServer.client_group[client_id] = None
                MultiIOServer.next_client_number += 1
            sender = self.MessageSender(client_id, sock)
            sender.start()
            
            buf = ''
            while sender.keep_running:
                try:
                    t = sock.recv(4096)
                    if t == '':
                        break
                    else:
                        buf += t
                        while True:
                            pos = buf.find('\n')
                            if pos == -1:
                                break
                            s = buf[:pos].rstrip()
                            if s != '':
                                self._handle_msg(client_id, s)
                            buf = buf[pos + 1:]
                except socket.error, (errno, _):
                    if errno == 10035 or errno == 11:
                        time.sleep(0.001)
                        continue
                    break
                except:
                    break
            
            self._broadcast(client_id, '/multi_io_server/client_disconnected ' + str(client_id) + ' ' + current_time())
            MultiIOServer.client_group[client_id] = None
            sender.keep_running = False
    
    def run(self):
        server = self.ThreadingTCPServer((self.host, self.port), self.TCPHandler)
        server.daemon_threads = True
        
        server_thread = threading.Thread(target = server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        self.ready = True
        
        SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' Listening on ' + self.host + ':' + str(self.port))
        while self.ready and server_thread.isAlive():
            time.sleep(0.05)
        self.ready = False

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('--host', dest = 'host', help = 'listen on HOST (default read from host.txt line 1, otherwise machine name)',
        default = common.host_finder.get_host())
    parser.add_option('-p', '--port', dest = 'port', help = 'listen on PORT (default 19999)', type = 'int', default = 19999)
    parser.add_option('-v', '--verbose', dest = 'verbose', help = 'show more information', action = 'store_true', default = False)
    options = parser.parse_args()[0]
    
    SynchronizedPrint(options.verbose).start()
    multi_io_server = MultiIOServer(options.host, options.port, options.verbose)
    multi_io_server.start()
    
    while multi_io_server.isAlive():
        time.sleep(0.05)