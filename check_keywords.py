import pickle
import pandas as pd
import ast

try:
    movies_dict = pickle.load(open('movie_list.pkl','rb'))
    movies = pd.DataFrame(movies_dict)
    
    keywords = ['erotic', 'sex', 'nudity', 'adult', 'sexual', 'romance']
    
    count = 0
    for index, row in movies.iterrows():
        k_list = row['keywords_list'] if 'keywords_list' in row else []
        # If string, parse it
        if isinstance(k_list, str):
            try: k_list = ast.literal_eval(k_list)
            except: k_list = []
            
        if any(k in str(k_list).lower() for k in keywords):
            print(f"Match: {row['title']} - {k_list}")
            count += 1
            if count > 10: break
            
    print(f"Found matches for keywords: {keywords}")

except Exception as e:
    print(e)
