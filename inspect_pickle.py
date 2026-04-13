import pickle
import pandas as pd

try:
    data = pickle.load(open('movie_list.pkl', 'rb'))
    print(f"Type: {type(data)}")
    if isinstance(data, pd.DataFrame):
        print(f"Columns: {data.columns}")
        print(data.head())
    elif isinstance(data, dict):
        print(f"Keys: {data.keys()}")
        # Check if it can be converted to DataFrame
        try:
            df = pd.DataFrame(data)
            print("Successfully converted dict to DataFrame.")
            print(df.head())
        except Exception as e:
            print(f"Could not convert to DataFrame: {e}")
    else:
        print(f"Content: {data}")
except Exception as e:
    print(f"Error loading pickle: {e}")
