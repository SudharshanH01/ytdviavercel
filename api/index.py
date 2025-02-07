from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
import logging
import threading
import time

# Initialize Flask app
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
    logger.info(f"Created downloads folder at: {DOWNLOADS_FOLDER}")

# Quality options for downloads
QUALITY_OPTIONS = {
    "mp3": "bestaudio/best",
    "720p": "bestvideo[height<=720]+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best"
}

# Function to delete files after a delay
def delayed_delete(file_path, delay=300):
    """ Deletes a file after a delay (default: 5 minutes) """
    def delete():
        time.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file after delay: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file: {e}")

    threading.Thread(target=delete, daemon=True).start()

# Route to handle video downloads
@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

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
            'logger': logger
        }

        # Add postprocessor for MP3 conversion
        if quality == "mp3":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            downloaded_filename = ydl.prepare_filename(info_dict)

            # If MP3 conversion was done, update filename
            if quality == "mp3":
                downloaded_filename = os.path.splitext(downloaded_filename)[0] + '.mp3'

            if not os.path.exists(downloaded_filename):
                logger.error(f"File not found in downloads folder: {downloaded_filename}")
                return jsonify({'error': 'File not found'}), 404

        logger.info(f"File found at: {downloaded_filename}")

        # Schedule the file for deletion after 5 minutes
        delayed_delete(downloaded_filename, delay=300)

        return send_file(
            downloaded_filename,
            as_attachment=True,
            download_name=os.path.basename(downloaded_filename)
        )

    except Exception as e:
        logger.error(f"Download Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route to fetch video thumbnail
@app.route('/thumbnail', methods=['POST'])
def get_thumbnail():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

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
        logger.error(f"Thumbnail Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Export the app for Vercel
def handler(event, context):
    return app(event, context)
