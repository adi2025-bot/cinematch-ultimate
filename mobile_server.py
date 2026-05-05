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
    from flask import make_response
    r = make_response(render_template('index.html'))
    r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    r.headers['Pragma'] = 'no-cache'
    r.headers['Expires'] = '0'
    return r

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
    if 'adult' in q.columns:
        q = q[q['adult'] == False]
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
                    detail['cast_rich'].append({'name': c['name'], 'photo': photo, 'id': c.get('id', 0), 'character': c.get('character', '')})
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
                    tmdb_link = pr[region].get('link', '')
                    detail['providers'] = [{'name': p['provider_name'], 'logo': "https://image.tmdb.org/t/p/original" + p['logo_path'], 'url': tmdb_link} for p in pr[region]['flatrate'] if p.get('logo_path')]
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

@app.route('/api/movies/suggestions')
def api_suggestions():
    """Lightweight autocomplete: returns up to 8 title matches."""
    q = request.args.get('q', '').strip()
    g = request.args.get('genre', '')
    if not q or len(q) < 2:
        return jsonify([])
    try:
        matches = movies_df[movies_df['title'].fillna('').str.contains(q, case=False, regex=False)]
        if 'adult' in matches.columns:
            if g == 'Adult':
                matches = matches[matches['adult'] == True]
            else:
                matches = matches[matches['adult'] == False]
        titles = matches['title'].head(8).tolist()
        # Return id + title for each suggestion
        results = []
        for _, row in matches.head(8).iterrows():
            results.append({'id': int(row['movie_id']), 'title': str(row['title'])})
        return jsonify(results)
    except:
        return jsonify([])

@app.route('/api/movies/search')
def api_search():
    q = request.args.get('q', '').strip()
    t = request.args.get('type', 'movie')
    if not q:
        return jsonify([])
    try:
        # Hide adult movies from search globally
        search_df = movies_df.copy()
        if 'adult' in search_df.columns:
            search_df = search_df[search_df['adult'] == False]
            
        # Use fillna('') to prevent NaN eval errors in pandas
        if t == 'movie':
            exact = search_df[search_df['title'].fillna('').str.lower() == q.lower()]
            if not exact.empty:
                # Automatically append recommendations downstream
                idx = exact.index[0]
                recs = pd.DataFrame()
                if isinstance(similarity, dict):
                    title = exact.iloc[0]['title']
                    dists = similarity.get(title, [])
                    if dists: recs = movies_df.iloc[dists[:10]]
                    if not recs.empty and 'adult' in recs.columns:
                        recs = recs[recs['adult'] == False]
                else:
                    dists = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])[1:11]
                    recs = movies_df.iloc[[i[0] for i in dists]]
                    if not recs.empty and 'adult' in recs.columns:
                        recs = recs[recs['adult'] == False]
                
                if not recs.empty:
                    combined = pd.concat([exact, recs])
                    return jsonify(cards_with_posters(combined, 11))
                return jsonify(cards_with_posters(exact, 1))
            
            partial = search_df[search_df['title'].fillna('').str.contains(q, case=False, regex=False)]
            return jsonify(cards_with_posters(partial, 20))
        elif t == 'director':
            sub = search_df[search_df['director'].fillna('').apply(lambda x: q.lower() in str(x).lower())]
            return jsonify(cards_with_posters(sub, 20))
        elif t == 'actor':
            sub = search_df[search_df['top_cast'].fillna('').apply(lambda x: any(q.lower() in str(a).lower() for a in x) if isinstance(x, list) else False)]
            return jsonify(cards_with_posters(sub, 20))
    except Exception as e:
        print(f"Search API Error: {e}")
        return jsonify([])
    return jsonify([])

