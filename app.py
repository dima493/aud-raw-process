import os
import json
import queue
import threading
import requests
from flask import Flask, render_template, request, Response
from yt_dlp import YoutubeDL

app = Flask(__name__)

def upload_to_cloud(file_path):
    """Uploads the file to Catbox and returns the public link."""
    url = "https://catbox.moe/user/api.php"
    catbox_hash = os.environ.get("CATBOX_USERHASH")
    
    data = {
        "reqtype": "fileupload",
        "userhash": catbox_hash
    }
    
    with open(file_path, 'rb') as f:
        files = {"fileToUpload": f}
        response = requests.post(url, data=data, files=files)
        
    if response.status_code == 200:
        return response.text
    else:
        raise Exception("Cloud upload failed")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    url = request.form.get('url_input')
    if not url:
        return Response("Missing URL", status=400)

    progress_queue = queue.Queue()

    def yt_dlp_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                percent = int((downloaded / total) * 100)
                progress_queue.put({
                    "type": "progress",
                    "stage": "Downloading video stream...",
                    "percent": percent
                })
        elif d['status'] == 'finished':
            progress_queue.put({
                "type": "progress",
                "stage": "Converting audio to MP3 format...",
                "percent": 100
            })

    def worker_thread():
        mp3_filename = None
        try:
            os.makedirs('downloads', exist_ok=True)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'ffmpeg_location': './bin',
                'progress_hooks': [yt_dlp_hook],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudioPP',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }

            progress_queue.put({"type": "status", "stage": "Analyzing video metadata..."})
            
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                song_name = info_dict.get('title', 'Unknown Title')
                author = info_dict.get('uploader', 'Unknown Author')
                
                filename = ydl.prepare_filename(info_dict)
                base_name, _ = os.path.splitext(filename)
                mp3_filename = f"{base_name}.mp3"
                
                progress_queue.put({"type": "status", "stage": "Uploading media to cloud storage..."})
                public_link = upload_to_cloud(mp3_filename)
                
                if os.path.exists(mp3_filename):
                    os.remove(mp3_filename)
                
                song_data = {
                    "name": song_name,
                    "author": author,
                    "link": public_link
                }
                progress_queue.put({"type": "final", "data": song_data})

        except Exception as e:
            progress_queue.put({"type": "error", "message": str(e)})
            if mp3_filename and os.path.exists(mp3_filename):
                os.remove(mp3_filename)
        finally:
            progress_queue.put(None)

    threading.Thread(target=worker_thread).start()

    def response_generator():
        while True:
            msg = progress_queue.get()
            if msg is None:
                break
            yield json.dumps(msg) + "\n"

    return Response(response_generator(), mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
