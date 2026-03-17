import streamlit as st
import os
import time
from datetime import datetime
from collections import Counter
from PIL import Image
LOG_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "command_logs", "commands.txt")

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
    st.image(Image.open(BANNER_PATH), use_container_width=True)
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
m1, m2, m3, m4 = st.columns(4)

total = len(entries)
unique = len(set(e["cmd"].split()[0] for e in entries if e["cmd"])) if entries else 0
last_cmd = entries[-1]["cmd"] if entries else "—"
last_time = entries[-1]["time"] if entries else "—"

for col, val, label in [
    (m1, total, "Total Commands"),
    (m2, unique, "Unique Programs"),
    (m3, last_cmd[:18] + ("…" if len(last_cmd) > 18 else ""), "Last Command"),
    (m4, last_time[11:] if last_time != "—" else "—", "Last Run"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
        </div>""", unsafe_allow_html=True)

# ── Current Tracker ───────────────────────────────────────────────────────
st.markdown('<div class="section-header">🎯 Current Tracker</div>', unsafe_allow_html=True)
_, center, _ = st.columns([1, 2, 1])
with center:
    current_cmd = entries[-1]["cmd"] if entries else "No commands yet"
    current_time = entries[-1]["time"] if entries else "—"
    st.markdown(f"""
    <div class="metric-card" style="padding: 30px; border-color: #ff4444;">
        <div style="font-size:0.8rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">Last Command Tracked</div>
        <div style="font-size:1.6rem; font-weight:700; color:#ff6b6b; font-family:'Courier New',monospace;">$ {current_cmd}</div>
        <div style="font-size:0.85rem; color:#58a6ff; margin-top:10px;">{current_time}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Two-column layout ─────────────────────────────────────────────────────
left, right = st.columns([3, 2])

with left:
    st.markdown('<div class="section-header">📋 Command Log</div>', unsafe_allow_html=True)
    log_placeholder = st.empty()
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
    log_placeholder.markdown(log_html, unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-header">🏆 Top Commands</div>', unsafe_allow_html=True)
    if entries:
        base_cmds = [e["cmd"].split()[0] for e in entries if e["cmd"]]
        counts = Counter(base_cmds).most_common(10)
        cmds, vals = zip(*counts)
        st.bar_chart({"Count": dict(zip(cmds, vals))}, color="#58a6ff")
    else:
        st.info("No commands logged yet.")

    st.markdown('<div class="section-header">🕐 Recent Activity</div>', unsafe_allow_html=True)
    if entries:
        recent = entries[-5:]
        for e in reversed(recent):
            st.markdown(f"`{e['time'][11:]}` — **{e['cmd'][:35]}**")
    else:
        st.caption("Nothing yet.")

# ── Auto-refresh ──────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
