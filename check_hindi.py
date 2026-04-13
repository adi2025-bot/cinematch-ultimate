import pickle
import pandas as pd

try:
    movies_dict = pickle.load(open('movie_list.pkl','rb'))
    movies = pd.DataFrame(movies_dict)
    
    # Check for original_language column or similar
    # The columns printed earlier were: ['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'vote_average', 'vote_count', 'popularity', 'release_date', 'runtime', 'budget', 'revenue', 'status', 'production_companies', 'tagline', 'genres_list', 'keywords_list', 'top_cast', 'director', 'tags']
    # 'original_language' was NOT in the list I saw earlier. Let me check 'overview' or 'title' for clues, or maybe it was just hidden.
    
    # Actually, let's check if I can find 'Hindi' in keywords or overview
    hindi_count = 0
    for index, row in movies.iterrows():
        if 'india' in str(row).lower() or 'hindi' in str(row).lower() or 'bollywood' in str(row).lower():
            hindi_count += 1
            if hindi_count < 5:
                print(f"Found potential Bollywood movie: {row['title']}")
                
    print(f"Total potential Hindi/Bollywood matches: {hindi_count}")

except Exception as e:
    print(e)
