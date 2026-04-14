"""
CineMatch Mobile — Flask Backend
=================================
Production-grade REST API for the CineMatch PWA mobile app.
Run: python mobile_server.py
Access from phone: http://<your-ip>:8502
"""
from flask import Flask, jsonify, request, render_template, send_from_directory
import pickle
import pandas as pd
import numpy as np
import gzip
import hashlib
import os
import urllib.parse
import requests as http_requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ML Models
from ml_models import (
    predict_sentiment, get_sentiment_confidence,
    predict_rating, get_feature_importance, get_model_stats
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# ==========================================
# CONFIGURATION
# ==========================================
API_KEY = "e9324b946a1cfdd8f612f18690be72d7"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
poster_cache = {}
tmdb_session = http_requests.Session()

# ==========================================
# DATA LOADING
# ==========================================
print("[*] Loading CineMatch data...")
movies_path = os.path.join(BASE_DIR, 'movie_list_optimized.pkl')
if not os.path.exists(movies_path):
    movies_path = os.path.join(BASE_DIR, 'movie_list.pkl')
movies_dict = pickle.load(open(movies_path, 'rb'))
movies_df = pd.DataFrame(movies_dict)

movies_df['year_int'] = pd.to_datetime(movies_df['release_date'], errors='coerce').dt.year.fillna(0).astype(int)
movies_df['vote_average'] = pd.to_numeric(movies_df['vote_average'], errors='coerce').fillna(0)
movies_df['vote_count'] = pd.to_numeric(movies_df['vote_count'], errors='coerce').fillna(0)
if 'movie_id' not in movies_df.columns and 'id' in movies_df.columns:
    movies_df.rename(columns={'id': 'movie_id'}, inplace=True)
if 'adult' not in movies_df.columns:
    movies_df['adult'] = False
print(f"   [OK] {len(movies_df)} movies loaded")

similarity = None
opt_path = os.path.join(BASE_DIR, 'similarity_optimized.pkl')
gz_path = os.path.join(BASE_DIR, 'similarity.pkl.gz')
pkl_path = os.path.join(BASE_DIR, 'similarity.pkl')

if os.path.exists(opt_path):
    print("   Loading similarity (optimized map)...")
    similarity = pickle.load(open(opt_path, 'rb'))
    print("   [OK] Optimized Similarity dict loaded")
elif os.path.exists(gz_path):
    print("   Loading similarity (compressed)...")
    with gzip.open(gz_path, 'rb') as f:
        similarity = pickle.load(f)
    print("   [OK] Similarity matrix loaded")
elif os.path.exists(pkl_path):
    print("   Loading similarity...")
    similarity = pickle.load(open(pkl_path, 'rb'))
    print("   [OK] Similarity matrix loaded")

# ==========================================
# HELPERS
# ==========================================
def make_hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def csv_path(name):
    return os.path.join(BASE_DIR, name)

def ensure_csvs():
    csvs = {
        'users.csv': ['username', 'password', 'role', 'security_question', 'security_answer'],
        'watchlist.csv': ['username', 'movie', 'date'],
        'feedback.csv': ['username', 'movie', 'feedback', 'date'],
        'reviews.csv': ['username', 'movie', 'rating', 'review', 'sentiment', 'date'],
    }
    for name, cols in csvs.items():
        p = csv_path(name)
        if not os.path.exists(p):
            pd.DataFrame(columns=cols).to_csv(p, index=False)

ensure_csvs()

def get_poster(movie_id, title="Movie"):
    mid = int(float(movie_id))
    if mid in poster_cache:
        return poster_cache[mid]
    try:
        r = tmdb_session.get(f"https://api.themoviedb.org/3/movie/{mid}?api_key={API_KEY}", timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data.get('poster_path'):
                url = "https://image.tmdb.org/t/p/w500" + data['poster_path']
                poster_cache[mid] = url
                return url
    except:
        pass
    clean = urllib.parse.quote(str(title)[:25])
    url = f"https://placehold.co/500x750/1a1a2e/a5b4fc?text={clean}"
    poster_cache[mid] = url
    return url

def movie_to_card(row):
    year = str(row['release_date'])[:4] if pd.notna(row.get('release_date')) else 'N/A'
    rating = round(float(row['vote_average']), 1) if row['vote_average'] > 0 else 0
    genres = ', '.join(row['genres_list'][:2]) if isinstance(row.get('genres_list'), list) else ''
    return {
        'id': int(row['movie_id']), 'title': str(row['title']),
        'year': year, 'rating': rating, 'genres': genres,
    }

def cards_with_posters(df, limit=20):
    rows = list(df.head(limit).iterrows())
    cards = [movie_to_card(row) for _, row in rows]
    def _fetch(card):
        card['poster'] = get_poster(card['id'], card['title'])
        return card
    with ThreadPoolExecutor(max_workers=8) as ex:
        cards = list(ex.map(_fetch, cards))
    return cards

def extract_cert(release_dates):
    if not release_dates or 'results' not in release_dates:
        return None
    ranking = {'A': 18, 'UA 16+': 16, 'UA 13+': 13, 'UA': 12, 'U': 0,
               'NC-17': 18, 'R': 17, 'PG-13': 13, 'PG': 10, 'G': 0}
    results = release_dates['results']
    cd = next((i for i in results if i['iso_3166_1'] == 'IN'), None)
    if not cd:
        cd = next((i for i in results if i['iso_3166_1'] == 'US'), None)
    if not cd:
        return None
    certs = [r.get('certification', '').strip().upper() for r in cd['release_dates'] if r.get('certification', '').strip()]
    if not certs:
        return None
    certs.sort(key=lambda x: ranking.get(x, 0), reverse=True)
    return certs[0]

# ==========================================
# PAGE ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

# ==========================================
# AUTH API
# ==========================================
@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json
    u, p = d.get('username', '').strip(), d.get('password', '')
    if not u or not p:
        return jsonify(success=False, message='Fill all fields')
    df = pd.read_csv(csv_path('users.csv'))
    match = df[(df['username'] == u) & (df['password'] == make_hash(p))]
    if not match.empty:
        return jsonify(success=True, role=match.iloc[0]['role'], username=u)
    return jsonify(success=False, message='Incorrect username or password')

@app.route('/api/register', methods=['POST'])
def api_register():
    d = request.json
    u = d.get('username', '').strip()
    p = d.get('password', '')
    sq = d.get('security_question', '')
    sa = d.get('security_answer', '')
    if not u or not p or not sa:
        return jsonify(success=False, message='Fill all fields including security answer')
    if len(p) < 4:
        return jsonify(success=False, message='Password must be at least 4 characters')
    df = pd.read_csv(csv_path('users.csv'))
    if u in df['username'].values:
        return jsonify(success=False, message='Username already taken')
    new = pd.DataFrame({'username': [u], 'password': [make_hash(p)], 'role': ['user'],
                        'security_question': [sq], 'security_answer': [make_hash(sa.lower())]})
    pd.concat([df, new], ignore_index=True).to_csv(csv_path('users.csv'), index=False)
    return jsonify(success=True)

@app.route('/api/security-question/<username>')
def api_sec_q(username):
    df = pd.read_csv(csv_path('users.csv'))
    row = df[df['username'] == username]
    if row.empty:
        return jsonify(found=False)
    q = row.iloc[0].get('security_question', '')
    if pd.isna(q) or str(q).strip() in ('', 'nan'):
        return jsonify(found=True, has_question=False)
    return jsonify(found=True, has_question=True, question=str(q))

@app.route('/api/forgot-password', methods=['POST'])
def api_forgot():
    d = request.json
    u, ans, np_ = d.get('username', ''), d.get('answer', ''), d.get('new_password', '')
    if not u or not ans or not np_:
        return jsonify(success=False, message='Fill all fields')
    if len(np_) < 4:
        return jsonify(success=False, message='Password must be at least 4 characters')
    df = pd.read_csv(csv_path('users.csv'))
    row = df[df['username'] == u]
    if row.empty:
        return jsonify(success=False, message='User not found')
    if str(row.iloc[0].get('security_answer', '')) != make_hash(ans.lower()):
        return jsonify(success=False, message='Incorrect security answer')
    df.loc[df['username'] == u, 'password'] = make_hash(np_)
    df.to_csv(csv_path('users.csv'), index=False)
    return jsonify(success=True)

# ==========================================
# MOVIES API
# ==========================================
@app.route('/api/movies/top')
def api_top():
    C = movies_df['vote_average'].mean()
    m_val = movies_df['vote_count'].quantile(0.9)
    q = movies_df.loc[movies_df['vote_count'] >= m_val].copy()
    q['score'] = q.apply(lambda x: (x['vote_count']/(x['vote_count']+m_val)*x['vote_average'])+(m_val/(m_val+x['vote_count'])*C), axis=1)
    top = q.sort_values('score', ascending=False)
    return jsonify(cards_with_posters(top, 20))

@app.route('/api/movies/<int:mid>')
def api_detail(mid):
    row = movies_df[movies_df['movie_id'] == mid]
    if row.empty:
        return jsonify(error='Not found'), 404
    r = row.iloc[0]
    detail = movie_to_card(r)
    detail.update({
        'overview': str(r.get('overview', '')) or 'No overview available.',
        'tagline': str(r.get('tagline', '')) if pd.notna(r.get('tagline')) else '',
        'runtime': int(r['runtime']) if pd.notna(r.get('runtime')) and r.get('runtime') else 0,
        'budget': int(r['budget']) if pd.notna(r.get('budget')) and r.get('budget') else 0,
        'revenue': int(r['revenue']) if pd.notna(r.get('revenue')) and r.get('revenue') else 0,
        'director': str(r.get('director', 'Unknown')),
        'cast': list(r['top_cast'])[:6] if isinstance(r.get('top_cast'), list) else [],
        'genres_list': list(r['genres_list']) if isinstance(r.get('genres_list'), list) else [],
        'poster': get_poster(mid, r['title']),
        'backdrop': '', 'cast_rich': [], 'trailer': None,
        'providers': [], 'certification': 'UA',
        'vote_count': int(r.get('vote_count', 0)) if pd.notna(r.get('vote_count')) else 0,
    })
    # TMDB enrichment
    try:
        resp = tmdb_session.get(
            f"https://api.themoviedb.org/3/movie/{mid}?api_key={API_KEY}"
            f"&append_to_response=credits,videos,watch/providers,release_dates", timeout=10)
        if resp.status_code == 200:
            t = resp.json()
            if t.get('poster_path'):
                detail['poster'] = "https://image.tmdb.org/t/p/w500" + t['poster_path']
            if t.get('backdrop_path'):
                detail['backdrop'] = "https://image.tmdb.org/t/p/original" + t['backdrop_path']
            if 'credits' in t and 'cast' in t['credits']:
                for c in t['credits']['cast'][:6]:
                    photo = ("https://image.tmdb.org/t/p/w200" + c['profile_path']) if c.get('profile_path') else f"https://placehold.co/200x200/1a1a2e/a5b4fc?text={urllib.parse.quote(c['name'].split()[0])}"
                    detail['cast_rich'].append({'name': c['name'], 'photo': photo})
            if 'credits' in t and 'crew' in t['credits']:
                d = next((x['name'] for x in t['credits']['crew'] if x['job'] == 'Director'), None)
                if d:
                    detail['director'] = d
            if 'videos' in t:
                for vtype in ['Trailer', 'Teaser']:
                    key = next((v['key'] for v in t['videos'].get('results', []) if v['site'] == 'YouTube' and v['type'] == vtype), None)
                    if key:
                        detail['trailer'] = key
                        break
            if 'watch/providers' in t and 'results' in t['watch/providers']:
                pr = t['watch/providers']['results']
                region = 'IN' if 'IN' in pr else ('US' if 'US' in pr else None)
                if region and 'flatrate' in pr.get(region, {}):
                    detail['providers'] = [{'name': p['provider_name'], 'logo': "https://image.tmdb.org/t/p/original" + p['logo_path']} for p in pr[region]['flatrate'] if p.get('logo_path')]
            if 'release_dates' in t:
                cert = extract_cert(t['release_dates'])
                if cert:
                    detail['certification'] = cert
    except:
        pass
    # AI prediction
    try:
        pred = predict_rating(r)
        if pred:
            detail['ai_prediction'] = pred
    except:
        pass
    return jsonify(detail)

@app.route('/api/movies/<int:mid>/recommend')
def api_rec(mid):
    if similarity is None:
        return jsonify([])
    try:
        row = movies_df[movies_df['movie_id'] == mid]
        if row.empty: return jsonify([])
        
        # Check if we are using the optimized dictionary or full matrix
        if isinstance(similarity, dict):
            title = row.iloc[0]['title']
            dists = similarity.get(title, [])
            if not dists: return jsonify([])
            sub = movies_df.iloc[dists]
        else:
            idx = row.index[0]
            dists = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])[1:11]
            sub = movies_df.iloc[[i[0] for i in dists]]
            
        return jsonify(cards_with_posters(sub, 10))
    except:
        return jsonify([])

