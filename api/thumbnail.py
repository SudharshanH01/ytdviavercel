from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL

app = Flask(__name__)

@app.route("/api/thumbnail", methods=["POST"])
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

# Required for Vercel
def handler(event, context):
    return app(event, context)
