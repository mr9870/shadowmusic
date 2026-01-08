from flask import Flask, request, jsonify, Response, stream_with_context
import yt_dlp
import requests
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# 1. Home Route: Taaki check kar sake ki server zinda hai
@app.route('/')
def home():
    return jsonify({
        "status": "Shadow Music Server is Online",
        "owner": "Shadow",
        "version": "1.2"
    })

# 2. Search API: Gaane dhundne ke liye
@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Query missing"}), 400
        
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'nocheckcertificate': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearch10:query matlab top 10 results fetch karega
            search_results = ydl.extract_info(f"ytsearch10:{query}", download=False).get('entries', [])
            results = []
            for e in search_results:
                if e:
                    results.append({
                        "id": e.get("id"),
                        "title": e.get("title"),
                        "thumbnail": f"https://i.ytimg.com/vi/{e.get('id')}/mqdefault.jpg"
                    })
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Proxy Audio: Windows Error C00D2EE2 fix karne ke liye
@app.route('/proxy_audio')
def proxy_audio():
    vid = request.args.get('id')
    if not vid:
        return "Video ID required", 400

    # Format 140 specifically 'm4a' hota hai jo Windows player easily samajh leta hai
    ydl_opts = {
        'format': '140/bestaudio', 
        'quiet': True,
        'nocheckcertificate': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
            audio_url = info['url']
            
            # YouTube se stream fetch karna
            resp = requests.get(audio_url, stream=True, timeout=15)
            
            # Windows native player ko ye headers chahiye hote hain
            headers = {
                'Content-Type': 'audio/mp4',
                'Accept-Ranges': 'bytes',
                'Access-Control-Allow-Origin': '*'
            }
            
            return Response(
                stream_with_context(resp.iter_content(chunk_size=1024*64)), 
                headers=headers
            )
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    # Render dynamic port set karega, default 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
