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

from common.synchronized_print import SynchronizedPrint
import threading
import socket
import Queue
import time

class MessageProxy(threading.Thread):
    def __init__(self, host, port, show_incoming = False, show_outgoing = False):
        threading.Thread.__init__(self, name = 'message proxy')
        self.daemon = True
        self.keep_running = True
        self._host = host
        self._port = port
        self.incoming = Queue.Queue()
        self.outgoing = Queue.Queue()
        self._show_incoming = show_incoming
        self._show_outgoing = show_outgoing
    
    def stop_with_msg(self, msg):
        self.keep_running = False
        print msg
    
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._host, self._port))
        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        sock.setblocking(False)
        
        buf = ''
        while self.keep_running:
            any_work = False
            
            if not self.outgoing.empty():
                msg = self.outgoing.get().rstrip()
                if self._show_incoming:
                    SynchronizedPrint.queue.put_nowait('client: ' + msg)
                while not self.outgoing.empty():
                    t = self.outgoing.get().rstrip()
                    msg += '\n' + t
                    if self._show_incoming:
                        SynchronizedPrint.queue.put_nowait('client: ' + t)
                if msg != '':
                    while True:
                        try:
                            sock.send(msg + '\n')
                        except socket.error, (errno, _):
                            if errno == 10035 or errno == 11:
                                time.sleep(0.001)
                                continue
                            raise
                        else:
                            break
                any_work = True
            
            try:
                t = sock.recv(4096)
                if t == '':
                    self.incoming.put('/central/exit', False)
                    self.stop_with_msg('unable to read from server (socket closed)')
                else:
                    any_work = True
                    buf += t
                    while True:
                        pos = buf.find('\n')
                        if pos == -1:
                            break
                        s = buf[:pos].rstrip()
                        if s != '':
                            self.incoming.put(s, False)
                            if self._show_outgoing:
                                SynchronizedPrint.queue.put_nowait('server: ' + s)
                        buf = buf[pos + 1:]
            except socket.error, (errno, _):
                if errno != 10035 and errno != 11:
                    self.incoming.put('/central/exit', False)
                    self.stop_with_msg('unable to read from server (socket error)')
            except:
                self.incoming.put('/central/exit', False)
                self.stop_with_msg('unable to read from server (unknown error)')
            
            if not any_work:
                time.sleep(0.001)

class StreamToServer(threading.Thread):
    def __init__(self, message_proxy, stream):
        threading.Thread.__init__(self, name = 'stream->server')
        self.daemon = True
        self._message_proxy = message_proxy
        self._stream = stream
    
    def run(self):
        while self._message_proxy.keep_running and self._message_proxy.isAlive():
            s = self._stream.readline()
            if s == '':
                self._message_proxy.stop_with_msg('unable to read from stream (pipe closed)')
            else:
                s = s.rstrip()
                self._message_proxy.outgoing.put(s, False)

class ServerToStream(threading.Thread):
    def __init__(self, message_proxy, stream):
        threading.Thread.__init__(self, name = 'server->stream')
        self.daemon = True
        self._message_proxy = message_proxy
        self._stream = stream
    
    def run(self):
        while self._message_proxy.keep_running and self._message_proxy.isAlive():
            if not self._message_proxy.incoming.empty():
                msg = self._message_proxy.incoming.get(True)
                while not self._message_proxy.incoming.empty():
                    msg += '\n' + self._message_proxy.incoming.get().rstrip()
                try:
                    self._stream.write(msg + '\n')
                    self._stream.flush()
                except:
                    self._message_proxy.stop_with_msg('unable to write to stream (pipe closed)')
            else:
                time.sleep(0.001)