@app.route('/api/movies/search')
def api_search():
    q = request.args.get('q', '').strip()
    t = request.args.get('type', 'movie')
    if not q:
        return jsonify([])
    try:
        # Use fillna('') to prevent NaN eval errors in pandas
        if t == 'movie':
            exact = movies_df[movies_df['title'].fillna('').str.lower() == q.lower()]
            if not exact.empty:
                return jsonify(cards_with_posters(exact, 1))
            partial = movies_df[movies_df['title'].fillna('').str.contains(q, case=False, regex=False)]
            return jsonify(cards_with_posters(partial, 20))
        elif t == 'director':
            sub = movies_df[movies_df['director'].fillna('').apply(lambda x: q.lower() in str(x).lower())]
            return jsonify(cards_with_posters(sub, 20))
        elif t == 'actor':
            sub = movies_df[movies_df['top_cast'].fillna('').apply(lambda x: any(q.lower() in str(a).lower() for a in x) if isinstance(x, list) else False)]
            return jsonify(cards_with_posters(sub, 20))
    except Exception as e:
        print(f"Search API Error: {e}")
        return jsonify([])
    return jsonify([])
    return jsonify([])

@app.route('/api/movies/filter')
def api_filter():
    genre = request.args.get('genre', 'All')
    min_y = int(request.args.get('min_year', 1950))
    max_y = int(request.args.get('max_year', 2026))
    min_r = int(request.args.get('min_rating', 0))
    sub = movies_df[(movies_df['year_int'] >= min_y) & (movies_df['year_int'] <= max_y) & (movies_df['vote_average'] * 10 >= min_r)]
    if genre not in ('All', 'Adult'):
        sub = sub[sub['genres_list'].apply(lambda x: genre in x if isinstance(x, list) else False)]
    elif genre == 'Adult':
        sub = sub[sub['adult'] == True] if 'adult' in sub.columns else pd.DataFrame()
    return jsonify(cards_with_posters(sub, 30))

