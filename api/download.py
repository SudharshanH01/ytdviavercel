from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
import os
import tempfile

app = Flask(__name__)

QUALITY_OPTIONS = {
    "mp3": "bestaudio/best",
    "720p": "bestvideo[height<=720]+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best"
}

@app.route("/api/download", methods=["POST"])
def download_video():
    try:
        data = request.json
        video_url = data.get('url')
        quality = data.get('quality', '720p')

        if not video_url:
            return jsonify({'error': 'URL is required'}), 400

        if quality not in QUALITY_OPTIONS:
            return jsonify({'error': 'Invalid quality option'}), 400

        temp_dir = tempfile.mkdtemp()
        ydl_opts = {
            'format': QUALITY_OPTIONS[quality],
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True
        }

        if quality == "mp3":
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            downloaded_filename = ydl.prepare_filename(info_dict)
            if quality == "mp3":
                downloaded_filename = os.path.splitext(downloaded_filename)[0] + '.mp3'

        return send_file(downloaded_filename, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Required for Vercel
def handler(event, context):
    return app(event, context)
