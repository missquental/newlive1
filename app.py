import streamlit as st
import gdown
import os
import subprocess
import threading
import time
from pathlib import Path
import streamlit.components.v1 as components

# ===============================
# KONFIGURASI
# ===============================
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1d7fpbrOI9q9Yl6w99-yZGNMB30XNyugf"
VIDEO_DIR = "videos"

Path(VIDEO_DIR).mkdir(exist_ok=True)

# ===============================
# DOWNLOAD GOOGLE DRIVE
# ===============================
def download_drive():
    gdown.download_folder(
        url=DRIVE_FOLDER_URL,
        output=VIDEO_DIR,
        quiet=False,
        use_cookies=False
    )

# ===============================
# FFMPEG STREAM
# ===============================
def run_ffmpeg(video_path, stream_key, is_shorts, log_cb):
    rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"

    scale = ["-vf", "scale=720:1280"] if is_shorts else []

    cmd = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",
        "-i", video_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-b:v", "2500k",
        "-maxrate", "2500k",
        "-bufsize", "5000k",
        "-g", "60",
        "-keyint_min", "60",
        "-c:a", "aac",
        "-b:a", "128k",
        "-f", "flv",
        *scale,
        rtmp_url
    ]

    log_cb(" ".join(cmd))

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in process.stdout:
        log_cb(line.strip())

# ===============================
# UI STREAMLIT
# ===============================
st.set_page_config("Drive → Live YouTube", "📡", layout="wide")
st.title("📡 Google Drive → Live YouTube")

# ===== IKLAN =====
if st.checkbox("Tampilkan Iklan", True):
    components.html(
        """
        <div style="padding:15px;border-radius:10px;background:#f5f5f5">
        <script type='text/javascript'
        src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'>
        </script>
        </div>
        """,
        height=250
    )

# ===== DOWNLOAD =====
if st.button("📥 Download Video dari Google Drive"):
    with st.spinner("Download..."):
        download_drive()
    st.success("Download selesai")

# ===== LIST VIDEO =====
videos = sorted([
    f for f in os.listdir(VIDEO_DIR)
    if f.lower().endswith((".mp4", ".flv"))
])

video_path = None
if videos:
    selected = st.selectbox("Pilih Video", videos)
    video_path = os.path.join(VIDEO_DIR, selected)
    st.video(video_path)
else:
    st.warning("Belum ada video")

# ===== STREAM SETTING =====
st.subheader("🔴 Live YouTube")

stream_key = st.text_input("Stream Key YouTube", type="password")
is_shorts = st.checkbox("Mode Shorts (9:16)")

log_box = st.empty()
logs = []

def log(msg):
    logs.append(msg)
    log_box.text("\n".join(logs[-15:]))

# ===== BUTTON =====
if st.button("🚀 Mulai Live"):
    if not video_path or not stream_key:
        st.error("Video & Stream Key wajib diisi")
    else:
        threading.Thread(
            target=run_ffmpeg,
            args=(video_path, stream_key, is_shorts, log),
            daemon=True
        ).start()
        st.success("Live dimulai")

if st.button("🛑 Stop Live"):
    os.system("pkill ffmpeg")
    st.warning("Live dihentikan")
