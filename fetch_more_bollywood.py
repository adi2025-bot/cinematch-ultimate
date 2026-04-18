"""
Fetch MORE Bollywood Movies from TMDB & merge into dataset
Targets: recent 2023-2026 releases, classics, and popular titles
"""
import pickle
import requests
import pandas as pd
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = "e9324b946a1cfdd8f612f18690be72d7"
BASE_URL = "https://api.themoviedb.org/3"
session = requests.Session()

# ===== Load existing dataset =====
print("=" * 55)
print("   BOLLYWOOD MOVIES FETCHER — Extended Edition")
print("=" * 55)
print("\n[1] Loading existing dataset...")
movies_dict = pickle.load(open('movie_list.pkl', 'rb'))
existing_df = pd.DataFrame(movies_dict)
existing_ids = set(existing_df['movie_id'].values)
print(f"    Existing: {len(existing_df)} movies ({len(existing_ids)} unique IDs)")

# ===== Fetch functions =====
def discover_movies(params, label=""):
    """Fetch movies from TMDB discover endpoint"""
    movies = []
    page = 1
    while page <= 500:
        try:
            p = {**params, "api_key": API_KEY, "page": page}
            r = session.get(f"{BASE_URL}/discover/movie", params=p, timeout=10)
            if r.status_code == 429:
                time.sleep(2)
                continue
            if r.status_code != 200:
                break
            data = r.json()
            results = data.get('results', [])
            if not results:
                break
            for m in results:
                if m['id'] not in existing_ids and m['id'] not in [x['id'] for x in movies]:
                    movies.append(m)
            total_pages = data.get('total_pages', 1)
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"    Error: {e}")
            time.sleep(1)
            continue
    print(f"    {label}: {len(movies)} new movies found")
    return movies

def search_movies_by_name(names):
    """Search specific movies by name"""
    movies = []
    for name in names:
        try:
            r = session.get(f"{BASE_URL}/search/movie", params={
                "api_key": API_KEY, "query": name, "language": "en-US"
            }, timeout=8)
            if r.status_code == 200:
                results = r.json().get('results', [])
                for m in results:
                    if m['id'] not in existing_ids and m.get('original_language') == 'hi':
                        movies.append(m)
                        break
            time.sleep(0.3)
        except:
            pass
    return movies

def get_movie_details(movie_id):
    """Get cast, crew, keywords for a movie"""
    try:
        r = session.get(f"{BASE_URL}/movie/{movie_id}", params={
            "api_key": API_KEY,
            "append_to_response": "credits,keywords"
        }, timeout=8)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(2)
            return get_movie_details(movie_id)
    except:
        pass
    return None

def process_movie(movie):
    """Convert TMDB movie to our dataset format"""
    details = get_movie_details(movie['id'])
    
    genres = []
    if details and 'genres' in details:
        genres = [g['name'] for g in details['genres']]
    
    cast = []
    director = []
    if details and 'credits' in details:
        cast = [c['name'] for c in details['credits'].get('cast', [])[:5]]
        director = [c['name'] for c in details['credits'].get('crew', []) if c.get('job') == 'Director']
    
    keywords = []
    if details and 'keywords' in details:
        keywords = [k['name'] for k in details['keywords'].get('keywords', [])[:10]]
    
    # Build tags string (same format as existing)
    tag_parts = []
    tag_parts.extend([g.replace(' ', '') for g in genres])
    tag_parts.extend([k.replace(' ', '') for k in keywords[:5]])
    tag_parts.extend([c.replace(' ', '') for c in cast[:3]])
    if director:
        tag_parts.append(director[0].replace(' ', ''))
    overview = str(movie.get('overview', ''))
    if overview:
        tag_parts.extend(overview.split()[:100])
    tags = ' '.join(tag_parts).lower()
    
    return {
        'movie_id': movie['id'],
        'title': movie.get('title', 'Unknown'),
        'overview': overview,
        'genres': str(genres),
        'keywords': str(keywords),
        'cast': str(cast),
        'crew': str(director),
        'vote_average': movie.get('vote_average', 0),
        'vote_count': movie.get('vote_count', 0),
        'popularity': movie.get('popularity', 0),
        'release_date': movie.get('release_date', ''),
        'runtime': details.get('runtime', 0) if details else 0,
        'budget': details.get('budget', 0) if details else 0,
        'revenue': details.get('revenue', 0) if details else 0,
        'status': details.get('status', 'Released') if details else 'Released',
        'production_companies': str([p['name'] for p in (details.get('production_companies', [])[:3] if details else [])]),
        'tagline': details.get('tagline', '') if details else '',
        'genres_list': genres,
        'keywords_list': keywords,
        'top_cast': cast,
        'director': director if director else ['Unknown'],
        'tags': tags,
        'adult': movie.get('adult', False),
        'original_language': 'hi',
    }

# ===== Fetch from multiple queries =====
print("\n[2] Fetching Bollywood movies from TMDB...")

all_new = []

# Recent blockbusters 2023-2026
recent = discover_movies({
    "with_original_language": "hi",
    "sort_by": "popularity.desc",
    "primary_release_date.gte": "2023-01-01",
    "vote_count.gte": 5,
}, "Recent 2023-2026")
all_new.extend(recent)

# Top rated Bollywood (all time) — lower vote threshold
top_rated = discover_movies({
    "with_original_language": "hi",
    "sort_by": "vote_average.desc",
    "vote_count.gte": 50,
}, "Top Rated (50+ votes)")
all_new.extend([m for m in top_rated if m['id'] not in {x['id'] for x in all_new}])

