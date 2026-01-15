import sys
import subprocess
import threading
import time
import os
import tempfile
import streamlit.components.v1 as components
import requests
from bs4 import BeautifulSoup
import re

# Install dependencies jika belum ada
try:
    import streamlit as st
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    import streamlit as st

try:
    import gdown
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
    import gdown

# Direktori cache untuk menyimpan video yang diunduh
CACHE_DIR = "cache_videos"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Fungsi untuk scrape daftar file dari folder Google Drive publik
def get_drive_folder_files(folder_url):
    # Ekstrak folder ID dari URL
    folder_id = folder_url.split('/')[-1]
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Cari file video berdasarkan pola nama file
    links = soup.find_all('a', href=re.compile(r'/file/d/'))
    
    video_files = []
    for link in links:
        title = link.text.strip()
        if title.lower().endswith(('.mp4', '.flv', '.mov', '.avi', '.mkv')):
            href = link.get('href')
            file_id = re.search(r'/file/d/([^/]+)', href)
            if file_id:
                file_id = file_id.group(1)
                video_files.append({
                    'title': title,
                    'id': file_id,
                    'url': f"https://drive.google.com/uc?id={file_id}"
                })
    
    return video_files

# Fungsi untuk mengunduh video
def download_video(url, filename):
    filepath = os.path.join(CACHE_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    
    try:
        gdown.download(url, filepath, quiet=False)
        return filepath
    except Exception as e:
        st.error(f"Gagal mengunduh {filename}: {str(e)}")
        return None

# Fungsi untuk streaming dengan FFmpeg
def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    scale = "-vf scale=720:1280" if is_shorts else ""
    cmd = [
        "ffmpeg", "-re", "-stream_loop", "-1", "-i", video_path,
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
        "-maxrate", "2500k", "-bufsize", "5000k",
        "-g", "60", "-keyint_min", "60",
        "-c:a", "aac", "-b:a", "128k",
        "-f", "flv"
    ]
    if scale:
        cmd += scale.split()
    cmd.append(output_url)
    log_callback(f"Menjalankan: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"Error: {e}")
    finally:
        log_callback("Streaming selesai atau dihentikan.")

# Main App
def main():
    st.set_page_config(page_title="Streaming YT by didinchy", page_icon="📈", layout="wide")
    st.title("Live Streaming Loss Doll")

    # Bagian iklan baru
    show_ads = st.checkbox("Tampilkan Iklan", value=True)
    if show_ads:
        st.subheader("Iklan Sponsor")
        components.html("""
            <div style="background:#f0f2f6;padding:20px;border-radius:10px;text-align:center">
                <script type='text/javascript' 
                        src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'></script>
                <p style="color:#888">Iklan akan muncul di sini</p>
            </div>
        """, height=300)

    # Sidebar navigation
    st.sidebar.header("Sumber Video")
    source_option = st.sidebar.radio("Pilih Sumber Video:", ("Lokal", "Upload", "Google Drive Link"))

    video_path = None

    # Opsi 1: Lokal
    if source_option == "Lokal":
        video_files = [f for f in os.listdir('.') if f.endswith(('.mp4', '.flv'))]
        st.write("Video lokal yang tersedia:")
        selected_video = st.selectbox("Pilih video lokal", video_files) if video_files else None
        if selected_video:
            video_path = selected_video

    # Opsi 2: Upload
    elif source_option == "Upload":
        uploaded_file = st.file_uploader("Upload video (mp4/flv)", type=['mp4', 'flv'])
        if uploaded_file:
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.read())
            st.success("Video berhasil diupload!")
            video_path = uploaded_file.name

    # Opsi 3: Google Drive Link
    elif source_option == "Google Drive Link":
        drive_folder_url = st.text_input("Masukkan Link Folder Google Drive", 
                                        "https://drive.google.com/drive/folders/1d7fpbrOI9q9Yl6w99-yZGNMB30XNyugf")
        
        if drive_folder_url:
            try:
                with st.spinner("Mengambil daftar video dari Google Drive..."):
                    video_list = get_drive_folder_files(drive_folder_url)
                
                if video_list:
                    filenames = [item["title"] for item in video_list]
                    chosen_title = st.selectbox("Pilih video dari Drive", filenames)
                    
                    if chosen_title:
                        selected_item = next((item for item in video_list if item["title"] == chosen_title), None)
                        if selected_item:
                            with st.spinner(f"Mengunduh {chosen_title}..."):
                                downloaded_path = download_video(selected_item["url"], chosen_title)
                                if downloaded_path:
                                    video_path = downloaded_path
                                    st.success(f"Video '{chosen_title}' telah diunduh dan siap untuk streaming.")
                else:
                    st.warning("Tidak ada video ditemukan di folder tersebut.")
                    
            except Exception as e:
                st.error(f"Gagal mengambil data dari Google Drive: {str(e)}")

    # Input lainnya
    stream_key = st.text_input("Stream Key YouTube", type="password")
    date = st.date_input("Tanggal Tayang")
    time_val = st.time_input("Jam Tayang")
    is_shorts = st.checkbox("Mode Shorts (720x1280)")

    # Log area
    logs = []
    log_placeholder = st.empty()

    def log_callback(msg):
        logs.append(msg)
        try:
            log_placeholder.text("\n".join(logs[-20:]))
        except:
            print(msg)

    # Tombol kontrol
    if st.button("Jalankan Streaming"):
        if not video_path or not stream_key:
            st.error("Video dan stream key harus diisi!")
        else:
            st.session_state['streaming'] = True
            st.session_state['ffmpeg_thread'] = threading.Thread(
                target=run_ffmpeg, args=(video_path, stream_key, is_shorts, log_callback), daemon=True)
            st.session_state['ffmpeg_thread'].start()
            st.success("Streaming dimulai!")

    if st.button("Stop Streaming"):
        st.session_state['streaming'] = False
        os.system("pkill ffmpeg")
        st.warning("Streaming dihentikan!")

    # Tampilkan log terbaru
    log_placeholder.text("\n".join(logs[-20:]))

if __name__ == "__main__":
    main()
