import socketserver as ss
import http.server as hs
from typing import Any, Dict, Tuple

class WebServer(ss.ThreadingTCPServer):
    def __init__(self, config: Dict[str, Any], address: Tuple[str, int], *args, **kwargs) -> None:
        self.screen_config = config
        super(WebServer, self).__init__(address, TCPHandler, *args, **kwargs)

class TCPHandler(hs.BaseHTTPRequestHandler, ss.StreamRequestHandler):
    def handle(self):
        super(TCPHandler, self).handle()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(f"""
<head>
  <title>Observ Web Interface</title>
</head>
<body onload="setup()">
test
</body>
<script>
function setup() {{
    request = new XMLHttpRequest();
    request.open("POST", "{self.headers._headers[0][1]}" , true);
    request.setRequestHeader('Content-Type', 'application/json');
    request.send(JSON.stringify(
{{
    action: "setup"
}}
    ));
}}
</script>
""".encode())

    def do_POST(self) -> None:
        print(self.headers)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()