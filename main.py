from flask import Flask, request, jsonify, Response, stream_with_context
import yt_dlp
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Taaki Flutter app aur browser se connectivity bani rahe

@app.route('/')
def home():
    return jsonify({"status": "Shadow Music Server is Online", "version": "1.2"})

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "No query provided"}), 400
        
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # YouTube search logic
            search_results = ydl.extract_info(f"ytsearch10:{query}", download=False)['entries']
            
            results = []
            for entry in search_results:
                results.append({
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "thumbnail": f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg",
                    "duration": entry.get("duration")
                })
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/proxy_audio')
def proxy_audio():
    vid = request.args.get('id')
    if not vid:
        return "No ID provided", 400

    # Windows Stability Fix: specifically asking for m4a (format 140)
    ydl_opts = {
        'format': '140/bestaudio', 
        'quiet': True,
        'nocheckcertificate': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
            url = info['url']
            
            # Fetch stream from YouTube
            resp = requests.get(url, stream=True, verify=False)
            
            # --- CRITICAL HEADERS FOR WINDOWS FIX ---
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            headers = [(name, value) for (name, value) in resp.raw.headers.items()
                       if name.lower() not in excluded_headers]
            
            # Ye 3 headers Windows native player ke liye zaroori hain
            headers.append(('Content-Type', 'audio/mp4')) # Windows recognizes m4a as audio/mp4
            headers.append(('Accept-Ranges', 'bytes'))
            headers.append(('Access-Control-Allow-Origin', '*'))
            
            return Response(
                stream_with_context(resp.iter_content(chunk_size=1024*64)), 
                headers=headers
            )
    except Exception as e:
        print(f"Proxy Error: {e}")
        return str(e), 500

if __name__ == "__main__":
    import os
    # Render dynamic port support
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
