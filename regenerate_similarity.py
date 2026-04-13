"""
Regenerate similarity matrix for all movies (Hollywood + Bollywood)
This creates the cosine similarity matrix used for movie recommendations
"""
import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import gzip
import os

print("=" * 50)
print("SIMILARITY MATRIX GENERATOR")
print("=" * 50)

# Load movie data
print("\n[1/5] Loading movie data...")
if not os.path.exists('movie_list.pkl'):
    print("ERROR: movie_list.pkl not found!")
    exit(1)

movies_dict = pickle.load(open('movie_list.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
print(f"   Loaded {len(movies)} movies")

# Prepare tags column
print("\n[2/5] Preparing tags for each movie...")
def create_tags(row):
    """Combine genres, keywords, cast, and overview into tags"""
    tags = []
    
    # Add genres
    if 'genres_list' in row and isinstance(row['genres_list'], list):
        tags.extend([g.replace(' ', '') for g in row['genres_list']])
    
    # Add keywords
    if 'keywords' in row and isinstance(row['keywords'], list):
        tags.extend([k.replace(' ', '') for k in row['keywords'][:5]])
    
    # Add cast
    if 'cast' in row and isinstance(row['cast'], list):
        tags.extend([c.replace(' ', '') for c in row['cast'][:3]])
    
    # Add director
    if 'director' in row and row['director']:
        tags.append(str(row['director']).replace(' ', ''))
    
    # Add overview words
    if 'overview' in row and row['overview']:
        overview = str(row['overview'])
        # Take first 100 words
        words = overview.split()[:100]
        tags.extend(words)
    
    return ' '.join(tags).lower()

movies['tags'] = movies.apply(create_tags, axis=1)
print(f"   Created tags for {len(movies)} movies")

print("\n[3/5] Vectorizing tags with TF-IDF (this may take a minute)...")
tfidf = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2), sublinear_tf=True)
vectors = tfidf.fit_transform(movies['tags'].fillna(''))
print(f"   Created {vectors.shape[0]} x {vectors.shape[1]} TF-IDF vector matrix")

# Calculate similarity
print("\n[4/5] Calculating cosine similarity (this takes a few minutes)...")
print("   Please wait...")
similarity = cosine_similarity(vectors)
print(f"   Created {similarity.shape[0]} x {similarity.shape[1]} similarity matrix")

# Save compressed
print("\n[5/5] Saving compressed similarity matrix...")
with gzip.open('similarity.pkl.gz', 'wb') as f:
    pickle.dump(similarity, f)

# Get file size
size_mb = os.path.getsize('similarity.pkl.gz') / (1024 * 1024)
print(f"   Saved as similarity.pkl.gz ({size_mb:.1f} MB)")

print("\n" + "=" * 50)
print("SUCCESS! Similarity matrix regenerated!")
print(f"Total movies: {len(movies)}")
print(f"Matrix size: {similarity.shape}")
print("=" * 50)
print("\nNow commit and push to GitHub to update Streamlit Cloud.")
