from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os, json, hashlib

app = Flask(__name__)
app.secret_key = 'cinematch_secret_2024'

USERS_FILE = 'users.json'

# ─── USER STORAGE (file-based, no DB needed) ──────────────────────────────────
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ─── DATASET ──────────────────────────────────────────────────────────────────
movies_data = [
    {"id":1,"title":"The Dark Knight","genres":"Action Crime Drama","director":"Christopher Nolan","cast":"Christian Bale Heath Ledger","description":"Batman faces the Joker a criminal mastermind who plunges Gotham into anarchy","year":2008,"rating":9.0,"tmdb_id":155},
    {"id":2,"title":"Inception","genres":"Action SciFi Thriller","director":"Christopher Nolan","cast":"Leonardo DiCaprio Joseph Gordon-Levitt","description":"A thief enters dreams to plant an idea in a targets mind","year":2010,"rating":8.8,"tmdb_id":27205},
    {"id":3,"title":"Interstellar","genres":"Adventure Drama SciFi","director":"Christopher Nolan","cast":"Matthew McConaughey Anne Hathaway","description":"Astronauts travel through a wormhole near Saturn to find a new home for humanity","year":2014,"rating":8.6,"tmdb_id":157336},
    {"id":4,"title":"The Shawshank Redemption","genres":"Drama","director":"Frank Darabont","cast":"Tim Robbins Morgan Freeman","description":"Two imprisoned men bond over years finding solace and redemption through decency","year":1994,"rating":9.3,"tmdb_id":278},
    {"id":5,"title":"Pulp Fiction","genres":"Crime Drama Thriller","director":"Quentin Tarantino","cast":"John Travolta Uma Thurman Samuel L Jackson","description":"Lives of two hit men a boxer and bandits intertwine in four tales of violence","year":1994,"rating":8.9,"tmdb_id":680},
    {"id":6,"title":"The Godfather","genres":"Crime Drama","director":"Francis Ford Coppola","cast":"Marlon Brando Al Pacino","description":"The aging patriarch of an organized crime dynasty transfers control to his reluctant son","year":1972,"rating":9.2,"tmdb_id":238},
    {"id":7,"title":"Forrest Gump","genres":"Drama Romance","director":"Robert Zemeckis","cast":"Tom Hanks Robin Wright","description":"The presidencies of Kennedy and Johnson through the eyes of an Alabama man with low IQ","year":1994,"rating":8.8,"tmdb_id":13},
    {"id":8,"title":"The Matrix","genres":"Action SciFi","director":"Wachowski Sisters","cast":"Keanu Reeves Laurence Fishburne","description":"A computer hacker learns about the true nature of reality and his role in the war against controllers","year":1999,"rating":8.7,"tmdb_id":603},
    {"id":9,"title":"Goodfellas","genres":"Biography Crime Drama","director":"Martin Scorsese","cast":"Ray Liotta Robert De Niro Joe Pesci","description":"The story of Henry Hill and his life in the mob","year":1990,"rating":8.7,"tmdb_id":769},
    {"id":10,"title":"Schindlers List","genres":"Biography Drama History","director":"Steven Spielberg","cast":"Liam Neeson Ben Kingsley","description":"Industrialist Oskar Schindler saves Jewish refugees in German-occupied Poland","year":1993,"rating":9.0,"tmdb_id":424},
    {"id":11,"title":"The Silence of the Lambs","genres":"Crime Drama Thriller","director":"Jonathan Demme","cast":"Jodie Foster Anthony Hopkins","description":"A young FBI cadet seeks help from an imprisoned cannibal killer to catch a serial killer","year":1991,"rating":8.6,"tmdb_id":274},
    {"id":12,"title":"Avatar","genres":"Action Adventure Fantasy SciFi","director":"James Cameron","cast":"Sam Worthington Zoe Saldana","description":"A paraplegic Marine is dispatched to the moon Pandora on a unique mission","year":2009,"rating":7.8,"tmdb_id":19995},
    {"id":13,"title":"Titanic","genres":"Drama Romance","director":"James Cameron","cast":"Leonardo DiCaprio Kate Winslet","description":"An aristocrat falls in love with a poor artist aboard the ill-fated Titanic","year":1997,"rating":7.9,"tmdb_id":597},
    {"id":14,"title":"The Avengers","genres":"Action Adventure SciFi","director":"Joss Whedon","cast":"Robert Downey Jr Chris Evans Scarlett Johansson","description":"Earths mightiest heroes must come together and learn to fight as a team","year":2012,"rating":8.0,"tmdb_id":24428},
    {"id":15,"title":"Joker","genres":"Crime Drama Thriller","director":"Todd Phillips","cast":"Joaquin Phoenix Robert De Niro","description":"In Gotham City mentally troubled comedian Arthur Fleck is disregarded by society","year":2019,"rating":8.4,"tmdb_id":475557},
    {"id":16,"title":"Parasite","genres":"Comedy Drama Thriller","director":"Bong Joon-ho","cast":"Kang-ho Song Sun-kyun Lee","description":"Greed and class discrimination threaten the relationship between the wealthy Park family and the destitute Kim clan","year":2019,"rating":8.5,"tmdb_id":496243},
    {"id":17,"title":"1917","genres":"Action Drama War","director":"Sam Mendes","cast":"George MacKay Dean-Charles Chapman","description":"Two British soldiers given a seemingly impossible mission to deliver a message deep in enemy territory","year":2019,"rating":8.3,"tmdb_id":530915},
    {"id":18,"title":"Whiplash","genres":"Drama Music","director":"Damien Chazelle","cast":"Miles Teller J.K. Simmons","description":"A promising young drummer enrolls at a cut-throat music conservatory driven to the edge","year":2014,"rating":8.5,"tmdb_id":244786},
    {"id":19,"title":"La La Land","genres":"Comedy Drama Music Romance","director":"Damien Chazelle","cast":"Ryan Gosling Emma Stone","description":"A pianist and actress fall in love in Los Angeles while pursuing their dreams","year":2016,"rating":8.0,"tmdb_id":313369},
    {"id":20,"title":"Get Out","genres":"Horror Mystery Thriller","director":"Jordan Peele","cast":"Daniel Kaluuya Allison Williams","description":"A young African-American visits his white girlfriends parents where uneasiness reaches a boiling point","year":2017,"rating":7.7,"tmdb_id":419430},
    {"id":21,"title":"Mad Max Fury Road","genres":"Action Adventure SciFi","director":"George Miller","cast":"Tom Hardy Charlize Theron","description":"In a post-apocalyptic wasteland a woman rebels against a tyrannical ruler searching for her homeland","year":2015,"rating":8.1,"tmdb_id":76341},
    {"id":22,"title":"Blade Runner 2049","genres":"Drama Mystery SciFi Thriller","director":"Denis Villeneuve","cast":"Ryan Gosling Harrison Ford","description":"A young blade runner discovers a long-buried secret that could plunge society into chaos","year":2017,"rating":8.0,"tmdb_id":335984},
    {"id":23,"title":"Dune","genres":"Adventure Drama SciFi","director":"Denis Villeneuve","cast":"Timothee Chalamet Zendaya","description":"The son of a noble family is entrusted with the protection of the most valuable asset in the galaxy","year":2021,"rating":8.0,"tmdb_id":438631},
    {"id":24,"title":"Spirited Away","genres":"Animation Adventure Family Fantasy","director":"Hayao Miyazaki","cast":"Daveigh Chase Suzanne Pleshette","description":"A sulky 10-year-old girl wanders into a world ruled by gods witches and spirits","year":2001,"rating":8.6,"tmdb_id":129},
    {"id":25,"title":"Fight Club","genres":"Drama Thriller","director":"David Fincher","cast":"Brad Pitt Edward Norton","description":"An insomniac office worker and a soap maker form an underground fight club that evolves into much more","year":1999,"rating":8.8,"tmdb_id":550},
    {"id":26,"title":"Gladiator","genres":"Action Adventure Drama","director":"Ridley Scott","cast":"Russell Crowe Joaquin Phoenix","description":"A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family","year":2000,"rating":8.5,"tmdb_id":98},
    {"id":27,"title":"The Departed","genres":"Crime Drama Thriller","director":"Martin Scorsese","cast":"Leonardo DiCaprio Matt Damon Jack Nicholson","description":"An undercover cop and a mole in the police attempt to identify each other in an Irish gang","year":2006,"rating":8.5,"tmdb_id":1422},
    {"id":28,"title":"No Country for Old Men","genres":"Crime Drama Thriller","director":"Coen Brothers","cast":"Tommy Lee Jones Javier Bardem Josh Brolin","description":"Violence and mayhem ensue after a hunter stumbles upon a drug deal gone wrong","year":2007,"rating":8.2,"tmdb_id":6966},
    {"id":29,"title":"Oppenheimer","genres":"Biography Drama History","director":"Christopher Nolan","cast":"Cillian Murphy Emily Blunt Matt Damon","description":"The story of American scientist J Robert Oppenheimer and his role in the development of the atomic bomb","year":2023,"rating":8.9,"tmdb_id":872585},
    {"id":30,"title":"Barbie","genres":"Adventure Comedy Fantasy","director":"Greta Gerwig","cast":"Margot Robbie Ryan Gosling","description":"Barbie and Ken go on a journey of self-discovery after a crisis in Barbieland","year":2023,"rating":7.0,"tmdb_id":346698},
]

