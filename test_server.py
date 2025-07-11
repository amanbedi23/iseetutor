#!/usr/bin/env python3
"""Simple HTTP server to test network connectivity"""
import http.server
import socketserver

PORT = 8000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Jetson Server is Working!</h1>")

with socketserver.TCPServer(("0.0.0.0", PORT), MyHandler) as httpd:
    print(f"Server running at http://0.0.0.0:{PORT}")
    print(f"Access from: http://192.168.10.118:{PORT}")
    httpd.serve_forever()