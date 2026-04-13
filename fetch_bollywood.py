"""
Fetch Bollywood Movies from TMDB and merge with existing dataset
Run this script to add 5000 Hindi movies to your movie_list.pkl
"""

import pickle
import requests
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor

API_KEY = "e9324b946a1cfdd8f612f18690be72d7"
BASE_URL = "https://api.themoviedb.org/3"

def fetch_bollywood_movies(total_movies=5000):
    """Fetch Bollywood/Hindi movies from TMDB"""
    movies = []
    page = 1
    movies_per_page = 20
    total_pages = (total_movies // movies_per_page) + 1
    
    print(f"[*] Fetching {total_movies} Bollywood movies...")
    
    while len(movies) < total_movies and page <= 500:  # TMDB max 500 pages
        try:
            # Discover Hindi movies sorted by popularity
            url = f"{BASE_URL}/discover/movie"
            params = {
                "api_key": API_KEY,
                "with_original_language": "hi",  # Hindi
                "sort_by": "popularity.desc",
                "page": page,
                "vote_count.gte": 10  # At least 10 votes for quality
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                for movie in results:
                    if len(movies) >= total_movies:
                        break
                    movies.append(movie)
                
                print(f"  Page {page} - Got {len(movies)} movies so far...")
                page += 1
                time.sleep(0.25)  # Rate limiting
            else:
                print(f"  Error on page {page}: {response.status_code}")
                break
                
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(1)
            continue
    
    print(f"[OK] Fetched {len(movies)} Bollywood movies!")
    return movies

def get_movie_details(movie_id):
    """Get detailed info for a movie"""
    try:
        url = f"{BASE_URL}/movie/{movie_id}"
        params = {
            "api_key": API_KEY,
            "append_to_response": "credits,keywords"
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def process_movie(movie):
    """Process movie into dataset format"""
    details = get_movie_details(movie['id'])
    
    # Extract genres from details (more reliable than genre_ids)
    genres = []
    if details and 'genres' in details:
        genres = [g['name'] for g in details['genres']]
    
    # Extract cast
    cast = []
    crew = []
    if details and 'credits' in details:
        cast = [c['name'] for c in details['credits'].get('cast', [])[:5]]
        crew = [c['name'] for c in details['credits'].get('crew', []) if c.get('job') == 'Director']
    
    # Extract keywords
    keywords = []
    if details and 'keywords' in details:
        keywords = [k['name'] for k in details['keywords'].get('keywords', [])[:10]]
    
    return {
        'movie_id': movie['id'],
        'title': movie.get('title', 'Unknown'),
        'overview': movie.get('overview', ''),
        'genres_list': genres,
        'keywords_list': keywords,
        'cast_list': cast,
        'crew_list': crew,
        'vote_average': movie.get('vote_average', 0),
        'vote_count': movie.get('vote_count', 0),
        'popularity': movie.get('popularity', 0),
        'release_date': movie.get('release_date', ''),
        'adult': movie.get('adult', False),
        'original_language': 'hi',
        'runtime': details.get('runtime', 0) if details else 0,
        'budget': details.get('budget', 0) if details else 0,
        'revenue': details.get('revenue', 0) if details else 0,
        'tagline': details.get('tagline', '') if details else '',
        'status': details.get('status', 'Released') if details else 'Released',
        'production_str': ', '.join([p['name'] for p in (details.get('production_companies', [])[:3] if details else [])])
    }

def main():
    print("=" * 50)
    print("BOLLYWOOD MOVIES FETCHER")
    print("=" * 50)
    
    # Step 1: Load existing dataset
    print("\n[*] Loading existing Hollywood dataset...")
    try:
        with open('movie_list.pkl', 'rb') as f:
            existing_data = pickle.load(f)
        existing_df = pd.DataFrame(existing_data)
        print(f"  Found {len(existing_df)} existing movies")
        existing_ids = set(existing_df['movie_id'].values)
    except Exception as e:
        print(f"  Error loading existing data: {e}")
        existing_df = pd.DataFrame()
        existing_ids = set()
    
    # Step 2: Fetch Bollywood movies
    bollywood_movies = fetch_bollywood_movies(5000)
    
    # Step 3: Filter out duplicates
    new_movies = [m for m in bollywood_movies if m['id'] not in existing_ids]
    print(f"\n[*] {len(new_movies)} new movies (after removing duplicates)")
    
    # Step 4: Process movies with details
    print("\n[*] Processing movie details (this takes a while)...")
    processed = []
    total = len(new_movies)
    
    for i, movie in enumerate(new_movies):
        result = process_movie(movie)
        if result:
            processed.append(result)
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{total} movies...")
    
    print(f"  Processed {len(processed)} movies total")
    
    # Step 5: Merge with existing
    if processed:
        new_df = pd.DataFrame(processed)
        
        # Ensure column compatibility
        for col in existing_df.columns:
            if col not in new_df.columns:
                new_df[col] = None
        
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Step 6: Save
        print(f"\n[*] Saving combined dataset ({len(combined_df)} total movies)...")
        combined_dict = combined_df.to_dict('list')
        
        with open('movie_list.pkl', 'wb') as f:
            pickle.dump(combined_dict, f)
        
        print("\n" + "=" * 50)
        print(f"[SUCCESS] Dataset now has {len(combined_df)} movies")
        print(f"   - Hollywood: {len(existing_df)}")
        print(f"   - Bollywood: {len(new_df)}")
        print("=" * 50)
        print("\n[!] Restart your Streamlit app to see Bollywood movies!")
    else:
        print("[ERROR] No new movies to add")

if __name__ == "__main__":
    main()