# ─── BUILD ML MODEL ───────────────────────────────────────────────────────────
for m in movies_data:
    m['tags'] = f"{m['genres']} {m['director']} {m['cast']} {m['description']}"

tags_list = [m['tags'] for m in movies_data]
tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
tfidf_matrix = tfidf.fit_transform(tags_list)
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

def get_recommendations(movie_title, n=6):
    movie_title_lower = movie_title.lower().strip()
    idx = None
    for i, m in enumerate(movies_data):
        if movie_title_lower in m['title'].lower():
            idx = i
            break
    if idx is None:
        return None, []
    movie = {k: v for k, v in movies_data[idx].items() if k != 'tags'}
    sim_scores = sorted(list(enumerate(cosine_sim[idx])), key=lambda x: x[1], reverse=True)
    sim_scores = [s for s in sim_scores if s[0] != idx][:n]
    recommended = []
    for i, score in sim_scores:
        rec = {k: v for k, v in movies_data[i].items() if k != 'tags'}
        rec['similarity'] = round(float(score) * 100, 1)
        recommended.append(rec)
    return movie, recommended

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    titles = sorted([m['title'] for m in movies_data])
    username = session['username']
    return render_template('index.html', titles=titles, username=username)

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

@app.route('/recommend', methods=['POST'])
def recommend():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    movie_title = data.get('movie', '')
    movie, recommendations = get_recommendations(movie_title)
    if movie is None:
        return jsonify({'error': 'Movie not found. Try another title!'}), 404
    return jsonify({'movie': movie, 'recommendations': recommendations})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
