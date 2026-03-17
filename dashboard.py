import streamlit as st
import os
import time
from datetime import datetime
from collections import Counter
from PIL import Image, ImageDraw, ImageFont
import io

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


def make_banner():
    w, h = 900, 160
    img = Image.new("RGB", (w, h), "#0d1117")
    draw = ImageDraw.Draw(img)

    for i in range(h):
        r = int(13 + (33 - 13) * i / h)
        g = int(17 + (43 - 17) * i / h)
        b = int(23 + (55 - 23) * i / h)
        draw.line([(0, i), (w, i)], fill=(r, g, b))

    # Grid lines
    for x in range(0, w, 40):
        draw.line([(x, 0), (x, h)], fill=(30, 40, 50), width=1)
    for y in range(0, h, 40):
        draw.line([(0, y), (w, y)], fill=(30, 40, 50), width=1)

    # Glow circles
    for cx, cy, rad, col in [
        (80, 80, 55, (88, 166, 255, 60)),
        (820, 80, 40, (121, 192, 255, 40)),
        (450, 40, 25, (88, 166, 255, 30)),
    ]:
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=col)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

    # Terminal icon
    draw.rounded_rectangle([30, 30, 120, 130], radius=10, fill="#161b22", outline="#58a6ff", width=2)
    draw.text((47, 45), ">_", fill="#58a6ff")
    draw.line([(45, 75), (105, 75)], fill="#30363d", width=1)
    for i, line in enumerate(["$ ls -la", "$ cd /home", "$ git log"]):
        draw.text((45, 85 + i * 13), line, fill="#8b949e")

    try:
        font_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 38)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
    except Exception:
        font_big = ImageFont.load_default()
        font_sub = font_big

    draw.text((148, 42), "COMMAND LOGGER", font=font_big, fill="#f0f6fc")
    draw.text((150, 90), "Real-time terminal command tracking dashboard", font=font_sub, fill="#8b949e")

    now_str = datetime.now().strftime("Last updated: %Y-%m-%d %H:%M:%S")
    draw.text((150, 115), now_str, font=font_sub, fill="#58a6ff")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


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
st.image(make_banner(), use_container_width=True)

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
