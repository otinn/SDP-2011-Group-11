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
from common.utility import current_time, convert_time
from optparse import OptionParser
import common.host_finder
import SocketServer
import threading
import datetime
import socket
import Queue
import time
import re

class Message(object):
    def __init__(self, msg, target_id, received, expires):
        self.msg = msg
        self.target_id = target_id
        self.received = received
        self._expires = expires
    
    def is_valid(self):
        if self._expires == None:
            return True
        return current_time() < self._expires

class KnowledgeServer(threading.Thread):
    REQUIRED = ['robot', 'vision', 'planner', 'movement', 'kicker', 'logger']
    LISTENERS = {
        'robot':    ['/movement/request/*', '/movement/order/*', '/kicker/request/*', '/kicker/order/*', '/manual/simulator/*', '/planner/move',
                     '/planner/move_rev', '/vision/*', '/general/vision/pong', '/general/state/*', '/general/robot/*'], # TODO: remove this ugly hack
        'kicker':   ['/planner/kick', '/planner/lower_kicker'],
        'planner':  ['/vision/*', '/general/state/*'],
        'movement': ['/planner/move', '/planner/move_rev', '/vision/*'],
        'vision':   ['/general/vision/*'],
        'logger':   [],
        'manual':   []
    }
    CENTRAL_CLIENT = 0
    next_client_number = 1
    client_lock = threading.Lock()
    connected_clients = {0: (None, 'central', 'Central')}
    incoming_queue = Queue.Queue()
    received_messages_for = {}
    verbose = False
    
    def __init__(self, host, port, verbose):
        threading.Thread.__init__(self)
        self.daemon = True
        self.host = host
        self.port = port
        self.ready = False
        KnowledgeServer.verbose = verbose
    
    class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
        def __init__(self, server_address, RequestHandlerClass):
            self.allow_reuse_address = True
            SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
    
    class MyTCPHandler(SocketServer.BaseRequestHandler):
        class MessageSender(threading.Thread):
            def __init__(self, client_id):
                threading.Thread.__init__(self)
                self.daemon = True
                self.client_id = client_id
            
            def run(self):
                while True:
                    client_type = KnowledgeServer.connected_clients[self.client_id][1]
                    if client_type in KnowledgeServer.received_messages_for.keys():
                        break
                    time.sleep(0.001)
                msg_list = KnowledgeServer.received_messages_for[client_type]
                log_prefix = '/central/sent_message ' + client_type + ' ' + str(self.client_id) + ' '
                
                pos = 0
                while True:
                    try:
                        num = 0
                        old_pos = pos
                        messages = ''
                        while num < 5 and pos < len(msg_list):
                            msg = msg_list[pos]
                            if msg.is_valid() and (msg.target_id == -1 or msg.target_id == self.client_id):
                                if client_type != 'logger':
                                    KnowledgeServer.received_messages_for['logger'].append(Message(log_prefix + current_time() + ' ' + msg.msg, -1, current_time(), None))
                                messages += msg.msg + '\n'
                            pos += 1
                            num += 1
                        if pos == old_pos:
                            time.sleep(0.001)
                        else:
                            KnowledgeServer.connected_clients[self.client_id][0].send(messages)
                    except:
                        break
        
        def handle(self):
            sock = self.request
            sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
            
            with KnowledgeServer.client_lock:
                client_id = KnowledgeServer.next_client_number
                if not KnowledgeServer.verbose:
                    SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' Client ' + str(client_id) + ' connected')
                KnowledgeServer.incoming_queue.put_nowait((KnowledgeServer.CENTRAL_CLIENT, '/central/client_connected ' + str(client_id), current_time()))
                KnowledgeServer.connected_clients[client_id] = [sock, 'unknown', 'unknown', current_time(), 'secondary']
                KnowledgeServer.next_client_number += 1
            self.MessageSender(client_id).start()
            
            buf = ''
            while True:
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
                                KnowledgeServer.incoming_queue.put_nowait((client_id, s, current_time()))
                            buf = buf[pos + 1:]
                except socket.error, (errno, _):
                    if errno == 10035 or errno == 11:
                        time.sleep(0.001)
                        continue
                    break
                except:
                    break
            
            if not KnowledgeServer.verbose:
                SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' Client ' + str(client_id) + ' disconnected')
            KnowledgeServer.incoming_queue.put_nowait((KnowledgeServer.CENTRAL_CLIENT, '/central/client_disconnected ' + str(client_id), current_time()))
            KnowledgeServer.connected_clients[client_id][0] = None
    
    class MessagePasser(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.daemon = True
        
        def mask_matches(self, mask, msg):
            if mask[-1:] == '*':
                return msg[:len(mask) - 1] == mask[:-1]
            elif msg[:len(mask)] == mask:
                return len(msg) == len(mask) or msg[len(mask)] == ' '
            return False
        
        def pass_regular_messages(self, client_id, msg, received, expires):
            for target, interests in KnowledgeServer.LISTENERS.items():
                for mask in interests:
                    if self.mask_matches(mask, msg):
                        KnowledgeServer.received_messages_for[target].append(Message(msg, -1, received, expires))
                        break
        
        def identify_client(self, client_id, msg):
            parts = msg.split(' ', 4)
            if len(parts) != 5 or parts[0] != '/general/identify':
                return
            types = []
            for key in KnowledgeServer.LISTENERS.keys():
                types.append(re.escape(key))
            match = re.match('/general/identify\s+(' + '|'.join(types) + ')\s+(primary|secondary)\s+([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]+)\s+(.+)$', msg)
            if match == None:
                return
            
            SynchronizedPrint.important.put_nowait(current_time()[11:-3] + ' Client ' + str(client_id) + ' recognised as type ' + match.group(1) + '(' + match.group(2) + ', ' + match.group(10) + ')')
            KnowledgeServer.connected_clients[client_id][1] = match.group(1)
            KnowledgeServer.connected_clients[client_id][2] = match.group(10)
            KnowledgeServer.connected_clients[client_id][4] = match.group(2)
        
        def run(self):
            vision_delta = datetime.timedelta(minutes = 1)
            
            while True:
                client_id, msg, received = KnowledgeServer.incoming_queue.get(True)
                SynchronizedPrint.queue.put_nowait(received[11:-3] + ' in(' + str(client_id) + ', ' + KnowledgeServer.connected_clients[client_id][1] + '): ' + msg)
                self.pass_regular_messages(client_id, msg, received, convert_time(datetime.datetime.now() + vision_delta))
                self.identify_client(client_id, msg)
                # add message for loggers
                KnowledgeServer.received_messages_for['logger'].append(Message('/central/received_message ' + KnowledgeServer.connected_clients[client_id][1] +
                    ' ' + str(client_id) + ' ' + received + ' ' + msg, -1, received, None))
    
    def have_module(self, type):
        for temp in KnowledgeServer.connected_clients.values():
            if temp[0] != None and type == temp[1] and temp[4] == 'primary':
                return True
        return False
    
    def run(self):
        for client_type in self.LISTENERS.keys():
            KnowledgeServer.received_messages_for[client_type] = []
        self.MessagePasser().start()
        
        server = self.ThreadingTCPServer((self.host, self.port), self.MyTCPHandler)
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
    parser.add_option('-p', '--port', dest = 'port', help = 'listen on PORT (default read from host.txt line 2, otherwise 9999)', type = 'int',
        default = common.host_finder.get_port())
    parser.add_option('-v', '--verbose', dest = 'verbose', help = 'show more information', action = 'store_true', default = False)
    options = parser.parse_args()[0]
    
    SynchronizedPrint(options.verbose).start()
    knowledge_server = KnowledgeServer(options.host, options.port, options.verbose)
    knowledge_server.start()
    
    while knowledge_server.isAlive():
        time.sleep(0.05)