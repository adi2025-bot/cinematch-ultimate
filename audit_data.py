import pickle
import pandas as pd
import numpy as np
import ast

def load_data_v2():
    try:
        movies_dict = pickle.load(open('movie_list.pkl','rb'))
        movies = pd.DataFrame(movies_dict)
        
        # --- DATA CLEANING & OPTIMIZATION ---
        # Fix '0' values for better performance and accuracy
        if 'release_date' in movies.columns:
            movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
            movies['year'] = movies['release_date'].dt.year.astype('Int64')
        else:
            movies['year'] = np.nan
        
        # Replace 0s with NaN in numeric columns to avoid skewing data/UI
        cols_to_clean = ['budget', 'revenue', 'runtime', 'vote_average', 'vote_count']
        for col in cols_to_clean:
            if col in movies.columns:
                movies[col] = movies[col].replace(0, np.nan)
                movies[col] = movies[col].replace(0.0, np.nan)
        
        return movies
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def check_data():
    movies = load_data_v2()
    if movies is None:
        return

    print(f"Loaded {len(movies)} movies.")
    
    # Check for 0s
    cols_to_check = ['budget', 'revenue', 'runtime', 'vote_average', 'vote_count']
    for col in cols_to_check:
        if col in movies.columns:
            zeros = movies[movies[col] == 0].shape[0]
            print(f"Column '{col}' has {zeros} zeros.")
            
            # Check for 0.0 float
            zeros_float = movies[movies[col] == 0.0].shape[0]
            if zeros_float > 0 and zeros_float != zeros:
                 print(f"Column '{col}' has {zeros_float} 0.0 values.")

    # Check for missing years
    missing_years = movies['year'].isna().sum()
    print(f"Movies with missing year: {missing_years}")

    # Check for potential crashers in process_movie_for_ui logic
    print("\nChecking for potential processing errors...")
    for idx, row in movies.iterrows():
        try:
            # Simulate logic from process_movie_for_ui
            rating_val = int(row.vote_average * 10) if pd.notna(row.vote_average) and row.vote_average > 0 else "NR"
            year_val = str(row.year) if pd.notna(row.year) else "N/A"
            
            # Runtime
            if 'runtime' in row:
                val = row.runtime
                fmt_run = f"{int(val//60)}h {int(val%60)}m" if pd.notna(val) and val > 0 else "N/A"
            
            # Budget/Revenue
            if 'budget' in row:
                val = row.budget
                fmt_bud = "${:,.0f}".format(val) if pd.notna(val) and val > 0 else "N/A"
                
        except Exception as e:
            print(f"Error processing row {idx} ({row.get('title', 'Unknown')}): {e}")

if __name__ == "__main__":
    check_data()
