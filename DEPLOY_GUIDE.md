# 🎬 CineMatch Deployment Guide

## 📦 Files to Upload:
| File | Size | Status |
|------|------|--------|
| `app.py` | 67KB | ✅ Required |
| `movie_list.pkl` | ~44MB | ✅ Under limit |
| `similarity.pkl.gz` | ~50MB | ✅ Under limit |
| `requirements.txt` | 62B | ✅ Required |
| `users.csv`, `watchlist.csv`, etc. | Small | ✅ Required |

## ⚠️ STEP 0: Install Git First!

---

## STEP 2: Go to your project folder

👉 Copy-paste this and press Enter:
```
cd "C:\Users\91961\Desktop\movie project"
```

---

## STEP 3: Delete old git folder (if any)

👉 Copy-paste this:
```
rmdir /s /q .git
```
(If it says "cannot find", that's OK, continue)

---

## STEP 4: Initialize Git

👉 Copy-paste:
```
git init
```

---

## STEP 5: Set your name and email

👉 Copy-paste (change YOUR_NAME and YOUR_EMAIL):
```
git config user.name "YOUR_NAME"
git config user.email "your_email@gmail.com"
```

---

## STEP 6: Add ONLY the required files

👉 Copy-paste this EXACTLY (one command):
```
git add app.py requirements.txt users.csv watchlist.csv feedback.csv reviews.csv ml_models.py *.pkl
```

---

## STEP 7: Add the BIG files separately

👉 Copy-paste:
```
git add movie_list.pkl
```

👉 Then copy-paste:
```
git add similarity.pkl.gz
```

---

## STEP 8: Commit

👉 Copy-paste:
```
git commit -m "CineMatch Movie App"
```

---

## STEP 9: Connect to GitHub

👉 First, CREATE a new repository on GitHub:
   1. Go to https://github.com
   2. Click + (top right) → New repository
   3. Name: cinematch
   4. Make it PUBLIC
   5. Click Create repository

👉 Then copy-paste (CHANGE your_username!):
```
git branch -M main
git remote add origin https://github.com/your_username/cinematch.git
```

---

## STEP 10: PUSH (Upload)

👉 Copy-paste:
```
git push -u origin main
```

👉 A browser window will open - **Sign in to GitHub**
👉 Wait 5-10 minutes for upload to complete...

✅ **DONE!**

---

## STEP 11: Deploy on Streamlit

👉 Go to: https://share.streamlit.io
� Sign in with GitHub
👉 Click New App
👉 Select your repository → Deploy!

---

## 🆘 IF ERROR:

### "remote origin already exists"
👉 Run this first, then try Step 9 again:
```
git remote remove origin
```

### "Authentication failed"
👉 Run this:
```
git config --global credential.helper manager
```
Then try git push again.

---

🎉 You got this!
