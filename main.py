from flask import Flask, request, jsonify, Response, stream_with_context
import yt_dlp
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "Online", "msg": "Shadow Music Production Server"})

@app.route('/search')
def search():
    query = request.args.get('q')
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch10:{query}", download=False).get('entries', [])
            results = [{"id": e['id'], "title": e['title'], "thumbnail": f"https://i.ytimg.com/vi/{e['id']}/mqdefault.jpg"} for e in search_results if e]
            return jsonify(results)
    except Exception as e:
        return jsonify([])

@app.route('/proxy_audio')
def proxy_audio():
    vid = request.args.get('id')
    # Windows fix: Format 140 (m4a) is globally supported
    ydl_opts = {'format': '140/bestaudio', 'quiet': True, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
            url = info['url']
            
            # Fetching from YouTube with high-performance stream
            resp = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
            
            # Render/Online Fix: Forward original headers for better buffering
            headers = {
                'Content-Type': 'audio/mp4',
                'Accept-Ranges': 'bytes',
                'Access-Control-Allow-Origin': '*',
                'Content-Length': resp.headers.get('Content-Length')
            }
            
            return Response(stream_with_context(resp.iter_content(chunk_size=1024*64)), headers=headers)
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
