import pickle
import pandas as pd
import requests
import os
from concurrent.futures import ThreadPoolExecutor

API_KEY = "e9324b946a1cfdd8f612f18690be72d7"
BASE_URL = "https://api.themoviedb.org/3"
session = requests.Session()

def is_adult(movie_id):
    try:
        r = session.get(f"{BASE_URL}/movie/{movie_id}/release_dates?api_key={API_KEY}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            if 'results' in data:
                # Check India first
                in_cert = next((i for i in data['results'] if i['iso_3166_1'] == 'IN'), None)
                if in_cert:
                    certs = [c.get('certification', '') for c in in_cert['release_dates']]
                    if any(c in ['A', '18'] for c in certs):
                        return True
                # Check US next
                us_cert = next((i for i in data['results'] if i['iso_3166_1'] == 'US'), None)
                if us_cert:
                    certs = [c.get('certification', '') for c in us_cert['release_dates']]
                    if any(c in ['NC-17', 'R'] for c in certs):
                        return True
        return False
    except:
        return False

files_to_update = ['movie_list_optimized.pkl', 'movie_list.pkl']

for file in files_to_update:
    if not os.path.exists(file):
        continue
    
    print(f"Updating {file}...")
    movies_dict = pickle.load(open(file, 'rb'))
    df = pd.DataFrame(movies_dict)
    
    if 'movie_id' not in df.columns and 'id' in df.columns:
        df.rename(columns={'id': 'movie_id'}, inplace=True)
    
    if 'adult' not in df.columns:
        df['adult'] = False
        
    # Find movies that need checking (we can just check all, or check ones where adult is False)
    # We will check all movies because some might actually be adult.
    movie_ids = df['movie_id'].unique()
    
    print(f"Found {len(movie_ids)} unique movies. Fetching certifications...")
    
    updated_count = 0
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(lambda mid: (mid, is_adult(mid)), movie_ids))
        
    for mid, adult_status in results:
        if adult_status:
            # Update dataframe
            df.loc[df['movie_id'] == mid, 'adult'] = True
            updated_count += 1
            
    print(f"Found {updated_count} Adult/A-rated movies in {file}")
    
    # Save back
    new_dict = df.to_dict('list')
    with open(file, 'wb') as f:
        pickle.dump(new_dict, f)
        
    print(f"Saved {file}")

print("Done tagging adult movies!")
