import os
import requests
from flask import Flask, render_template, request, jsonify
from yt_dlp import YoutubeDL

app = Flask(__name__)

def upload_to_cloud(file_path):
    """Uploads the file to Catbox and returns the public link."""
    url = "https://catbox.moe/user/api.php"
    catbox_hash = os.environ.get("CATBOX_USERHASH")
    
    # Add your userhash to tell Catbox who is uploading the file
    data = {
        "reqtype": "fileupload",
        "userhash": catbox_hash  # <-- Replace with your actual userhash
    }
    
    with open(file_path, 'rb') as f:
        files = {"fileToUpload": f}
        response = requests.post(url, data=data, files=files)
        
    if response.status_code == 200:
        return response.text
    else:
        raise Exception("Cloud upload failed")

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None

    if request.method == 'POST':
        url = request.form.get('url_input')
        
        if url:
            # Create downloads folder if it doesn't exist
            os.makedirs('downloads', exist_ok=True)
            
            # Configure yt-dlp to extract audio and convert to mp3
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'ffmpeg_location': './bin',  # Used by Render's build script
                'postprocessors': [{
                    'key': 'FFmpegExtractAudioPP',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
            }

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    # 1. Download audio and extract metadata
                    info_dict = ydl.extract_info(url, download=True)
                    song_name = info_dict.get('title', 'Unknown Title')
                    author = info_dict.get('uploader', 'Unknown Author')
                    
                    # 2. Get the local file path of the resulting MP3
                    filename = ydl.prepare_filename(info_dict)
                    base_name, _ = os.path.splitext(filename)
                    mp3_filename = f"{base_name}.mp3"
                    
                    # 3. Upload to Catbox and get the public link
                    public_link = upload_to_cloud(mp3_filename)
                    
                    # 4. IMMEDIATE CLEANUP: Delete the MP3 from Render's disk
                    if os.path.exists(mp3_filename):
                        os.remove(mp3_filename)
                    
                    # 5. Create JSON structure purely in RAM
                    song_data = {
                        "name": song_name,
                        "author": author,
                        "link": public_link
                    }
                    
                    # 6. Send the JSON to the browser as a downloadable file
                    response = jsonify(song_data)
                    response.headers.set('Content-Disposition', 'attachment', filename="song_data.json")
                    return response
                    
            except Exception as e:
                error = f"Failed to process video: {str(e)}"
                
                # Cleanup fallback: delete the file if something crashes mid-process
                if 'mp3_filename' in locals() and os.path.exists(mp3_filename):
                    os.remove(mp3_filename)

    return render_template('index.html', error=error)

if __name__ == '__main__':
    # Bind to Render's dynamic port, or 5000 if running locally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
            
