import sys
import subprocess
import threading
import time
import os
import tempfile
import streamlit.components.v1 as components
import json
import requests

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

# Fungsi untuk mengambil daftar file dari folder Google Drive menggunakan gdown
def get_drive_folder_files_gdown(folder_url):
    try:
        # Ekstrak folder ID dari URL
        if '/folders/' in folder_url:
            folder_id = folder_url.split('/folders/')[-1].split('?')[0]
        else:
            folder_id = folder_url.split('/')[-1].split('?')[0]
        
        # Buat URL untuk listing
        list_url = f"https://drive.google.com/drive/u/0/folders/{folder_id}"
        
        # Gunakan gdown untuk mendapatkan info file
        # Alternatif: parse dari HTML dengan session
        files_info = []
        
        # Metode alternatif: gunakan API sederhana
        api_url = f"https://drive.google.com/drive/u/0/folders/{folder_id}"
        
        # Karena scraping kompleks, kita akan menggunakan pendekatan yang lebih stabil
        # Yaitu dengan mengunduh file sample.txt atau metadata jika tersedia
        # Atau menggunakan pendekatan manual
        
        return get_files_via_manual_parsing(folder_id)
        
    except Exception as e:
        st.error(f"Error getting folder info: {str(e)}")
        return []

# Fungsi parsing manual yang lebih stabil
def get_files_via_manual_parsing(folder_id):
    try:
        # Gunakan endpoint API sederhana
        url = f"https://drive.google.com/drive/u/0/folders/{folder_id}"
        
        # Headers untuk meniru browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Karena Google Drive sulit di-scrape, kita akan menggunakan pendekatan alternatif
        # Yaitu dengan mencoba mengunduh file sample atau menggunakan gdown dengan cara berbeda
        
        # Metode yang lebih andal: gunakan gdown dengan parameter khusus
        return get_files_with_gdown_method(folder_id)
        
    except Exception as e:
        st.error(f"Parsing error: {str(e)}")
        return []

# Metode yang lebih andal menggunakan gdown
def get_files_with_gdown_method(folder_id):
    try:
        # Buat temporary file untuk testing
        temp_output = "temp_folder_contents.txt"
        
        # Coba list isi folder menggunakan gdown
        # Ini adalah metode workaround karena Google Drive tidak memberikan API publik untuk listing
        
        # Alternatif: kita akan membuat daftar file secara manual berdasarkan ID
        # Untuk folder publik, kita bisa mencoba mengakses beberapa file sample
        
        # Metode terakhir: gunakan pendekatan yang lebih sederhana
        files_list = []
        
        # Karena metode scraping tidak stabil, kita akan menggunakan pendekatan yang lebih fleksibel
        # User bisa memasukkan ID file secara manual jika diperlukan
        
        return manual_file_entry_mode()
        
    except Exception as e:
        return []

# Mode entry manual untuk file Google Drive
def manual_file_entry_mode():
    st.info("⚠️ Mode Manual: Masukkan informasi file secara manual")
    st.markdown("Cara mendapatkan ID file:")
    st.markdown("1. Buka file di Google Drive")
    st.markdown("2. Salin ID dari URL: `https://drive.google.com/file/d/[FILE_ID]/view`")
    
    col1, col2 = st.columns(2)
    with col1:
        file_name = st.text_input("Nama File (termasuk ekstensi)")
    with col2:
        file_id = st.text_input("File ID Google Drive")
    
    if file_name and file_id:
        if st.button("Tambah File ke Daftar"):
            if 'manual_files' not in st.session_state:
                st.session_state.manual_files = []
            
            new_file = {
                'title': file_name,
                'id': file_id,
                'url': f"https://drive.google.com/uc?id={file_id}"
            }
            
            # Cek duplikat
            exists = any(f['id'] == file_id for f in st.session_state.manual_files)
            if not exists:
                st.session_state.manual_files.append(new_file)
                st.success(f"Ditambahkan: {file_name}")
            else:
                st.warning("File sudah ada dalam daftar")
    
    # Tampilkan daftar file yang sudah ditambahkan
    if 'manual_files' in st.session_state and st.session_state.manual_files:
        st.subheader("Daftar File yang Siap Streaming:")
        for i, file_info in enumerate(st.session_state.manual_files):
            col1, col2, col3 = st.columns([3,2,1])
            with col1:
                st.write(file_info['title'])
            with col2:
                if st.button(f"Pilih", key=f"select_{i}"):
                    return [file_info]
            with col3:
                if st.button(f"Hapus", key=f"remove_{i}"):
                    st.session_state.manual_files.pop(i)
                    st.experimental_rerun()
    
    return st.session_state.manual_files if 'manual_files' in st.session_state else []

# Fungsi untuk mengunduh video
def download_video(url, filename):
    filepath = os.path.join(CACHE_DIR, filename)
    if os.path.exists(filepath):
        st.info(f"File {filename} sudah ada di cache")
        return filepath
    
    try:
        st.info(f"Mengunduh {filename}...")
        gdown.download(url, filepath, quiet=False)
        st.success(f"Berhasil mengunduh {filename}")
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
    source_option = st.sidebar.radio("Pilih Sumber Video:", ("Lokal", "Upload", "Google Drive (Manual)"))

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

    # Opsi 3: Google Drive (Manual Entry)
    elif source_option == "Google Drive (Manual)":
        st.info("📁 Masukkan informasi file Google Drive secara manual")
        
        # Gunakan mode entry manual
        video_list = manual_file_entry_mode()
        
        if video_list:
            chosen_file = video_list[0]  # Karena hanya satu file yang dipilih
            chosen_title = chosen_file["title"]
            
            if st.button(f"Gunakan File: {chosen_title}"):
                with st.spinner(f"Mengunduh {chosen_title}..."):
                    downloaded_path = download_video(chosen_file["url"], chosen_title)
                    if downloaded_path:
                        video_path = downloaded_path
                        st.success(f"Video '{chosen_title}' telah diunduh dan siap untuk streaming.")

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
