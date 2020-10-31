import socketserver as ss
import http.server as hs
import json

from typing import Any, Callable, Dict, Tuple

import tiles as ti

class WebServer(ss.ThreadingTCPServer):
    def __init__(self, config: Dict[str, Any], address: Tuple[str, int], *args, **kwargs) -> None:
        self.screen_config = config
        self.started = False
        super(WebServer, self).__init__(address, TCPHandler, *args, **kwargs)

    def initialize_screen(self, content):
        if not self.started:
            self.tile_root = ti.tile.from_conf(self.screen_config["screen"])

        

    def update_screen(self, content):
        pass


class TCPHandler(hs.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super(TCPHandler, self).__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(f"""
<html>
    <head>
        <title>Observ Web Interface</title>
    </head>
    <body onload="setup()">
    </body>
    <script>
    function setup() {{
        request = new XMLHttpRequest();\n
        request.open("POST", "{self.headers.values()[1]}", true);\n
        request.setRequestHeader('Content-Type', 'application/json');\n
        request.send(JSON.stringify(\n
    {{\n
        action: "setup"\n
    }}\n
        ));\n
    }}
    </script>
</html>
""".encode())

    def do_POST(self) -> None:
        _action_dict : Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "setup" : self.server.initialize_screen,
            "update" : self.server.update_screen
        }

        content_len = int(self.headers.values()[self.headers.keys().index("Content-Length")])
        content = self.rfile.read(content_len).decode("utf-8")

        if self.headers.get_content_type() == 'application/json':
            content = json.loads(content)

            _action_dict[content.pop('action', 'setup')](content)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()