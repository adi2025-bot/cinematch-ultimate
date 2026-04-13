import pickle
import pandas as pd

try:
    movies_dict = pickle.load(open('movie_list.pkl','rb'))
    movies = pd.DataFrame(movies_dict)
    print("Columns:", movies.columns.tolist())
    if 'adult' in movies.columns:
        print("Adult column exists. Unique values:", movies['adult'].unique())
    else:
        print("Adult column NOT found.")
        
    if 'genres_list' in movies.columns:
         print("Sample genres:", movies['genres_list'].head())
except Exception as e:
    print(e)
