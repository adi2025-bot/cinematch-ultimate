import pandas as pd
import pickle

try:
    movies_dict = pickle.load(open('movie_list.pkl','rb'))
    movies = pd.DataFrame(movies_dict)
    print("Columns:", movies.columns.tolist())
    print("\nMemory Usage (MB):")
    print(movies.memory_usage(deep=True) / 1024 / 1024)
    print("\nTotal Size:", movies.memory_usage(deep=True).sum() / 1024 / 1024, "MB")
    
    if 'tags' in movies.columns:
        print("\n'tags' column sample:", movies['tags'].iloc[0])
except Exception as e:
    print(e)
