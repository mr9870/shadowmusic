from flask import Flask, request, jsonify, Response, stream_with_context
import yt_dlp
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/search')
def search():
    query = request.args.get('q')
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ydl.extract_info use karte waqt download=False zaroori hai
            search_results = ydl.extract_info(f"ytsearch10:{query}", download=False).get('entries', [])
            results = [{"id": e.get("id"), "title": e.get("title"), "thumbnail": f"https://i.ytimg.com/vi/{e.get('id')}/mqdefault.jpg"} for e in search_results if e]
            return jsonify(results)
    except Exception as e:
        return jsonify([]) # Error par empty list bhejein taaki Flutter crash na ho

@app.route('/proxy_audio')
def proxy_audio():
    vid = request.args.get('id')
    # Windows fix: specifically format 140 (m4a)
    ydl_opts = {'format': '140/bestaudio', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
            url = info['url']
            resp = requests.get(url, stream=True)
            # Critical Headers for Windows
            headers = {
                'Content-Type': 'audio/mp4',
                'Accept-Ranges': 'bytes',
                'Access-Control-Allow-Origin': '*'
            }
            return Response(stream_with_context(resp.iter_content(chunk_size=1024*64)), headers=headers)
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
