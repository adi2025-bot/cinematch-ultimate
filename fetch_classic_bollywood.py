"""
Fetch Classic Bollywood Movies (1950-2000) from TMDB
=====================================================
Adds old Hindi-language movies to the CineMatch dataset.
Run: python fetch_classic_bollywood.py
"""
import pickle
import requests
import time
import os

API_KEY = "e9324b946a1cfdd8f612f18690be72d7"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def fetch_classic_bollywood():
    """Fetch Hindi movies from 1950-2000 from TMDB discover API."""
    all_movies = []
    seen_ids = set()
    
    session = requests.Session()
    
    # Fetch decade by decade for better coverage
    decades = [
        (1950, 1959), (1960, 1969), (1970, 1979),
        (1980, 1989), (1990, 2000)
    ]
    
    for start_year, end_year in decades:
        print(f"\n--- Fetching {start_year}-{end_year} ---")
        page = 1
        max_pages = 30  # Up to 30 pages per decade
        
        while page <= max_pages:
            try:
                url = (
                    f"https://api.themoviedb.org/3/discover/movie"
                    f"?api_key={API_KEY}"
                    f"&with_original_language=hi"
                    f"&primary_release_date.gte={start_year}-01-01"
                    f"&primary_release_date.lte={end_year}-12-31"
                    f"&sort_by=popularity.desc"
                    f"&page={page}"
                    f"&include_adult=false"
                )
                r = session.get(url, timeout=15)
                if r.status_code != 200:
                    print(f"  Error on page {page}: {r.status_code}")
                    break
                    
                data = r.json()
                results = data.get('results', [])
                if not results:
                    break
                
                for m in results:
                    mid = m['id']
                    if mid not in seen_ids:
                        seen_ids.add(mid)
                        all_movies.append({
                            'movie_id': mid,
                            'title': m.get('title', ''),
                            'overview': m.get('overview', ''),
                            'release_date': m.get('release_date', ''),
                            'vote_average': m.get('vote_average', 0),
                            'vote_count': m.get('vote_count', 0),
                            'genres_list': [],  # Will be filled below
                            'genre_ids': m.get('genre_ids', []),
                            'original_language': m.get('original_language', 'hi'),
                            'popularity': m.get('popularity', 0),
                            'adult': m.get('adult', False),
                            'poster_path': m.get('poster_path', ''),
                        })
                
                total_pages = data.get('total_pages', 1)
                print(f"  Page {page}/{min(total_pages, max_pages)} — {len(results)} movies (Total: {len(all_movies)})")
                
                if page >= total_pages:
                    break
                page += 1
                time.sleep(0.25)  # Rate limit
                
            except Exception as e:
                print(f"  Error: {e}")
                time.sleep(1)
                break
    
    print(f"\n[OK] Fetched {len(all_movies)} classic Bollywood movies")
    
    # Map genre IDs to names
    genre_map = {
        28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy',
        80: 'Crime', 99: 'Documentary', 18: 'Drama', 10751: 'Family',
        14: 'Fantasy', 36: 'History', 27: 'Horror', 10402: 'Music',
        9648: 'Mystery', 10749: 'Romance', 878: 'Science Fiction',
        10770: 'TV Movie', 53: 'Thriller', 10752: 'War', 37: 'Western'
    }
    
    for m in all_movies:
        m['genres_list'] = [genre_map.get(gid, 'Other') for gid in m.get('genre_ids', [])]
        m.pop('genre_ids', None)
        m.pop('poster_path', None)
        # Add placeholder fields to match existing dataset
        m.setdefault('director', 'Unknown')
        m.setdefault('top_cast', [])
        m.setdefault('runtime', 0)
        m.setdefault('budget', 0)
        m.setdefault('revenue', 0)
        m.setdefault('tagline', '')
        m.setdefault('tags', '')
    
    # Load existing dataset and merge
    movies_path = os.path.join(BASE_DIR, 'movie_list_optimized.pkl')
    if not os.path.exists(movies_path):
        movies_path = os.path.join(BASE_DIR, 'movie_list.pkl')
    
    import pandas as pd
    existing_df = pd.DataFrame(pickle.load(open(movies_path, 'rb')))
    if 'movie_id' not in existing_df.columns and 'id' in existing_df.columns:
        existing_df.rename(columns={'id': 'movie_id'}, inplace=True)
    
    existing_ids = set(existing_df['movie_id'].astype(int).tolist())
    new_movies = [m for m in all_movies if m['movie_id'] not in existing_ids]
    
    print(f"[INFO] Existing: {len(existing_df)}, New unique: {len(new_movies)}")
    
    if new_movies:
        new_df = pd.DataFrame(new_movies)
        # Align columns
        for col in existing_df.columns:
            if col not in new_df.columns:
                new_df[col] = '' if existing_df[col].dtype == 'object' else 0
        
        merged = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Save
        out_path = os.path.join(BASE_DIR, 'movie_list_optimized.pkl')
        pickle.dump(merged.to_dict(), open(out_path, 'wb'))
        print(f"[OK] Saved {len(merged)} total movies to {out_path}")
        print(f"\n⚠️  Run 'python regenerate_similarity.py' to update recommendations!")
    else:
        print("[INFO] No new movies to add — all already in dataset.")

if __name__ == '__main__':
    fetch_classic_bollywood()
