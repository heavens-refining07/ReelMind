from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os, hashlib, urllib.request, json as jsonlib

app = Flask(__name__)
app.secret_key = 'reelmind_secret_2024'

TMDB_KEY = os.environ.get('TMDB_API_KEY', '')
TMDB_BASE = 'https://api.themoviedb.org/3'
IMG_BASE  = 'https://image.tmdb.org/t/p/w300'

USERS = {}

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def tmdb_get(endpoint, params=''):
    url = f"{TMDB_BASE}{endpoint}?api_key={TMDB_KEY}&{params}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            return jsonlib.loads(r.read().decode())
    except:
        return None

def search_movie(query):
    q = urllib.request.quote(query)
    data = tmdb_get('/search/movie', f'query={q}&language=en-US&page=1')
    if not data or not data.get('results'):
        return []
    results = []
    for m in data['results'][:8]:
        results.append({
            'id': m['id'],
            'title': m.get('title', ''),
            'year': m.get('release_date', '???')[:4],
            'poster': IMG_BASE + m['poster_path'] if m.get('poster_path') else None,
            'rating': round(m.get('vote_average', 0), 1),
            'overview': m.get('overview', '')
        })
    return results

def get_movie_details(movie_id):
    data = tmdb_get(f'/movie/{movie_id}', 'language=en-US')
    if not data:
        return None
    return {
        'id': data['id'],
        'title': data.get('title', ''),
        'year': data.get('release_date', '???')[:4],
        'poster': IMG_BASE + data['poster_path'] if data.get('poster_path') else None,
        'rating': round(data.get('vote_average', 0), 1),
        'overview': data.get('overview', ''),
        'genres': ' '.join([g['name'] for g in data.get('genres', [])]),
        'runtime': data.get('runtime', ''),
    }

def get_recommendations(movie_id):
    data = tmdb_get(f'/movie/{movie_id}/recommendations', 'language=en-US&page=1')
    if not data or not data.get('results'):
        data = tmdb_get(f'/movie/{movie_id}/similar', 'language=en-US&page=1')
    if not data or not data.get('results'):
        return []
    recs = []
    for m in data['results']:
        if not m.get('poster_path'):
            continue
        recs.append({
            'id': m['id'],
            'title': m.get('title', ''),
            'year': m.get('release_date', '???')[:4],
            'poster': IMG_BASE + m['poster_path'],
            'rating': round(m.get('vote_average', 0), 1),
            'overview': m.get('overview', ''),
        })
        if len(recs) == 6:
            break
    return recs

def get_popular():
    data = tmdb_get('/movie/popular', 'language=en-US&page=1')
    if not data:
        return []
    return [m['title'] for m in data.get('results', [])[:10] if m.get('title')]

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    popular = get_popular()
    return render_template('index.html', popular=popular, username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        if username in USERS and USERS[username] == hash_password(password):
            session['username'] = username
            return jsonify({'success': True})
        return jsonify({'error': 'Invalid username or password'}), 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        if not username or not password:
            return jsonify({'error': 'All fields required'}), 400
        if username in USERS:
            return jsonify({'error': 'Username already exists'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        USERS[username] = hash_password(password)
        session['username'] = username
        return jsonify({'success': True})
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/search')
def search():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    return jsonify(search_movie(query))

@app.route('/recommend/<int:movie_id>')
def recommend(movie_id):
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    movie = get_movie_details(movie_id)
    recs  = get_recommendations(movie_id)
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404
    return jsonify({'movie': movie, 'recommendations': recs})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
