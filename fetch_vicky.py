import pickle
import requests
import pandas as pd
import time
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "e9324b946a1cfdd8f612f18690be72d7"
BASE_URL = "https://api.themoviedb.org/3"

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount("https://", adapter)
session.mount("http://", adapter)
session.verify = False


print("Loading existing dataset...")
movies_dict = pickle.load(open('movie_list.pkl', 'rb'))
existing_df = pd.DataFrame(movies_dict)
existing_ids = set(existing_df['movie_id'].values)
print(f"Existing: {len(existing_df)} movies")

def get_movie_details(movie_id):
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
    details = get_movie_details(movie['id'])
    genres = [g['name'] for g in details.get('genres', [])] if details else []
    cast = [c['name'] for c in details.get('credits', {}).get('cast', [])[:5]] if details else []
    director = [c['name'] for c in details.get('credits', {}).get('crew', []) if c.get('job') == 'Director'] if details else []
    keywords = [k['name'] for k in details.get('keywords', {}).get('keywords', [])[:10]] if details else []
    
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
        'original_language': movie.get('original_language', 'hi'),
    }

# 1. Search for Vicky Kaushal
actor_name = "Vicky Kaushal"
print(f"Searching for actor: {actor_name}...")
r = session.get(f"{BASE_URL}/search/person", params={"api_key": API_KEY, "query": actor_name})
actor_data = r.json()
if not actor_data.get('results'):
    print(f"Actor {actor_name} not found!")
    exit()

actor_id = actor_data['results'][0]['id']
print(f"Found Vicky Kaushal! ID: {actor_id}")

# 2. Get movie credits for Vicky Kaushal
r = session.get(f"{BASE_URL}/person/{actor_id}/movie_credits", params={"api_key": API_KEY})
credits_data = r.json()
movies = credits_data.get('cast', [])

new_movies = []
for m in movies:
    if m['id'] not in existing_ids:
        new_movies.append(m)

print(f"Total movies found: {len(movies)}")
print(f"New movies to add: {len(new_movies)}")

if not new_movies:
    print("All Vicky Kaushal movies are already in your dataset!")
else:
    processed = []
    for i, m in enumerate(new_movies):
        try:
            res = process_movie(m)
            if res:
                processed.append(res)
            print(f"Processed {i+1}/{len(new_movies)}: {m.get('title')}")
        except Exception as e:
            print(f"Error processing {m.get('title')}: {e}")
        time.sleep(0.3)
        
    new_df = pd.DataFrame(processed)
    for col in existing_df.columns:
        if col not in new_df.columns:
            new_df[col] = None
    for col in new_df.columns:
        if col not in existing_df.columns:
            existing_df[col] = None
            
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset='movie_id', keep='first')
    
    combined_dict = combined_df.to_dict('list')
    with open('movie_list.pkl', 'wb') as f:
        pickle.dump(combined_dict, f)
    
    print(f"Successfully added {len(processed)} Vicky Kaushal movies!")
