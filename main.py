from flask import Flask, request, Response, jsonify, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests
import urllib3
import os

# SSL warnings disable karne ke liye
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "Shadow Music Server is Online", "version": "1.1"})

@app.route('/search', methods=['GET'])
def search_songs():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "No query provided"}), 400
        
    # extract_flat: True taaki sirf metadata aaye, heavy data nahi
    ydl_opts = {'quiet': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Hum query ke saath 'audio' add kar rahe hain taaki music quality mile
            info = ydl.extract_info(f"ytsearch10:{query} audio", download=False)
            results = [{
                'id': e['id'], 
                'title': e['title'], 
                'thumbnail': f"https://i.ytimg.com/vi/{e['id']}/mqdefault.jpg"
            } for e in info['entries']]
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/proxy_audio')
def proxy_audio():
    vid = request.args.get('id')
    # Format 140 = M4A (Light and High Quality for streaming)
    ydl_opts = {
        'format': '140/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
            url = info['url']
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            # Stream=True taaki data load hota rahe aur gaana chalta rahe
            req = requests.get(url, stream=True, headers=headers, timeout=20, verify=False)
            
            def generate():
                for chunk in req.iter_content(chunk_size=32768): # 32KB chunks stability ke liye
                    if chunk:
                        yield chunk
            
            return Response(stream_with_context(generate()), content_type='audio/mp4')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Koyeb environment variable se PORT uthayega (Step 1 fix)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)