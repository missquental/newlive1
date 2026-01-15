import streamlit as st
import gdown
import os
from pathlib import Path

# ===============================
# KONFIGURASI
# ===============================
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1d7fpbrOI9q9Yl6w99-yZGNMB30XNyugf"
DOWNLOAD_DIR = "videos_drive"

# ===============================
# UI STREAMLIT
# ===============================
st.set_page_config(page_title="Google Drive Video Downloader", layout="centered")

st.title("📥 Download Video dari Google Drive")
st.write("Folder sumber:")
st.code(DRIVE_FOLDER_URL)

# Pastikan folder download ada
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

# ===============================
# FUNGSI DOWNLOAD
# ===============================
def download_drive_folder(url, output_dir):
    """
    Download semua file dari Google Drive folder public
    """
    gdown.download_folder(
        url=url,
        output=output_dir,
        quiet=False,
        use_cookies=False
    )

# ===============================
# TOMBOL DOWNLOAD
# ===============================
if st.button("🚀 Download Semua Video"):
    with st.spinner("Mengunduh video dari Google Drive..."):
        try:
            download_drive_folder(DRIVE_FOLDER_URL, DOWNLOAD_DIR)
            st.success("✅ Download selesai!")
        except Exception as e:
            st.error(f"❌ Gagal download: {e}")

# ===============================
# TAMPILKAN VIDEO
# ===============================
st.subheader("🎬 Video yang berhasil diunduh")

video_files = sorted([
    f for f in os.listdir(DOWNLOAD_DIR)
    if f.lower().endswith((".mp4", ".mkv", ".mov", ".avi"))
])

if video_files:
    for video in video_files:
        video_path = os.path.join(DOWNLOAD_DIR, video)
        st.video(video_path)
        st.caption(video)
else:
    st.info("Belum ada video yang diunduh.")