@app.route('/api/genres')
def api_genres():
    genres = set()
    for gl in movies_df['genres_list']:
        if isinstance(gl, list):
            genres.update(gl)
    return jsonify(sorted(list(genres)))

# ==========================================
# USER ACTIONS API
# ==========================================
@app.route('/api/watchlist', methods=['GET', 'POST'])
def api_watchlist():
    if request.method == 'POST':
        d = request.json
        u, m = d['username'], d['movie']
        df = pd.read_csv(csv_path('watchlist.csv'))
        if not ((df['username'] == u) & (df['movie'] == m)).any():
            new = pd.DataFrame({'username': [u], 'movie': [m], 'date': [str(datetime.now().date())]})
            pd.concat([df, new], ignore_index=True).to_csv(csv_path('watchlist.csv'), index=False)
            return jsonify(success=True, message='Added to watchlist!')
        return jsonify(success=False, message='Already in watchlist')
    u = request.args.get('username', '')
    df = pd.read_csv(csv_path('watchlist.csv'))
    titles = df[df['username'] == u]['movie'].tolist()
    if not titles:
        return jsonify([])
    sub = movies_df[movies_df['title'].isin(titles)]
    return jsonify(cards_with_posters(sub, 50))

@app.route('/api/liked', methods=['GET', 'POST'])
def api_liked():
    if request.method == 'POST':
        d = request.json
        u, m = d['username'], d['movie']
        df = pd.read_csv(csv_path('feedback.csv'))
        df = df[~((df['username'] == u) & (df['movie'] == m))]
        new = pd.DataFrame({'username': [u], 'movie': [m], 'feedback': ['Like'], 'date': [str(datetime.now().date())]})
        pd.concat([df, new], ignore_index=True).to_csv(csv_path('feedback.csv'), index=False)
        return jsonify(success=True, message='Liked!')
    u = request.args.get('username', '')
    df = pd.read_csv(csv_path('feedback.csv'))
    titles = df[(df['username'] == u) & (df['feedback'] == 'Like')]['movie'].tolist()
    if not titles:
        return jsonify([])
    sub = movies_df[movies_df['title'].isin(titles)]
    return jsonify(cards_with_posters(sub, 50))

