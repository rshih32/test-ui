import os
import json
import threading
import streamlit as st
import streamlit.components.v1 as components
from http.server import HTTPServer, BaseHTTPRequestHandler

KEYS_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "command_logs", "keystrokes.txt")
API_PORT  = 8502


def get_current_command():
    if not os.path.exists(KEYS_FILE):
        return ""
    with open(KEYS_FILE, "r") as f:
        lines = f.readlines()
    last_enter = -1
    for i, line in enumerate(lines):
        if "[ENTER]" in line:
            last_enter = i
    buf = []
    for line in lines[last_enter + 1:]:
        parts = line.split('] ', 1)
        if len(parts) < 2:
            continue
        key = parts[1].rstrip('\r\n')
        if key == "[BACKSPACE]":
            if buf: buf.pop()
        elif key.startswith("[") and key.endswith("]"):
            pass
        else:
            buf.append(key)
    return "".join(buf)


class _KeystrokeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = json.dumps({"cmd": get_current_command()}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *args): pass


@st.cache_resource
def start_server():
    server = HTTPServer(("localhost", API_PORT), _KeystrokeHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


def render():
    """Render the real-time current command widget (JS polls the keystroke API at 5ms)."""
    start_server()
    components.html(f"""
    <div id="cmd" style="
        background: linear-gradient(135deg, #161b22, #21262d);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 20px;
        font-family: 'Courier New', monospace;
        font-size: 1.3rem;
        font-weight: 700;
        min-height: 1.8rem;
    ">
        <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Typing</div>
        <div id="cmd-text" style="color:#444;">&#x25AE; idle</div>
    </div>
    <script>
      setInterval(() => {{
        fetch('http://localhost:{API_PORT}')
          .then(r => r.json())
          .then(d => {{
            const box  = document.getElementById('cmd');
            const text = document.getElementById('cmd-text');
            if (d.cmd) {{
              box.style.borderColor = '#ff4444';
              text.style.color      = '#ff6b6b';
              text.textContent      = '$ ' + d.cmd + '▮';
            }} else {{
              box.style.borderColor = '#30363d';
              text.style.color      = '#444';
              text.innerHTML        = '&#x25AE; idle';
            }}
          }})
          .catch(() => {{}});
      }}, 5);
    </script>
    """, height=90)
