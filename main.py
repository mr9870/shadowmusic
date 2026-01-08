from flask import Flask, request, jsonify, Response, stream_with_context
import yt_dlp
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Bypass Headers: YouTube ko lagega ki request ek real browser se aa rahi hai
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Origin': 'https://www.youtube.com',
    'Referer': 'https://www.google.com/',
}

@app.route('/')
def home():
    return jsonify({"status": "Shadow Music Server is Live", "bypass_mode": "Active"})

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query: return jsonify([])
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'nocheckcertificate': True,
        'http_headers': HEADERS
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearch10:query top 10 results nikalega
            search_results = ydl.extract_info(f"ytsearch10:{query}", download=False).get('entries', [])
            results = [{"id": e['id'], "title": e['title'], "thumbnail": f"https://i.ytimg.com/vi/{e['id']}/mqdefault.jpg"} for e in search_results if e]
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/proxy_audio')
def proxy_audio():
    vid = request.args.get('id')
    if not vid: return "Video ID missing", 400

    # m4a format (140) use kar rahe hain kyunki ye Windows/Android dono par stable hai
    ydl_opts = {
        'format': '140/bestaudio',
        'quiet': True,
        'nocheckcertificate': True,
        'http_headers': HEADERS
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
            url = info['url']
            
            # YouTube se stream fetch karna browser headers ke sath
            resp = requests.get(url, stream=True, headers=HEADERS, timeout=15)
            
            # Windows native player ke liye Partial Content (206) aur Range support headers
            rv = Response(stream_with_context(resp.iter_content(chunk_size=1024*128)),
                          status=resp.status_code,
                          content_type='audio/mp4',
                          direct_passthrough=True)
            
            rv.headers.add('Accept-Ranges', 'bytes')
            if 'Content-Length' in resp.headers:
                rv.headers.add('Content-Length', resp.headers.get('Content-Length'))
            rv.headers.add('Access-Control-Allow-Origin', '*')
            
            return rv
    except Exception as e:
        # Agar bot detection ab bhi block kare toh error code 403 (Forbidden) bhejega
        return str(e), 403

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
