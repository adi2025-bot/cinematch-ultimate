# Deploy to Hugging Face Spaces

## Step 1: Create Hugging Face Account
1. Go to https://huggingface.co/join
2. Sign up (free)
3. Verify email

## Step 2: Create New Space
1. Go to https://huggingface.co/new-space
2. Fill in:
   - Space name: `cinematch` (or any name)
   - License: MIT
   - SDK: **Streamlit**
   - Hardware: CPU basic (FREE)
3. Click "Create Space"

## Step 3: Upload Files
Upload these files to your Space:
- `app.py`
- `requirements.txt`
- `README.md`
- `movie_list.pkl`
- `similarity.pkl.gz`
- `users.csv`
- `watchlist.csv`
- `feedback.csv`
- `reviews.csv`

### Upload Methods:
**Option A: Web Upload**
- Click "Files" tab in your Space
- Drag and drop files

**Option B: Git (Recommended for large files)**
```bash
git lfs install
git clone https://huggingface.co/spaces/YOUR_USERNAME/cinematch
# Copy all project files to cloned folder
git add .
git commit -m "Initial upload"
git push
```

## Step 4: Wait for Build
- HF will automatically build and deploy
- Takes 2-5 minutes
- Your app will be live at: `https://YOUR_USERNAME-cinematch.hf.space`

## Files to Upload:
| File | Size | Required |
|------|------|----------|
| app.py | ~85KB | Yes |
| requirements.txt | ~100B | Yes |
| README.md | ~500B | Yes |
| movie_list.pkl | ~44MB | Yes |
| similarity.pkl.gz | ~50MB | Yes (for recommendations) |
| users.csv | ~1KB | Yes |
| watchlist.csv | ~1KB | Yes |
| feedback.csv | ~1KB | Yes |
| reviews.csv | ~1KB | Yes |

## Troubleshooting:
- If build fails, check "Logs" tab
- Make sure requirements.txt has all packages
- Large files need Git LFS