@app.route('/api/movies/by-song')
def api_by_song():
    q = request.args.get('q', '').strip()
    if not q: return jsonify({'success': False})
    
    data = _saavn_get('search/songs', {'query': q, 'limit': 1})
    if not data: return jsonify({'success': False})
    
    try:
        if data.get('success') and data.get('data', {}).get('results'):
            song = data['data']['results'][0]
        elif isinstance(data.get('results'), list) and len(data['results']) > 0:
            song = data['results'][0]
        else:
            return jsonify({'success': False})
            
        album_name = ''
        if isinstance(song.get('album'), dict):
            album_name = song['album'].get('name', '')
        elif isinstance(song.get('album'), str):
            album_name = song['album']
            
        if not album_name:
            return jsonify({'success': False})
            
        # Clean album name (remove (Original Motion Picture Soundtrack) etc.)
        import re
        album_clean = re.sub(r'\(.*?\)', '', album_name).strip()
        
        # Search movies_df
        exact = movies_df[movies_df['title'].fillna('').str.lower() == album_clean.lower()]
        if not exact.empty:
            return jsonify({'success': True, 'movie': movie_to_card(exact.iloc[0])})
            
        partial = movies_df[movies_df['title'].fillna('').str.contains(album_clean, case=False, regex=False)]
        if not partial.empty:
            return jsonify({'success': True, 'movie': movie_to_card(partial.iloc[0])})
            
        return jsonify({'success': False})
    except Exception as e:
        print(f"By Song API Error: {e}")
        return jsonify({'success': False})

@app.route('/api/movies/filter')
def api_filter():
    genre = request.args.get('genre', 'All')
    q = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    min_y = int(request.args.get('min_year', 1950))
    max_y = int(request.args.get('max_year', 2026))
    min_r = int(request.args.get('min_rating', 0))
    limit = 30
    
    sub = movies_df[(movies_df['year_int'] >= min_y) & (movies_df['year_int'] <= max_y) & (movies_df['vote_average'] * 10 >= min_r)]
    if genre not in ('All', 'Adult', 'Bollywood'):
        sub = sub[sub['genres_list'].apply(lambda x: genre in x if isinstance(x, list) else False)]
        if 'adult' in sub.columns:
            sub = sub[sub['adult'] == False]
    elif genre == 'Adult':
        sub = sub[sub['adult'] == True] if 'adult' in sub.columns else pd.DataFrame()
    elif genre == 'Bollywood':
        if 'original_language' in sub.columns:
            sub = sub[sub['original_language'] == 'hi']
        if 'adult' in sub.columns:
            sub = sub[sub['adult'] == False]
    elif genre == 'All':
        if 'adult' in sub.columns:
            sub = sub[sub['adult'] == False]
            
    if q:
        sub = sub[sub['title'].fillna('').str.contains(q, case=False, regex=False)]
        
    start = (page - 1) * limit
    end = start + limit
    return jsonify(cards_with_posters(sub.iloc[start:end], limit))

@app.route('/api/genres')
def api_genres():
    genres = set()
    for gl in movies_df['genres_list']:
        if isinstance(gl, list):
            genres.update(gl)
    genre_list = sorted(list(genres))
    if 'Adult' not in genre_list:
        genre_list.append('Adult')
    if 'Bollywood' not in genre_list:
        genre_list.append('Bollywood')
    return jsonify(genre_list)

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
# SONGS API (JioSaavn) — Album-based Lookup
# ==========================================
SAAVN_INSTANCES = [
    "https://jiosaavnapi-six.vercel.app/api",
    "https://saavn.sumit.co/api",
]
songs_cache = {}

