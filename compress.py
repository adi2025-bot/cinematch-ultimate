import pickle
import gzip

print("Loading similarity.pkl... (This might take a moment)")
# Load your original big file
with open('similarity.pkl', 'rb') as f:
    data = pickle.load(f)

print("Compressing to similarity.pkl.gz...")
# Save it as a compressed file
with gzip.open('similarity.pkl.gz', 'wb') as f:
    pickle.dump(data, f)

print("Success! You can now upload 'similarity.pkl.gz' to GitHub.")