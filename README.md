# 🎬 ReelMind — Movie Recommendation System

> **AI-powered content-based filtering | 30+ curated films | Instant similarity matching**

🌐 **Live Demo:** [https://reelmind-abej.onrender.com](https://reelmind-abej.onrender.com)

---

## 📌 Project Overview

**ReelMind** is a web-based Movie Recommendation System that suggests films to users based on what they like. It was built as a mini project for the subject **CS-281-FP** (Python Programming / Full-Stack Python) in **Semester IV, S.Y.B.Sc. Computer Science** under the NEP Pattern 2024.

> In simple words — you tell the app a movie you like, and it shows you other similar movies you might enjoy. The app also has a login system so each user gets their own personalized experience.

---

## 🛠️ Tech Stack

### Backend (Server Side)

| Technology | Purpose |
|---|---|
| **Python 3** | Main programming language for all backend logic |
| **Flask** | Lightweight web framework — handles URL routing, renders pages, and processes requests |
| **Jinja2** | Templating engine (comes with Flask) — lets us inject Python data into HTML dynamically |
| **SQLite / JSON** | Stores user account info locally without a heavy database setup |
| **Werkzeug** | Helper library used to hash (encrypt) passwords securely before storing them |

### Frontend (Client Side)

| Technology | Purpose |
|---|---|
| **HTML5** | Defines the structure of web pages (login, home, recommendations) |
| **CSS3** | Handles visual design — colors, fonts, layout, hover effects |
| **JavaScript (Vanilla)** | Adds interactivity — button clicks, form validation, dynamic updates |

### Data & Movie Information

| Component | Details |
|---|---|
| **Movie Dataset** | 30+ curated movies stored as a Python list/JSON. Each has: Title, Genre(s), Description, Tags, Poster URL |
| **Movie Posters** | Real poster images fetched via TMDB API URLs |
| **Feature Vectors** | Each movie is converted into a TF-IDF vector for mathematical comparison |

### Deployment

| Platform | Details |
|---|---|
| **Render.com** | Free cloud platform to host the Flask app publicly on the internet |
| **Gunicorn** | Production-grade WSGI server to run Flask on Render |
| **GitHub** | Source code is pushed here; Render auto-deploys from this repo |

---

## 🤖 Algorithm — Content-Based Filtering

The core intelligence of ReelMind comes from the **Content-Based Filtering** algorithm.

### What is Content-Based Filtering?

Content-Based Filtering recommends movies by comparing their **content** (genres, keywords, descriptions) to each other — no user history needed.

> **Simple Analogy:** If you liked *Inception* (sci-fi, mind-bending, thriller), the algorithm finds other movies with the same tags and recommends them.

### Step-by-Step Working

#### Step 1 — Feature Extraction
Each movie's metadata (genres, tags, description) is combined into a single text string called a **"soup"**.

```
Movie: The Dark Knight
Soup: "action crime thriller superhero DC Batman Joker Nolan"
```

#### Step 2 — Vectorization (TF-IDF / CountVectorizer)
The text soup of all movies is converted into **numerical vectors** using TF-IDF or CountVectorizer.

Each word becomes a column. Each movie becomes a row. The numbers represent how important each word is for that movie — creating a big matrix of numbers.

#### Step 3 — Cosine Similarity
Once all movies are vectors, the algorithm calculates the **Cosine Similarity** between them.

```
Cosine Similarity = (A · B) / (|A| × |B|)
```

- Score = **1.0** → Movies are identical
- Score = **0.0** → Movies are completely different

The algorithm picks the **top 5–10 movies** with the highest similarity score.

#### Step 4 — Ranking & Display
Movies are sorted from highest to lowest similarity score and displayed with their posters, titles, and genres.

---

## 🔐 User Authentication System

### Registration
- User enters a username and password
- Password is **hashed** using `generate_password_hash()` from Werkzeug
- The hashed password (never plain text) is stored in the database

### Login / Sign In
- User enters credentials
- Password is verified using `check_password_hash()`
- A **Flask session** is created to keep the user logged in

### Session Management
Flask uses a `session` object backed by a secret key to remember the logged-in user across pages. Protected routes check for a valid session before granting access.

---

## 🔄 Application Flow

| Step | Action | What Happens |
|---|---|---|
| 1 | User visits the site | Login page is shown. Flask route `/login` handles this |
| 2 | Login / Register | Credentials verified, session started |
| 3 | Home / Dashboard | User sees the movie catalog — 30+ films as cards with posters |
| 4 | Select a Movie | User clicks a movie. A request is sent to the Flask backend |
| 5 | Algorithm Runs | Content-based filtering calculates cosine similarity |
| 6 | Results Displayed | Top 5–10 similar movies rendered with posters and genres |

---

## ✨ Key Features

- 🤖 **AI-Powered Recommendations** — Content-based filtering for instant similar movie suggestions
- 🔐 **User Authentication** — Secure login/register with hashed passwords
- 🎬 **30+ Curated Movies** — Popular films across genres with real poster images
- 📱 **Responsive UI** — Clean design on both desktop and mobile
- ⚡ **Instant Matching** — Pre-computed similarity matrix for fast results
- ☁️ **Cloud Deployed** — Accessible from anywhere via Render.com

---

## 📚 Important CS Concepts Used

### TF-IDF (Term Frequency – Inverse Document Frequency)
Converts text into numbers, giving higher weight to words unique to a movie and lower weight to common words.

```
TF  = (Times word appears in doc) / (Total words in doc)
IDF = log(Total documents / Documents containing the word)
```

### Cosine Similarity
Measures how alike two movie vectors are by calculating the angle between them in multi-dimensional space. Smaller angle = more similar movies.

### Vectorization
Converts text data (genres, descriptions) into numerical arrays so a computer can mathematically compare movies.

### Session Management
Temporary storage that lets Flask remember a logged-in user as they navigate between pages — without it, the user would have to log in on every page.

---

## 📁 Project Structure

```
reelmind/
├── app.py              → Main Flask application (routes, logic)
├── recommender.py      → Content-based filtering algorithm
├── movies.py / data/   → Movie dataset (titles, genres, posters)
├── templates/          → HTML pages (Jinja2 templates)
│   ├── login.html
│   ├── register.html
│   └── index.html / home.html
├── static/             → CSS files, images, JavaScript
├── requirements.txt    → Python dependencies (Flask, scikit-learn, etc.)
└── Procfile            → Render/Gunicorn startup command
```

---

## 🚀 Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/your-username/reelmind.git
cd reelmind

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

---

## 📋 Project Info

| Field | Details |
|---|---|
| **Subject** | CS-281-FP — Mini Project |
| **Semester** | IV — S.Y.B.Sc. Computer Science |
| **Pattern** | NEP 2024 |
| **University** | Savitribai Phule Pune University |
| **College** | Dr. D.Y. Patil Arts, Commerce & Science College, Pimpri |

---

> Built with ❤️ using Python & Flask
