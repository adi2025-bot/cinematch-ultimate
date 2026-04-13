"""
CineMatch ML Model Trainer
============================
One-time script to train all machine learning models.

Run this once: python train_models.py

This will generate:
  - sentiment_model.pkl       (Naive Bayes sentiment classifier)
  - sentiment_vectorizer.pkl  (TF-IDF vectorizer for sentiment)
  - rating_predictor.pkl      (Random Forest rating model)
  - rating_features.pkl       (Feature name mappings)
"""

import time
import sys
import io

# Fix Windows encoding issues with emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from ml_models import train_sentiment_model, train_rating_predictor

def main():
    print("=" * 60)
    print("  CineMatch ML Model Training Pipeline")
    print("=" * 60)
    start_time = time.time()
    
    # Step 1: Train Sentiment Analysis Model
    print("\n" + "-" * 60)
    print("STEP 1: Sentiment Analysis (Multinomial Naive Bayes)")
    print("-" * 60)
    accuracy, _, _ = train_sentiment_model()
    if accuracy:
        print(f"[OK] Sentiment model trained successfully! (Accuracy: {accuracy * 100:.1f}%)")
    else:
        print("[FAIL] Sentiment model training failed!")
    
    # Step 2: Train Rating Predictor
    print("\n" + "-" * 60)
    print("STEP 2: Rating Predictor (Random Forest Regressor)")
    print("-" * 60)
    rmse, importance, _ = train_rating_predictor()
    if rmse is not None:
        print(f"[OK] Rating predictor trained successfully! (RMSE: {rmse:.2f})")
    else:
        print("[FAIL] Rating predictor training failed!")
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print(f"  ALL MODELS TRAINED IN {elapsed:.1f} SECONDS")
    print("=" * 60)
    print("\nGenerated files:")
    print("  -> sentiment_model.pkl")
    print("  -> sentiment_vectorizer.pkl")
    print("  -> rating_predictor.pkl")
    print("  -> rating_features.pkl")
    print("\nYou can now run: streamlit run app.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
