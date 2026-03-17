import streamlit as st
import os
import time
from datetime import datetime
from PIL import Image
LOG_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "command_logs", "commands.txt")
KEYS_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "command_logs", "keystrokes.txt")

st.set_page_config(
    page_title="Command Logger",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }

    .metric-card {
        background: linear-gradient(135deg, #161b22, #21262d);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .log-row {
        background: #161b22;
        border-left: 3px solid #58a6ff;
        border-radius: 6px;
        padding: 10px 15px;
        margin: 6px 0;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    .log-time { color: #8b949e; font-size: 0.8rem; }
    .log-cmd  { color: #79c0ff; font-weight: 600; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f0f6fc;
        border-bottom: 1px solid #30363d;
        padding-bottom: 8px;
        margin: 20px 0 12px 0;
    }
    div[data-testid="stHorizontalBlock"] { gap: 1rem; }
    .stButton>button {
        background: #21262d;
        border: 1px solid #30363d;
        color: #c9d1d9;
        border-radius: 8px;
    }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


BANNER_PATH = os.path.join(os.path.dirname(__file__), "banner.png")


def get_current_command():
    """Read keystrokes.txt and reconstruct what's currently being typed since last [ENTER]."""
    if not os.path.exists(KEYS_FILE):
        return ""
    with open(KEYS_FILE, "r") as f:
        lines = f.readlines()
    # Find last [ENTER], take everything after it
    last_enter = -1
    for i, line in enumerate(lines):
        if "[ENTER]" in line:
            last_enter = i
    since_enter = lines[last_enter + 1:]
    # Reconstruct the in-progress command
    buf = []
    for line in since_enter:
        line = line.strip()
        if not line:
            continue
        key = line[26:].strip() if len(line) > 26 else ""
        if key == "[BACKSPACE]":
            if buf:
                buf.pop()
        elif key.startswith("[") and key.endswith("]"):
            pass  # ignore special keys in display
        else:
            buf.append(key)
    return "".join(buf)


def parse_logs():
    if not os.path.exists(LOG_FILE):
        return []
    entries = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ts = line[1:20]
                cmd = line[22:].strip()
                entries.append({"time": ts, "cmd": cmd})
            except Exception:
                entries.append({"time": "?", "cmd": line})
    return entries


# ── Banner ──────────────────────────────────────────────────────────────
if os.path.exists(BANNER_PATH):
    banner = Image.open(BANNER_PATH)
    banner = banner.resize((banner.width, banner.height // 2))
    st.image(banner, use_container_width=True)
else:
    st.warning("Banner image not found. Save banner.png to the project folder.")

# ── Controls ─────────────────────────────────────────────────────────────
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 4])
with col_ctrl1:
    auto_refresh = st.toggle("Live Mode", value=True)
with col_ctrl2:
    refresh_rate = st.selectbox("Refresh", [2, 5, 10], index=0, label_visibility="collapsed")

entries = parse_logs()

# ── Metrics ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 Overview</div>', unsafe_allow_html=True)
m1, m2 = st.columns(2)

total = len(entries)
unique = len(set(e["cmd"].split()[0] for e in entries if e["cmd"])) if entries else 0

for col, val, label in [
    (m1, total, "Total Commands"),
    (m2, unique, "Unique Programs"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

# ── Current Command ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">🎯 Current Command</div>', unsafe_allow_html=True)

@st.fragment(run_every=0.1)
def current_command_widget():
    typing = get_current_command()
    _, center, _ = st.columns([1, 2, 1])
    with center:
        display = f"$ {typing}▮" if typing else "&nbsp;"
        color = "#ff6b6b" if typing else "#444"
        st.markdown(f"""
        <div class="metric-card" style="padding: 30px; border-color: {'#ff4444' if typing else '#30363d'};">
            <div style="font-size:0.8rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Currently Typing</div>
            <div style="font-size:1.6rem; font-weight:700; color:{color}; font-family:'Courier New',monospace; min-height:2.2rem;">{display}</div>
        </div>
        """, unsafe_allow_html=True)

current_command_widget()

# ── Command Log ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Command Log</div>', unsafe_allow_html=True)
shown = entries[-30:] if len(entries) > 30 else entries
log_html = ""
for e in reversed(shown):
    log_html += f"""
    <div class="log-row">
        <span class="log-time">{e['time']}</span><br>
        <span class="log-cmd">$ {e['cmd']}</span>
    </div>"""
if not log_html:
    log_html = '<div class="log-row"><span class="log-time">Waiting for commands…</span></div>'
st.markdown(log_html, unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
