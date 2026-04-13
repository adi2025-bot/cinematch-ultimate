import pandas as pd
import pickle
import gzip

def optimize():
    print("Loading original data...")
    movies_dict = pickle.load(open('movie_list.pkl','rb'))
    movies = pd.DataFrame(movies_dict)
    
    # Load similarity (try compressed first, then raw)
    try:
        with gzip.open('similarity.pkl.gz', 'rb') as f:
            similarity = pickle.load(f)
    except:
        similarity = pickle.load(open('similarity.pkl','rb'))

    print("Optimizing Similarity Matrix...")
    # Pre-compute top 10 recommendations for every movie
    # Structure: { 'Movie Title': [index1, index2, index3, ...] }
    # Storing indices is smaller than storing titles strings again
    
    # Reset index to ensure it matches the similarity matrix (0 to N-1)
    movies = movies.reset_index(drop=True)
    
    recommendations = {}
    
    # Use positional index 'i' to access similarity matrix
    for i, row in movies.iterrows():
        title = row['title']
        try:
            distances = similarity[i]
        except IndexError:
            continue # Skip if mismatch
            
        # Get top 10 similar movies (excluding itself)
        # enumerate -> (index, score)
        m_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:11]
        # Store only the indices
        recommendations[title] = [x[0] for x in m_list]
        
    print(f"Generated recommendations for {len(recommendations)} movies.")
    
    print("Saving 'similarity_optimized.pkl'...")
    pickle.dump(recommendations, open('similarity_optimized.pkl', 'wb'))
    
    print("Optimizing Movie List...")
    # Drop columns not needed for UI
    # Keep: movie_id, title, overview, genres_list, keywords_list(maybe?), cast, crew, release_date, vote_average, etc.
    # Drop: tags, vectors, etc.
    
    cols_to_drop = ['tags', 'keywords', 'cast', 'crew'] # 'cast' and 'crew' might be the raw string versions if 'top_cast' and 'director' exist
    
    # Check what we have
    existing_cols = movies.columns.tolist()
    final_drop = [c for c in cols_to_drop if c in existing_cols]
    
    movies_small = movies.drop(columns=final_drop)
    
    print(f"Dropped columns: {final_drop}")
    print("Saving 'movie_list_optimized.pkl'...")
    pickle.dump(movies_small.to_dict(), open('movie_list_optimized.pkl', 'wb'))
    
    print("Done! Check the file sizes of *_optimized.pkl")

if __name__ == "__main__":
    optimize()
