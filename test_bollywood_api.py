import requests
import pandas as pd

API_KEY = "e9324b946a1cfdd8f612f18690be72d7"

def fetch_bollywood_movies():
    try:
        url = f"https://api.themoviedb.org/3/discover/movie?api_key={API_KEY}&language=en-US&sort_by=popularity.desc&with_original_language=hi&page=1"
        print(f"Fetching URL: {url}")
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if 'results' in data:
            print(f"Found {len(data['results'])} results.")
            for m in data['results'][:3]:
                print(f" - {m['title']} ({m.get('release_date')})")
        else:
            print("No 'results' key in response.")
            print(data)
            
    except Exception as e:
        print(f"Error: {e}")

fetch_bollywood_movies()
