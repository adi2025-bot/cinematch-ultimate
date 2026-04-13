import pandas as pd
import numpy as np
import ast
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. LOAD DATA
print("⏳ Loading Data...")
try:
    movies = pd.read_csv('tmdb_5000_movies.csv')
    credits = pd.read_csv('tmdb_5000_credits.csv')
except FileNotFoundError:
    print("❌ Error: CSV files not found. Please download them from Kaggle.")
    exit()

# 2. MERGE DATASETS
print("🛠️ Merging Files...")
movies = movies.merge(credits, on='title')

# 3. SELECT COLUMNS (Added 'popularity'!)
movies = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 
                 'vote_average', 'vote_count', 'popularity', 'release_date', 'runtime', 
                 'budget', 'revenue', 'status', 'production_companies', 'tagline']]

# Fix missing values safely
movies['overview'] = movies['overview'].fillna('')
movies['tagline'] = movies['tagline'].fillna('')
movies.dropna(subset=['release_date'], inplace=True)

# --- HELPER FUNCTIONS ---
def convert(text):
    L = []
    try:
        for i in ast.literal_eval(text):
            L.append(i['name'])
    except: pass
    return L

def fetch_director(text):
    L = []
    try:
        for i in ast.literal_eval(text):
            if i['job'] == 'Director':
                L.append(i['name'])
                break
    except: pass
    return L

def fetch_top_cast(text):
    L = []
    try:
        counter = 0
        for i in ast.literal_eval(text):
            if counter < 6:
                L.append(i['name'])
                counter+=1
            else: break
    except: pass
    return L

def collapse(L):
    L1 = []
    for i in L:
        L1.append(i.replace(" ",""))
    return L1

# 4. DATA PROCESSING
print("⚙️ Processing Features...")
movies['genres_list'] = movies['genres'].apply(convert)
movies['keywords_list'] = movies['keywords'].apply(convert)
movies['top_cast'] = movies['cast'].apply(fetch_top_cast)
movies['director'] = movies['crew'].apply(fetch_director)

# 5. INTELLIGENT TAGGING
movies['genres_ai'] = movies['genres_list'].apply(collapse)
movies['keywords_ai'] = movies['keywords_list'].apply(collapse)
movies['cast_ai'] = movies['top_cast'].apply(collapse)
movies['director_ai'] = movies['director'].apply(collapse)
movies['overview_ai'] = movies['overview'].apply(lambda x: x.split())

movies['tags'] = movies['overview_ai'] + \
                 (movies['genres_ai'] * 2) + \
                 movies['keywords_ai'] + \
                 (movies['cast_ai'] * 2) + \
                 (movies['director_ai'] * 3)

new_df = movies.drop(columns=['overview_ai','genres_ai','keywords_ai','cast_ai','director_ai'])
new_df['tags'] = new_df['tags'].apply(lambda x: " ".join(x))
new_df['tags'] = new_df['tags'].apply(lambda x: x.lower())

# 6. VECTORIZATION
print("🧠 Training Model...")
cv = CountVectorizer(max_features=5000, stop_words='english')
vectors = cv.fit_transform(new_df['tags']).toarray()

# 7. SIMILARITY MATRIX
print("📐 Calculating Similarity...")
similarity = cosine_similarity(vectors)

# 8. SAVE FILES
print("💾 Saving Database...")
pickle.dump(new_df.to_dict(), open('movie_list.pkl', 'wb'))
pickle.dump(similarity, open('similarity.pkl', 'wb'))

print("✅ SUCCESS! The Project Brain is updated.")