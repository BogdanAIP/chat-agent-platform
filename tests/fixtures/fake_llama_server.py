#!/usr/bin/env python3
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sys


if "--version" in sys.argv:
    print("fake llama.cpp 0.1.0-dev (build 10448, commit ad1de39e0)")
    raise SystemExit(0)


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-m", "--model", dest="model")
parser.add_argument("--mmproj")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, required=True)
args, _unknown = parser.parse_known_args()

if args.host != "127.0.0.1":
    raise SystemExit("fake runtime is loopback-only")
if not args.model or not args.mmproj:
    raise SystemExit("fake runtime requires model and mmproj arguments")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            payload = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(404)
        self.end_headers()


server = ThreadingHTTPServer((args.host, args.port), Handler)
server.serve_forever(poll_interval=0.1)