@app.route('/api/review', methods=['POST'])
def api_review():
    d = request.json
    sentiment = predict_sentiment(d['review'])
    df = pd.read_csv(csv_path('reviews.csv'))
    new = pd.DataFrame({
        'username': [d['username']], 'movie': [d['movie']], 'rating': [d['rating']],
        'review': [d['review']], 'sentiment': [sentiment], 'date': [str(datetime.now().date())]
    })
    pd.concat([df, new], ignore_index=True).to_csv(csv_path('reviews.csv'), index=False)
    return jsonify(success=True, sentiment=sentiment)

@app.route('/api/reviews/<path:title>')
def api_reviews(title):
    df = pd.read_csv(csv_path('reviews.csv'))
    revs = df[df['movie'] == title]
    result = []
    for _, r in revs.iterrows():
        conf = get_sentiment_confidence(str(r['review']))
        result.append({
            'username': r['username'], 'rating': int(r['rating']) if pd.notna(r['rating']) else 0,
            'review': str(r['review']), 'sentiment': r.get('sentiment', 'Neutral'),
            'confidence': conf.get('confidence', 50), 'date': str(r.get('date', ''))
        })
    return jsonify(result)

# ==========================================
# ML INSIGHTS API
# ==========================================
@app.route('/api/ml/stats')
def api_ml_stats():
    return jsonify(get_model_stats())

