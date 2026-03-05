from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os, hashlib, urllib.request, json as jsonlib

app = Flask(__name__)
app.secret_key = 'reelmind_secret_2024'

TMDB_KEY = os.environ.get('TMDB_API_KEY', '')
TMDB_BASE = 'https://api.themoviedb.org/3'
IMG_BASE  = 'https://image.tmdb.org/t/p/w300'

USERS = {}        # {username: hashed_password}
PREFS = {}        # {username: [movie_ids]}

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def tmdb_get(endpoint, params=''):
    url = f"{TMDB_BASE}{endpoint}?api_key={TMDB_KEY}&{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return jsonlib.loads(r.read().decode())
    except Exception as e:
        print(f"TMDB error: {e}")
        return None

def format_movie(m):
    return {
        'id': m['id'],
        'title': m.get('title', ''),
        'year': m.get('release_date', '???')[:4],
        'poster': IMG_BASE + m['poster_path'] if m.get('poster_path') else None,
        'rating': round(m.get('vote_average', 0), 1),
        'overview': m.get('overview', '')
    }

def search_movie(query):
    q = urllib.request.quote(query)
    data = tmdb_get('/search/movie', f'query={q}&language=en-US&page=1')
    if not data or not data.get('results'):
        return []
    return [format_movie(m) for m in data['results'][:8]]

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
    recs = []
    data = tmdb_get(f'/movie/{movie_id}/recommendations', 'language=en-US&page=1')
    if data and data.get('results'):
        for m in data['results']:
            if m.get('poster_path') and m.get('title'):
                recs.append(format_movie(m))
    if len(recs) < 6:
        data2 = tmdb_get(f'/movie/{movie_id}/similar', 'language=en-US&page=1')
        if data2 and data2.get('results'):
            existing = {r['id'] for r in recs}
            for m in data2['results']:
                if m.get('poster_path') and m['id'] not in existing:
                    recs.append(format_movie(m))
    if len(recs) == 0:
        details = tmdb_get(f'/movie/{movie_id}', 'language=en-US')
        if details and details.get('genres'):
            gid = details['genres'][0]['id']
            data3 = tmdb_get('/discover/movie', f'with_genres={gid}&sort_by=popularity.desc&page=1')
            if data3 and data3.get('results'):
                for m in data3['results']:
                    if m.get('poster_path') and m['id'] != movie_id:
                        recs.append(format_movie(m))
    return recs[:6]

def get_personalized(username):
    """Get personalized recommendations based on user's preferred movies"""
    pref_movies = PREFS.get(username, [])
    if not pref_movies:
        # No preferences — return popular
        data = tmdb_get('/movie/popular', 'language=en-US&page=1')
        if data and data.get('results'):
            return [format_movie(m) for m in data['results'][:12] if m.get('poster_path')]
        return []

    # Get recommendations for each preferred movie, merge & deduplicate
    all_recs = {}
    for movie in pref_movies[:3]:  # use first 3 preferred movies
        mid = movie['id']
        recs = get_recommendations(mid)
        for r in recs:
            if r['id'] not in all_recs:
                all_recs[r['id']] = r

    # Sort by rating
    sorted_recs = sorted(all_recs.values(), key=lambda x: x['rating'], reverse=True)
    return sorted_recs[:12]

def get_popular_titles():
    data = tmdb_get('/movie/popular', 'language=en-US&page=1')
    if not data:
        return []
    return [m['title'] for m in data.get('results', [])[:10] if m.get('title')]

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    popular = get_popular_titles()
    has_prefs = username in PREFS
    personalized = get_personalized(username) if has_prefs else []
    pref_movies = PREFS.get(username, [])
    return render_template('index.html',
        popular=popular,
        username=username,
        personalized=personalized,
        pref_movies=pref_movies,
        has_prefs=has_prefs
    )

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
        return jsonify({'success': True, 'redirect': '/onboarding'})
    return render_template('register.html')

@app.route('/onboarding')
def onboarding():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('onboarding.html')

@app.route('/onboarding-movies')
def onboarding_movies():
    genre_id = request.args.get('genre', '28')
    data = tmdb_get('/discover/movie', f'with_genres={genre_id}&sort_by=popularity.desc&page=1&vote_count.gte=500')
    if not data or not data.get('results'):
        return jsonify([])
    movies = [format_movie(m) for m in data['results'] if m.get('poster_path')]
    return jsonify(movies[:20])

@app.route('/save-preferences', methods=['POST'])
def save_preferences():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    movies = data.get('movies', [])
    PREFS[session['username']] = movies
    return jsonify({'success': True})

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
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404
    recs = get_recommendations(movie_id)
    return jsonify({'movie': movie, 'recommendations': recs})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
