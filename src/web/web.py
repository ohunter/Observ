import socketserver as ss
import http.server as hs
import json

from typing import Any, Callable, Dict, Tuple

import tiles as ti

class WebServer(ss.ThreadingTCPServer):
    def __init__(self, config: Dict[str, Any], address: Tuple[str, int], *args, **kwargs) -> None:
        self._config = config
        self.started = False
        super(WebServer, self).__init__(address, TCPHandler, *args, **kwargs)

    def initialize_screen(self, content):
        if not self.started:
            self.started = True
            self.tile_root = ti.tile.from_conf(self._config["screen"])
            self.screen_conf = json.dumps(self.tile_root.configuration())

        return self.screen_conf

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
        request = new XMLHttpRequest();
        request.onreadystatechange = function() {{
            if (this.readyState == 4 && and this.status == 200){{

            }}
        }}
        request.open("POST", "{self.headers.values()[1]}", true);
        request.setRequestHeader('Content-Type', 'application/json');
        request.send(JSON.stringify(
    {{
        action: "setup"
    }}
        ));
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

        response = ""

        if self.headers.get_content_type() == 'application/json':
            content = json.loads(content)

            response = _action_dict[content.pop('action', 'setup')](content)

            import pdb; pdb.set_trace()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response)