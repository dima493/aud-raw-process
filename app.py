
import os
from flask import Flask, render_template, request, send_file
from yt_dlp import YoutubeDL

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None

    if request.method == 'POST':
        url = request.form.get('url_input')
        
        if url:
            # Create a downloads directory if it doesn't exist
            os.makedirs('downloads', exist_ok=True)
            
            # Configure yt-dlp for MP3 extraction
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(title)s.%(ext)s', # Define save location and name
                'ffmpeg_location': './bin',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudioPP',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
            }

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    # 1. Extract video info
                    info_dict = ydl.extract_info(url, download=True)
                    
                    # 2. Get the expected filename based on the template
                    filename = ydl.prepare_filename(info_dict)
                    
                    # 3. The postprocessor changes the extension to .mp3
                    base_name, _ = os.path.splitext(filename)
                    mp3_filename = f"{base_name}.mp3"
                    
                    # 4. Send the file to the user's browser
                    return send_file(mp3_filename, as_attachment=True)
                    
            except Exception as e:
                error = f"Failed to process video: {str(e)}"

    # If it's a GET request or there was an error, render the page
    return render_template('index.html', error=error)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
                    
