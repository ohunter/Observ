import http.server as hs
import json
import multiprocessing as mp
import os
import queue as qu
import socketserver as ss
import threading as th
import time

from inspect import getsourcefile
from itertools import chain
from typing import Any, Callable, Dict, Tuple, Union

import tiles as ti
import sched as sc

def _monitor_execution(root: ti.tile, sched: sc.scheduler, queue: Union[qu.Queue, mp.Queue]):
    root.start_concurrent()

    for t, tiles in sched.next_timing():
        data = {k : v for k,v in chain(*[tile.get_data().items() for tile in tiles])}

        import pdb; pdb.set_trace()

        queue.put_nowait(data)

        time.sleep(t)

class WebServer(ss.ThreadingTCPServer):
    def __init__(self, config: Dict[str, Any], mode: str, address: Tuple[str, int], *args, **kwargs) -> None:
        self._config = config
        self.started = False
        self.data = {}

        assert mode in ["thread", "process"], "Unknown execution mode specified. If you believe this to be an error, submit a PR."

        self.mode = mode
        super(WebServer, self).__init__(address, TCPHandler, *args, **kwargs)

    def initialize_screen(self, content):
        if not self.started:
            self.tile_root = ti.tile.from_conf(self._config["screen"])
            self.screen_conf = json.dumps(self.tile_root.configuration())

            if self.mode == "thread":
                self.remote = th.Thread
                self.queue = qu.Queue()
            elif self.mode == "process":
                self.remote = mp.Process
                self.queue = mp.Queue()

            sched = sc.scheduler(self.tile_root.timing())

            kwargs = {
                "root" : self.tile_root,
                "sched" : sched,
                "queue" : self.queue,
                }

            self.remote = self.remote(target=_monitor_execution, kwargs=kwargs, daemon=True)
            self.remote.start()
            self.started = True

        self.data[content['client']] = []

        return self.screen_conf

    def update_screen(self, content):
        # TODO: find a better solution for storing the data per client
        new_data = []
        while not self.queue.empty():
            new_data.append(self.queue.get_nowait())

        for key in self.data:
            self.data[key] += new_data

        return self.data[content['client']].pop()

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

            tmp = content['action']

            content.update({"client" : self.client_address})
            response = _action_dict[content.pop('action', 'setup')](content)

            if tmp == "update":
                import pdb; pdb.set_trace()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode())
