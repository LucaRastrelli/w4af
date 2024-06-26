"""
http_daemon.py

Copyright 2013 Andres Riancho

This file is part of w4af, https://w4af.net/ .

w4af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w4af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w4af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import http.server
import threading
import socketserver
import time


class LoggedRequest(object):
    def __init__(self, command, path, request_version, headers, request_body):
        self.command = command
        self.path = path
        self.request_version = request_version
        self.headers = dict(headers)
        self.request_body = request_body 

    def __repr__(self):
        return '<LoggedRequest %s %s %s>' % (self.command, self.path,
                                             self.request_version)


class ServerHandler(http.server.SimpleHTTPRequestHandler):

    requests = []
    
    def do_GET(self):
        """Serve a GET request."""
        self.send_response(200)
        self.end_headers()        
        
        self.wfile.write(b'ABCDEF\n')

    def do_POST(self):
        """Serve a POST request."""
        self.send_response(200)
        self.end_headers()        
        
        self.wfile.write(b'ABCDEF\n')

    def log_message(self, fmt, *args):
        pass
    
    def handle_one_request(self):
        # TODO: Add support for reading self.rfile
        request_body = None
        
        http.server.SimpleHTTPRequestHandler.handle_one_request(self)
        self.requests.append(LoggedRequest(self.command, self.path,
                                           self.request_version, self.headers,
                                           request_body))
        

class HTTPDaemon(threading.Thread):
    """
    Trivial HTTP daemon that binds to an open port that can be retrieved by
    get_port()
    """
    
    def __init__(self):
        super(HTTPDaemon, self).__init__()
        self.daemon = True
        self.server = None
        
    def run(self):
        # Zero in the port means: bind to any free port
        self.server = socketserver.TCPServer(('127.0.0.1', 0),
                                             ServerHandler)
    
        self.server.serve_forever()
    
    def get_port(self):
        if self.server is not None:
            return self.server.server_address[1]
    
    def wait_for_start(self):
        while self.server is None or self.get_port() is None:
            time.sleep(0.5)
    
    @property
    def requests(self):
        return self.server.RequestHandlerClass.requests
    
    def shutdown(self):
        self.server.RequestHandlerClass.requests = []
        self.server.shutdown()
