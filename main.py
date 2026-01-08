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
    ydl_opts = {'format': '140/bestaudio', 'quiet': True, 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
            url = info['url']
            
            # Windows/Render Fix: Range Request Handling
            headers = {'User-Agent': 'Mozilla/5.0'}
            if 'Range' in request.headers:
                headers['Range'] = request.headers.get('Range')
            
            resp = requests.get(url, stream=True, headers=headers)
            
            rv = Response(stream_with_context(resp.iter_content(chunk_size=1024*64)),
                          status=resp.status_code,
                          content_type=resp.headers.get('Content-Type'),
                          direct_passthrough=True)
            
            # Essential Headers for Windows Native Player
            rv.headers.add('Accept-Ranges', 'bytes')
            if 'Content-Range' in resp.headers:
                rv.headers.add('Content-Range', resp.headers.get('Content-Range'))
            if 'Content-Length' in resp.headers:
                rv.headers.add('Content-Length', resp.headers.get('Content-Length'))
            rv.headers.add('Access-Control-Allow-Origin', '*')
            
            return rv
    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
