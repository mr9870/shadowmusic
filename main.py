from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

def get_client_id():
    try:
        res = requests.get("https://soundcloud.com", headers=HEADERS)
        scripts = re.findall(r'src="([^"]+\.js)"', res.text)
        for script_url in reversed(scripts):
            s_res = requests.get(script_url, headers=HEADERS)
            found = re.findall(r'client_id:"([a-zA-Z0-9]{32})"', s_res.text)
            if found: return found[0]
    except: pass
    return "iFagfuAuwkp6GbI6M6rA7UMw4LOdqC95" # Jo teri current working ID hai

CLIENT_ID = get_client_id()

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query: return jsonify([])
    try:
        url = f"https://api-v2.soundcloud.com/search/tracks?q={query}&client_id={CLIENT_ID}&limit=15"
        data = requests.get(url, headers=HEADERS).json()
        results = []
        for track in data.get('collection', []):
            results.append({
                'id': track['permalink_url'],
                'title': track['title'],
                'thumbnail': (track['artwork_url'] or track['user']['avatar_url']).replace('-large', '-t500x500'),
                'artist': track['user']['username']
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/proxy_audio')
def proxy_audio():
    track_url = request.args.get('id')
    try:
        # 1. Resolve SoundCloud URL to get track info
        resolve_url = f"https://api-v2.soundcloud.com/resolve?url={track_url}&client_id={CLIENT_ID}"
        track_data = requests.get(resolve_url, headers=HEADERS).json()
        
        # 2. Get the streaming URL (progressive format)
        transcodings = track_data['media']['transcodings']
        # Filter for progressive mp3 (sabse stable streaming ke liye)
        stream_meta_url = next(t['url'] for t in transcodings if t['format']['protocol'] == 'progressive')
        
        final_stream_url = requests.get(f"{stream_meta_url}?client_id={CLIENT_ID}", headers=HEADERS).json()['url']
        
        # 3. Stream audio to Flutter
        def generate():
            with requests.get(final_stream_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=1024*64):
                    yield chunk
        return Response(generate(), mimetype="audio/mpeg")
    except Exception as e:
        return str(e), 500

@app.route('/')
def home():
    return f"Shadow Backend Active. ClientID: {CLIENT_ID}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