# Revenue sorted
revenue = discover_movies({
    "with_original_language": "hi",
    "sort_by": "revenue.desc",
    "vote_count.gte": 10,
}, "Revenue sorted")
all_new.extend([m for m in revenue if m['id'] not in {x['id'] for x in all_new}])

# Popularity — lower threshold to catch more
popular_low = discover_movies({
    "with_original_language": "hi",
    "sort_by": "popularity.desc",
    "vote_count.gte": 3,
    "primary_release_date.gte": "2020-01-01",
}, "Popular 2020+ (low threshold)")
all_new.extend([m for m in popular_low if m['id'] not in {x['id'] for x in all_new}])

# Classic Bollywood
classic = discover_movies({
    "with_original_language": "hi",
    "sort_by": "vote_average.desc",
    "primary_release_date.lte": "1999-12-31",
    "vote_count.gte": 20,
}, "Classics (pre-2000)")
all_new.extend([m for m in classic if m['id'] not in {x['id'] for x in all_new}])

# Specific well-known recent movies people expect
print("\n    Searching specific titles...")
specific_titles = [
    "Stree 2", "Pushpa 2", "Kalki 2898 AD", "Fighter 2024", "Crew 2024",
    "Shaitaan", "Teri Baaton Mein Aisa Uljha Jiya", "Amar Prem Ki Prem Kahani",
    "Bade Miyan Chote Miyan", "Maidaan", "Laapataa Ladies", "Dunki",
    "Sam Bahadur", "12th Fail", "Tiger 3", "Tejas", "Ganapath",
    "Jawan", "Gadar 2", "OMG 2", "Rocky Aur Rani Kii Prem Kahaani",
    "Mission Raniganj", "Fukrey 3", "Khichdi 2", "Dream Girl 2",
    "Satyaprem Ki Katha", "Adipurush", "Bhola", "Kisi Ka Bhai Kisi Ki Jaan",
    "Tu Jhoothi Main Makkaar", "Pathaan", "Shehzada", "Selfiee",
    "Cirkus", "Drishyam 2", "Bhediya", "An Action Hero", "Phone Bhoot",
    "Mili", "Ram Setu", "Thank God", "Goodbye", "Vikram Vedha",
    "Brahmastra", "Liger", "Laal Singh Chaddha", "Raksha Bandhan",
    "Shamshera", "Ek Villain Returns", "Samrat Prithviraj",
    "Jhund", "Gehraiyaan", "Badhaai Do", "Looop Lapeta",
    "Chandigarh Kare Aashiqui", "83", "Tadap", "Antim",
    "Sooryavanshi", "Sardar Udham", "Bhuj", "Shershaah",
    "Toofaan", "Haseen Dillruba", "Roohi", "Sandeep Aur Pinky Faraar",
    "Mumbai Saga", "The White Tiger", "Coolie No. 1", "Laxmii",
    "Ludo", "Chhalaang", "Gunjan Saxena", "Dil Bechara", "Gulabo Sitabo",
    "Thappad", "Malang", "Jawaani Jaaneman", "Chhapaak", "Tanhaji",
    "Singham Again", "Bhool Bhulaiya 3", "Sky Force", "Deva",
    "Baby John", "Auron Mein Kahan Dum Tha", "Khel Khel Mein",
    "Vedaa", "Sarfira", "Chandu Champion", "Mr & Mrs Mahi",
]
specific = search_movies_by_name(specific_titles)
all_new.extend([m for m in specific if m['id'] not in {x['id'] for x in all_new}])
print(f"    Specific titles: {len(specific)} found")

# De-duplicate
seen_ids = set()
unique_new = []
for m in all_new:
    if m['id'] not in seen_ids and m['id'] not in existing_ids:
        seen_ids.add(m['id'])
        unique_new.append(m)

print(f"\n[3] Total new unique movies to process: {len(unique_new)}")

if not unique_new:
    print("No new movies found! Your dataset is already up to date.")
    sys.exit(0)

# ===== Process with details =====
print(f"\n[4] Fetching details for {len(unique_new)} movies...")
processed = []
failed = 0
for i, movie in enumerate(unique_new):
    try:
        result = process_movie(movie)
        if result:
            processed.append(result)
    except Exception as e:
        failed += 1
    if (i + 1) % 50 == 0 or (i + 1) == len(unique_new):
        print(f"    Processed {i + 1}/{len(unique_new)} ({len(processed)} ok, {failed} failed)")
    time.sleep(0.3)

print(f"\n[5] Merging {len(processed)} new movies with existing {len(existing_df)}...")
new_df = pd.DataFrame(processed)

# Ensure column compatibility
for col in existing_df.columns:
    if col not in new_df.columns:
        new_df[col] = None
for col in new_df.columns:
    if col not in existing_df.columns:
        existing_df[col] = None

combined_df = pd.concat([existing_df, new_df], ignore_index=True)

# Remove any duplicates by movie_id
combined_df = combined_df.drop_duplicates(subset='movie_id', keep='first')

# Save
print(f"\n[6] Saving dataset ({len(combined_df)} total movies)...")
combined_dict = combined_df.to_dict('list')
with open('movie_list.pkl', 'wb') as f:
    pickle.dump(combined_dict, f)

print(f"\n{'='*55}")
print(f"   SUCCESS!")
print(f"   Previous: {len(existing_df)} movies")
print(f"   Added:    {len(processed)} Bollywood movies")
print(f"   Total:    {len(combined_df)} movies")
print(f"{'='*55}")
print(f"\n[!] Now run: python regenerate_similarity.py")
print(f"    Then:    python optimize_data.py")
print(f"    Then commit & push to deploy!")
