import http.server as hs
import json
import multiprocessing as mp
import os
import queue as qu
import socketserver as ss
import threading as th

from inspect import getsourcefile
from typing import Any, Callable, Dict, Tuple, Union

import tiles as ti

class WebServer(ss.ThreadingTCPServer):
    def __init__(self, config: Dict[str, Any], mode: str, address: Tuple[str, int], *args, **kwargs) -> None:
        self._config = config
        self.started = False

        assert self.mode in ["thread", "process"], "Unknown execution mode specified. If you believe this to be an error, submit a PR."

        self.mode = mode
        super(WebServer, self).__init__(address, TCPHandler, *args, **kwargs)

    def initialize_screen(self, content):
        if not self.started:
            self.started = True
            self.tile_root = ti.tile.from_conf(self._config["screen"])
            self.screen_conf = json.dumps(self.tile_root.configuration())

            if self.mode == "thread":
                self.remote = th.Thread
                self.queue = qu.Queue()
            elif self.mode == "process":
                self.remote = mp.Process
                self.queue = mp.Queue()

        return self.screen_conf

    def update_screen(self, content):
        pass


class TCPHandler(hs.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super(TCPHandler, self).__init__(*args, **kwargs)

    def do_GET(self):
        try:
            with open(f"{os.path.dirname(os.path.abspath(getsourcefile(lambda:0)))}/base.html", 'r') as fi:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(fi.read().encode())
                return
        except OSError:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        _action_dict : Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "setup" : self.server.initialize_screen,
            "update" : self.server.update_screen
        }

        content_len = int(self.headers.values()[self.headers.keys().index("Content-Length")])
        content = self.rfile.read(content_len).decode("utf-8")

        response = ""

        if self.headers.get_content_type() == 'application/json':
            content = json.loads(content)

            response = _action_dict[content.pop('action', 'setup')](content)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode())