def _saavn_get(path, params, timeout=10):
    """Try multiple JioSaavn API instances, return first successful JSON response."""
    for base in SAAVN_INSTANCES:
        try:
            r = tmdb_session.get(f"{base}/{path}", params=params, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                return data
        except Exception:
            continue
    return None

def _extract_song(s):
    """Extract a clean song dict from a JioSaavn song object."""
    # Best quality image (500x500)
    image = ''
    if s.get('image'):
        for img in s['image']:
            if img.get('quality') == '500x500':
                image = img['url']
                break
        if not image and s['image']:
            image = s['image'][-1].get('url', '')

    # 160kbps streaming URL (good quality, low bandwidth)
    audio_url = ''
    if s.get('downloadUrl'):
        for dl in s['downloadUrl']:
            if dl.get('quality') == '160kbps':
                audio_url = dl['url']
                break
        if not audio_url and s['downloadUrl']:
            audio_url = s['downloadUrl'][-1].get('url', '')

    # Primary artist names
    artists = []
    if isinstance(s.get('artists'), dict) and s['artists'].get('primary'):
        artists = [a['name'] for a in s['artists']['primary'][:3]]
    elif isinstance(s.get('artists'), dict) and s['artists'].get('all'):
        artists = [a['name'] for a in s['artists']['all'][:3]]
    elif isinstance(s.get('primaryArtists'), str) and s['primaryArtists']:
        artists = [a.strip() for a in s['primaryArtists'].split(',')[:3]]

    return {
        'id': s.get('id', ''),
        'name': s.get('name', 'Unknown'),
        'artist': ', '.join(artists) if artists else 'Unknown',
        'album': s.get('album', {}).get('name', '') if isinstance(s.get('album'), dict) else str(s.get('album', '')),
        'image': image,
        'duration': int(s.get('duration', 0)),
        'url': audio_url,
        'year': s.get('year', ''),
        'language': s.get('language', ''),
        'playCount': s.get('playCount', 0),
    }


def _score_album(album, q_clean, movie_year):
    """Score how well an album matches the movie. Higher = better."""
    import re
    name = album.get('name', '') or album.get('title', '') or ''
    name_clean = re.sub(r'[^a-z0-9]', '', name.lower())
    score = 0

    # Exact match is best
    if name_clean == q_clean:
        score += 100
    elif q_clean in name_clean:
        score += 60
    elif name_clean in q_clean:
        score += 40
    else:
        return -1  # No match at all

    # Year proximity bonus
    album_year = 0
    if str(album.get('year', '')).isdigit():
        album_year = int(album['year'])
    if movie_year > 0 and album_year > 0:
        diff = abs(album_year - movie_year)
        if diff == 0:
            score += 50
        elif diff == 1:
            score += 30
        elif diff == 2:
            score += 10
        elif diff > 5:
            score -= 30

    # Song count bonus — real movie albums usually have 4+ songs
    song_count = album.get('songCount', 0)
    if isinstance(song_count, str) and song_count.isdigit():
        song_count = int(song_count)
    if song_count and song_count >= 4:
        score += 20
    elif song_count and song_count >= 2:
        score += 10

    # Language bonus — prefer Hindi for Bollywood
    lang = str(album.get('language', '')).lower()
    if lang in ('hindi', 'telugu', 'tamil', 'kannada', 'malayalam', 'bengali', 'punjabi', 'marathi'):
        score += 5

    return score


@app.route('/api/songs/search')
def api_songs_search():
    """Search songs by movie name — uses album-based lookup for accuracy.
    
    Strategy:
    1. Search for albums matching the movie title
    2. Pick the best-matching album (by title + year)
    3. Fetch all songs from that album
    This ensures we return the actual movie soundtrack, not random songs.
    """
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    # Check cache
    year_str = request.args.get('year', '')
    cache_key = f"{q.lower()}|{year_str}"
    if cache_key in songs_cache:
        return jsonify(songs_cache[cache_key])

    try:
        import re
        q_clean = re.sub(r'[^a-z0-9]', '', q.lower())
        movie_year = int(year_str) if year_str.isdigit() else 0

        # ── STEP 1: Search for albums matching the movie name ──
        album_data = _saavn_get('search/albums', {'query': q, 'limit': 15})

        best_album_id = None
        best_score = -1

        if album_data:
            albums = []
            if album_data.get('success') and album_data.get('data', {}).get('results'):
                albums = album_data['data']['results']
            elif album_data.get('data') and isinstance(album_data['data'], list):
                albums = album_data['data']
            elif isinstance(album_data.get('results'), list):
                albums = album_data['results']

            for alb in albums:
                score = _score_album(alb, q_clean, movie_year)
                if score > best_score:
                    best_score = score
                    best_album_id = alb.get('id')

        # ── STEP 2: Fetch all songs from the best matching album ──
        songs = []

        if best_album_id and best_score >= 40:
            detail = _saavn_get('albums', {'id': best_album_id})
            if detail:
                song_list = []
                if detail.get('success') and detail.get('data', {}).get('songs'):
                    song_list = detail['data']['songs']
                elif detail.get('data') and isinstance(detail['data'], list):
                    song_list = detail['data']
                elif detail.get('songs'):
                    song_list = detail['songs']

                for s in song_list:
                    song = _extract_song(s)
                    if song['url']:  # Only include playable songs
                        songs.append(song)

        # ── STEP 3: Fallback — song search if album approach found nothing ──
        if not songs:
            search_query = f"{q} songs"
            data = _saavn_get('search/songs', {'query': search_query, 'limit': 25})
            if data:
                results_list = []
                if data.get('success') and data.get('data', {}).get('results'):
                    results_list = data['data']['results']
                elif isinstance(data.get('results'), list):
                    results_list = data['results']

                # Group by album to prefer soundtrack albums
                album_groups = {}
                for s in results_list:
                    album_name = ''
                    if isinstance(s.get('album'), dict):
                        album_name = s['album'].get('name', '')
                    album_clean = re.sub(r'[^a-z0-9]', '', album_name.lower())
                    if album_clean and (q_clean in album_clean or album_clean in q_clean):
                        aid = str(s.get('album', {}).get('id', ''))
                        if aid not in album_groups:
                            album_groups[aid] = []
                        album_groups[aid].append(s)

                # Prefer the album group with most songs (likely the real soundtrack)
                if album_groups:
                    best_group = max(album_groups.values(), key=len)
                    for s in best_group:
                        song = _extract_song(s)
                        if song['url']:
                            songs.append(song)

                # If still nothing, take individual matches loosely
                if not songs:
                    for s in results_list[:10]:
                        album_name = ''
                        if isinstance(s.get('album'), dict):
                            album_name = s['album'].get('name', '')
                        album_clean = re.sub(r'[^a-z0-9]', '', album_name.lower())
                        if album_clean and (q_clean in album_clean or album_clean in q_clean):
                            song = _extract_song(s)
                            if song['url']:
                                songs.append(song)

        # Deduplicate by song ID
        seen_ids = set()
        unique_songs = []
        for s in songs:
            if s['id'] not in seen_ids:
                seen_ids.add(s['id'])
                unique_songs.append(s)
        songs = unique_songs

        # Cache the result
        songs_cache[cache_key] = songs
        return jsonify(songs)
    except Exception as e:
        print(f"Songs API error: {e}")
        return jsonify([])

# ==========================================
# PERSON / ACTOR API
# ==========================================
person_cache = {}

@app.route('/api/person/<int:pid>')
def api_person(pid):
    """Get actor/person details from TMDB — biography, filmography, etc."""
    if pid in person_cache:
        return jsonify(person_cache[pid])
    try:
        r = tmdb_session.get(
            f"https://api.themoviedb.org/3/person/{pid}?api_key={API_KEY}&append_to_response=movie_credits",
            timeout=10
        )
        if r.status_code != 200:
            return jsonify(error='Not found'), 404
        p = r.json()
        photo = ("https://image.tmdb.org/t/p/w500" + p['profile_path']) if p.get('profile_path') else ''
        # Get top movies sorted by popularity
        movies = []
        if 'movie_credits' in p and 'cast' in p['movie_credits']:
            sorted_movies = sorted(p['movie_credits']['cast'], key=lambda x: x.get('popularity', 0), reverse=True)
            for m in sorted_movies[:12]:
                poster = ("https://image.tmdb.org/t/p/w300" + m['poster_path']) if m.get('poster_path') else ''
                if poster:
                    movies.append({
                        'id': m.get('id', 0), 'title': m.get('title', ''),
                        'year': str(m.get('release_date', ''))[:4],
                        'rating': round(m.get('vote_average', 0), 1),
                        'poster': poster, 'character': m.get('character', '')
                    })
        result = {
            'id': pid, 'name': p.get('name', ''),
            'photo': photo,
            'biography': p.get('biography', 'No biography available.'),
            'birthday': p.get('birthday', ''),
            'deathday': p.get('deathday', ''),
            'birthplace': p.get('place_of_birth', ''),
            'known_for': p.get('known_for_department', 'Acting'),
            'popularity': round(p.get('popularity', 0), 1),
            'gender': 'Male' if p.get('gender') == 2 else 'Female' if p.get('gender') == 1 else 'Unknown',
            'movies': movies,
            'total_movies': len(p.get('movie_credits', {}).get('cast', [])),
        }
        person_cache[pid] = result
        return jsonify(result)
    except Exception as e:
        print(f"Person API error: {e}")
        return jsonify(error='Failed to fetch'), 500

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
