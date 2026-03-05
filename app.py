from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os, hashlib, requests

app = Flask(__name__)
app.secret_key = 'reelmind_secret_2024'

TMDB_KEY = os.environ.get('TMDB_API_KEY', 'YOUR_TMDB_API_KEY')
TMDB_BASE = 'https://api.themoviedb.org/3'

# USER STORAGE (in-memory)
USERS = {}

def load_users():
    return USERS

def save_users(users):
    USERS.update(users)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# TMDB HELPERS
def search_movie(query):
    url = f"{TMDB_BASE}/search/movie"
    params = {'api_key': TMDB_KEY, 'query': query, 'language': 'en-US', 'page': 1}
    r = requests.get(url, params=params, timeout=10)
    results = r.json().get('results', [])
    return results[0] if results else None

def get_movie_details(tmdb_id):
    url = f"{TMDB_BASE}/movie/{tmdb_id}"
    params = {'api_key': TMDB_KEY, 'append_to_response': 'credits,keywords'}
    r = requests.get(url, params=params, timeout=10)
    return r.json()

def get_similar_movies(tmdb_id):
    url = f"{TMDB_BASE}/movie/{tmdb_id}/similar"
    params = {'api_key': TMDB_KEY, 'language': 'en-US', 'page': 1}
    r = requests.get(url, params=params, timeout=10)
    return r.json().get('results', [])[:12]

def get_recommendations_tmdb(tmdb_id):
    url = f"{TMDB_BASE}/movie/{tmdb_id}/recommendations"
    params = {'api_key': TMDB_KEY, 'language': 'en-US', 'page': 1}
    r = requests.get(url, params=params, timeout=10)
    return r.json().get('results', [])[:12]

def compute_similarity(main_movie, candidates):
    if not candidates:
        return []
    main_text = f"{main_movie.get('overview','')} {' '.join([g['name'] for g in main_movie.get('genres',[])])}"
    candidate_texts = [f"{c.get('overview','')} {c.get('title','')}" for c in candidates]
    all_texts = [main_text] + candidate_texts
    try:
        tfidf = TfidfVectorizer(stop_words='english', max_features=3000)
        matrix = tfidf.fit_transform(all_texts)
        sims = cosine_similarity(matrix[0:1], matrix[1:])[0]
        ranked = sorted(zip(candidates, sims), key=lambda x: x[1], reverse=True)
        return ranked[:6]
    except:
        return [(c, 0.5) for c in candidates[:6]]

# ROUTES
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        users = load_users()
        if username in users and users[username] == hash_password(password):
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
        users = load_users()
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        if username in users:
            return jsonify({'error': 'Username already exists'}), 400
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        users[username] = hash_password(password)
        save_users(users)
        session['username'] = username
        return jsonify({'success': True})
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/search-suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    try:
        url = f"{TMDB_BASE}/search/movie"
        params = {'api_key': TMDB_KEY, 'query': query, 'page': 1}
        r = requests.get(url, params=params, timeout=8)
        results = r.json().get('results', [])[:6]
        suggestions = [{'title': m['title'], 'year': m.get('release_date','')[:4]} for m in results if m.get('title')]
        return jsonify(suggestions)
    except:
        return jsonify([])

@app.route('/recommend', methods=['POST'])
def recommend():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    movie_title = data.get('movie', '').strip()
    if not movie_title:
        return jsonify({'error': 'Please enter a movie name'}), 400
    try:
        result = search_movie(movie_title)
        if not result:
            return jsonify({'error': f'Movie not found. Try another title!'}), 404

        tmdb_id = result['id']
        details = get_movie_details(tmdb_id)
        similar = get_similar_movies(tmdb_id)
        tmdb_recs = get_recommendations_tmdb(tmdb_id)

        all_candidates = {m['id']: m for m in similar + tmdb_recs if m['id'] != tmdb_id}
        candidates = list(all_candidates.values())
        ranked = compute_similarity(details, candidates)

        main_poster = f"https://image.tmdb.org/t/p/w300{details['poster_path']}" if details.get('poster_path') else None
        movie = {
            'title': details.get('title', ''),
            'description': details.get('overview', ''),
            'year': details.get('release_date', '????')[:4],
            'rating': round(details.get('vote_average', 0), 1),
            'genres': ' '.join([g['name'] for g in details.get('genres', [])]),
            'poster': main_poster,
            'tmdb_id': tmdb_id,
        }

        recommendations = []
        for m, score in ranked:
            poster = f"https://image.tmdb.org/t/p/w300{m['poster_path']}" if m.get('poster_path') else None
            recommendations.append({
                'title': m.get('title', ''),
                'description': m.get('overview', ''),
                'year': m.get('release_date', '????')[:4] if m.get('release_date') else '????',
                'rating': round(m.get('vote_average', 0), 1),
                'poster': poster,
                'tmdb_id': m.get('id'),
                'similarity': round(float(score) * 100, 1),
            })

        return jsonify({'movie': movie, 'recommendations': recommendations})

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timeout. Please try again.'}), 500
    except Exception as e:
        return jsonify({'error': f'Something went wrong: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
