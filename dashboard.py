import streamlit as st
import os
import time
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

LOG_FILE    = os.path.join(os.path.expanduser("~"), "Desktop", "command_logs", "commands.txt")
KEYS_FILE   = os.path.join(os.path.expanduser("~"), "Desktop", "command_logs", "keystrokes.txt")
BANNER_PATH = os.path.join(os.path.dirname(__file__), "banner.png")

APP_NAME    = "SHADOWLOG"
APP_TAGLINE = "Real-time terminal command tracker"

st.set_page_config(page_title=APP_NAME, page_icon="💀", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .block-container { padding-top: 0 !important; padding-bottom: 1rem !important; }
    .metric-card {
        background: linear-gradient(135deg, #161b22, #21262d);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #58a6ff; line-height: 1.2; }
    .metric-label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .log-row {
        background: #161b22;
        border-left: 3px solid #58a6ff;
        border-radius: 5px;
        padding: 6px 12px;
        margin: 4px 0;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
    }
    .log-time { color: #8b949e; font-size: 0.75rem; }
    .log-cmd  { color: #79c0ff; font-weight: 600; }
    .section-header {
        font-size: 0.85rem;
        font-weight: 600;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid #21262d;
        padding-bottom: 4px;
        margin: 10px 0 8px 0;
    }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    div[data-testid="stHorizontalBlock"] { gap: 0.6rem; }
</style>
""", unsafe_allow_html=True)


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
        line = line.strip()
        if not line:
            continue
        key = line[26:].rstrip('\n') if len(line) > 26 else ""
        if key == "[BACKSPACE]":
            if buf: buf.pop()
        elif key.startswith("[") and key.endswith("]"):
            pass
        else:
            buf.append(key)
    return "".join(buf)


def parse_entries():
    if not os.path.exists(LOG_FILE):
        return []
    entries = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append({"time": line[1:20], "cmd": line[22:].strip()})
            except Exception:
                entries.append({"time": "?", "cmd": line})
    return entries


def make_banner():
    if not os.path.exists(BANNER_PATH):
        return None
    img = Image.open(BANNER_PATH).convert("RGBA")
    w, h = img.width, img.height // 4
    img = img.resize((w, h))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(h):
        alpha = int(180 * (i / h))
        draw.line([(0, i), (w, i)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", max(h // 3, 20))
        font_sub   = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   max(h // 7, 11))
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = font_title

    draw.text((22, h // 2 - h // 4 + 2), APP_NAME,    font=font_title, fill=(0, 0, 0, 180))
    draw.text((20, h // 2 - h // 4),     APP_NAME,    font=font_title, fill=(255, 255, 255, 255))
    draw.text((22, h // 2 + h // 8),     APP_TAGLINE, font=font_sub,   fill=(150, 200, 255, 220))

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return buf


# ── Banner ────────────────────────────────────────────────────────────────
banner = make_banner()
if banner:
    st.image(banner, use_container_width=True)
else:
    st.error("banner.png not found.")

# ── Controls ──────────────────────────────────────────────────────────────
c1, c2, _ = st.columns([1, 1, 6])
with c1:
    auto_refresh = st.toggle("Live", value=True)
with c2:
    refresh_rate = st.selectbox("Rate", [2, 5, 10], index=0, label_visibility="collapsed")

entries = parse_entries()

# ── Metrics + Current Command ─────────────────────────────────────────────
left, right = st.columns([1, 2])

with left:
    st.markdown('<div class="section-header">📊 Overview</div>', unsafe_allow_html=True)
    total  = len(entries)
    unique = len(set(e["cmd"].split()[0] for e in entries if e["cmd"])) if entries else 0
    m1, m2 = st.columns(2)
    for col, val, label in [(m1, total, "Commands"), (m2, unique, "Programs")]:
        with col:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-header">🎯 Current Command</div>', unsafe_allow_html=True)

    @st.fragment(run_every=0.1)
    def current_command_widget():
        typing  = get_current_command()
        display = f"$ {typing}▮" if typing else "&#x25AE; idle"
        color   = "#ff6b6b" if typing else "#444"
        border  = "#ff4444" if typing else "#30363d"
        st.markdown(f"""<div class="metric-card" style="padding:14px 20px; border-color:{border};">
            <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Typing</div>
            <div style="font-size:1.3rem;font-weight:700;color:{color};font-family:'Courier New',monospace;min-height:1.8rem;">{display}</div>
        </div>""", unsafe_allow_html=True)

    current_command_widget()

# ── Command Log ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Command Log</div>', unsafe_allow_html=True)
shown    = entries[-30:]
log_html = "".join(f"""<div class="log-row">
    <span class="log-time">{e['time']}</span><br>
    <span class="log-cmd">$ {e['cmd']}</span>
</div>""" for e in reversed(shown))
st.markdown(
    log_html or '<div class="log-row"><span class="log-time">Waiting for commands…</span></div>',
    unsafe_allow_html=True
)

# ── Auto-refresh ──────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