@app.route('/api/ml/feature-importance')
def api_ml_fi():
    return jsonify(get_feature_importance() or {})

@app.route('/api/ml/sentiment', methods=['POST'])
def api_ml_sent():
    text = request.json.get('text', '')
    return jsonify(get_sentiment_confidence(text) if text else {})

@app.route('/api/ml/genre-decades')
def api_ml_gd():
    try:
        mc = movies_df.copy()
        mc['year'] = pd.to_datetime(mc['release_date'], errors='coerce').dt.year
        mc = mc.dropna(subset=['year'])
        mc['decade'] = (mc['year'] // 10 * 10).astype(int).astype(str) + 's'
        data = []
        for _, row in mc.iterrows():
            if isinstance(row['genres_list'], list):
                for g in row['genres_list']:
                    data.append({'decade': row['decade'], 'genre': g})
        gd = pd.DataFrame(data)
        if gd.empty:
            return jsonify([])
        top8 = gd['genre'].value_counts().head(8).index.tolist()
        counts = gd[gd['genre'].isin(top8)].groupby(['decade', 'genre']).size().reset_index(name='count')
        return jsonify(counts.to_dict('records'))
    except:
        return jsonify([])

@app.route('/api/ml/top-directors')
def api_ml_td():
    try:
        d = movies_df[movies_df['director'].notna() & (movies_df['director'] != 'Unknown')].copy()
        stats = d.groupby('director').agg(avg_rating=('vote_average', 'mean'), count=('title', 'count')).reset_index()
        stats = stats[stats['count'] >= 3].sort_values('avg_rating', ascending=False).head(10)
        stats['avg_rating'] = stats['avg_rating'].round(1)
        return jsonify(stats.to_dict('records'))
    except:
        return jsonify([])

@app.route('/api/ml/taste-profile')
def api_ml_tp():
    u = request.args.get('username', '')
    try:
        wl = pd.read_csv(csv_path('watchlist.csv'))
        fb = pd.read_csv(csv_path('feedback.csv'))
        titles = pd.concat([wl[wl['username'] == u]['movie'], fb[(fb['username'] == u) & (fb['feedback'] == 'Like')]['movie']]).unique()
        if len(titles) == 0:
            return jsonify({})
        sub = movies_df[movies_df['title'].isin(titles)]
        genres = []
        for _, r in sub.iterrows():
            if isinstance(r['genres_list'], list):
                genres.extend(r['genres_list'])
        return jsonify(pd.Series(genres).value_counts().head(8).to_dict() if genres else {})
    except:
        return jsonify({})

@app.route('/api/ml/sentiment-distribution')
def api_ml_sd():
    try:
        df = pd.read_csv(csv_path('reviews.csv'))
        if df.empty or 'sentiment' not in df.columns:
            return jsonify({})
        return jsonify(df['sentiment'].value_counts().to_dict())
    except:
        return jsonify({})

# ==========================================
# ADMIN API
# ==========================================
@app.route('/api/admin/stats')
def api_admin_stats():
    try:
        fb = pd.read_csv(csv_path('feedback.csv'))
        wl = pd.read_csv(csv_path('watchlist.csv'))
        rv = pd.read_csv(csv_path('reviews.csv'))
        return jsonify(total_likes=len(fb), total_watchlist=len(wl), total_reviews=len(rv),
                       top_liked=fb['movie'].value_counts().head(10).to_dict() if not fb.empty else {})
    except:
        return jsonify(total_likes=0, total_watchlist=0, total_reviews=0, top_liked={})

@app.route('/api/admin/users')
def api_admin_users():
    try:
        return jsonify([u for u in pd.read_csv(csv_path('users.csv'))['username'].tolist() if u != 'admin'])
    except:
        return jsonify([])

@app.route('/api/admin/reset-password', methods=['POST'])
def api_admin_reset():
    d = request.json
    u, p = d.get('username', ''), d.get('new_password', '')
    if not u or not p or len(p) < 4:
        return jsonify(success=False, message='Invalid input')
    df = pd.read_csv(csv_path('users.csv'))
    if u not in df['username'].values:
        return jsonify(success=False, message='User not found')
    df.loc[df['username'] == u, 'password'] = make_hash(p)
    df.to_csv(csv_path('users.csv'), index=False)
    return jsonify(success=True)

# ==========================================
# RUN
# ==========================================
if __name__ == '__main__':
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "localhost"
    print(f"\n{'='*50}")
    print(f"CineMatch Mobile is LIVE!")
    print(f"{'='*50}")
    print(f"Open on phone: http://{local_ip}:8502")
    print(f"Open on PC:    http://localhost:8502")
    print(f"{'='*50}\n")
    app.run(host='0.0.0.0', port=8502, debug=False)
