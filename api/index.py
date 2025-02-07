from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
import logging
import threading
import time

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define absolute downloads folder path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_FOLDER = os.path.join(BASE_DIR, 'downloads')

# Create downloads folder if it doesn't exist
if not os.path.exists(DOWNLOADS_FOLDER):
    os.makedirs(DOWNLOADS_FOLDER)

# Quality options for downloads
QUALITY_OPTIONS = {
    "mp3": "bestaudio/best",
    "720p": "bestvideo[height<=720]+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best"
}

# Function to delete files after a delay
def delayed_delete(file_path, delay=300):
    def delete():
        time.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting file: {e}")

    threading.Thread(target=delete, daemon=True).start()

# Route to handle video downloads
@app.route('/api/download', methods=['POST'])
def download_video():
    try:
        data = request.json
        video_url = data.get('url')
        quality = data.get('quality', '720p')

        if not video_url:
            return jsonify({'error': 'URL is required'}), 400

        if quality not in QUALITY_OPTIONS:
            return jsonify({'error': 'Invalid quality option'}), 400

        ydl_opts = {
            'format': QUALITY_OPTIONS[quality],
            'outtmpl': os.path.join(DOWNLOADS_FOLDER, '%(title)s-%(id)s.%(ext)s'),
            'quiet': True,
        }

        if quality == "mp3":
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            downloaded_filename = ydl.prepare_filename(info_dict)
            if quality == "mp3":
                downloaded_filename = os.path.splitext(downloaded_filename)[0] + '.mp3'

        if not os.path.exists(downloaded_filename):
            return jsonify({'error': 'File not found'}), 404

        delayed_delete(downloaded_filename)

        return send_file(downloaded_filename, as_attachment=True)

    except Exception as e:
        logger.error(f"Download Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route to fetch video thumbnail
@app.route('/api/thumbnail', methods=['POST'])
def get_thumbnail():
    try:
        data = request.json
        video_url = data.get('url')

        if not video_url:
            return jsonify({'error': 'URL is required'}), 400

        ydl_opts = {'skip_download': True, 'quiet': True}

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            thumbnail_url = info_dict.get('thumbnail')

        if not thumbnail_url:
            return jsonify({'error': 'Thumbnail not found'}), 404

        return jsonify({'thumbnail_url': thumbnail_url})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ensure app runs correctly on Vercel
def handler(event, context):
    return app(event, context)
