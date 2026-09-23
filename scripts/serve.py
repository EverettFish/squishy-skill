#!/usr/bin/env python3
"""Serve a squishy locally without a package manager."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.js':'text/javascript','.glb':'model/gltf-binary','.json':'application/json'}
    def end_headers(self):
        self.send_header('Cache-Control','no-cache');super().end_headers()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--port',type=int,default=4173);args=p.parse_args()
    root=args.directory.resolve()
    if not (root/'index.html').is_file():p.error('This directory does not contain index.html')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(root)))
    print('Local: http://127.0.0.1:'+str(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
