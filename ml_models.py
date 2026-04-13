"""
CineMatch ML Models Module
===========================
Contains machine learning models for:
1. Sentiment Analysis (Multinomial Naive Bayes with TF-IDF)
2. Movie Rating Prediction (Random Forest Regressor)

These models replace basic keyword matching with real ML intelligence.
"""

import pickle
import os
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error


# ==========================================
# PATHS FOR SAVED MODELS
# ==========================================
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
SENTIMENT_MODEL_PATH = os.path.join(MODEL_DIR, 'sentiment_model.pkl')
SENTIMENT_VECTORIZER_PATH = os.path.join(MODEL_DIR, 'sentiment_vectorizer.pkl')
RATING_MODEL_PATH = os.path.join(MODEL_DIR, 'rating_predictor.pkl')
RATING_FEATURES_PATH = os.path.join(MODEL_DIR, 'rating_features.pkl')


# ==========================================
# 1. SENTIMENT ANALYSIS MODEL
# ==========================================
def _get_training_data():
    """
    Generate labeled movie review training data.
    Uses a curated dataset of positive and negative movie reviews
    to train the Naive Bayes classifier.
    """
    positive_reviews = [
        "This movie was absolutely amazing, I loved every minute of it",
        "Brilliant performance by the lead actor, truly outstanding cinema",
        "One of the best films I have ever watched, a masterpiece",
        "The storyline was captivating and the direction was superb",
        "A beautiful film with stunning visuals and great acting",
        "I was thoroughly entertained from start to finish",
        "This is a must watch movie, highly recommend to everyone",
        "The screenplay was excellent and the music was phenomenal",
        "A perfect blend of action and emotion, loved it",
        "Great movie with an incredible plot twist at the end",
        "The cinematography was breathtaking and the score was perfect",
        "Wonderful performances by the entire cast, truly memorable",
        "This film exceeded all my expectations, absolutely fantastic",
        "A heartwarming story told with great skill and passion",
        "The best movie of the year without any doubt",
        "Incredibly well made film with superb direction",
        "The acting was top notch and the story was gripping",
        "A cinematic gem that deserves all the praise it gets",
        "Loved the character development and the emotional depth",
        "This movie is a triumph of storytelling and filmmaking",
        "Exceptional movie with brilliant performances all around",
        "The director has outdone himself with this masterwork",
        "A truly inspiring film that touches your heart",
        "Perfect casting and an amazing screenplay make this unforgettable",
        "I couldn't stop watching, it was that good and engaging",
        "Spectacular visual effects combined with a great story",
        "This movie deserves every award it can get",
        "Truly a work of art, beautifully crafted in every way",
        "An emotional rollercoaster that kept me fully invested",
        "The best sequel I have ever seen, even better than the original",
        "Hilarious comedy that had me laughing throughout the entire film",
        "A powerful movie that stays with you long after watching",
        "Stunning direction with incredible attention to detail",
        "The chemistry between the leads was absolutely electric",
        "Every scene was perfectly executed and emotionally resonant",
        "The movie had me on the edge of my seat the entire time",
        "A beautiful exploration of human nature and relationships",
        "The writing was sharp witty and full of clever moments",
        "Outstanding film that pushes the boundaries of cinema",
        "I was moved to tears by this powerful and beautiful story",
        "A rare gem in modern cinema absolutely worth watching",
        "The performances were deeply moving and authentic",
        "Brilliant direction paired with a compelling narrative",
        "This movie is proof that great storytelling never gets old",
        "An absolute delight from beginning to end truly wonderful",
        "The musical score elevated every scene to perfection",
        "A bold and daring film that takes creative risks and succeeds",
        "Phenomenal acting with a script that feels genuine and real",
        "The pacing was perfect keeping the audience engaged throughout",
        "A triumphant return to form for the director absolutely loved it",
    ]

    negative_reviews = [
        "This was the worst movie I have ever seen, complete waste of time",
        "Terrible acting and a boring plot that went nowhere",
        "I hated every minute of this awful film",
        "The movie was so bad I wanted to leave the theater",
        "Poorly written script with no character development at all",
        "A complete disaster from start to finish, very disappointing",
        "The acting was wooden and the story made no sense",
        "Worst movie of the year, do not waste your money on this",
        "The plot was predictable and the dialogues were cringe worthy",
        "I cannot believe how bad this movie turned out to be",
        "Boring and pointless, I fell asleep halfway through",
        "The special effects were cheap and the story was terrible",
        "A total letdown after all the hype, very disappointing",
        "This movie is an insult to cinema and its audience",
        "Awful performances and a ridiculous storyline",
        "The direction was lazy and the editing was choppy",
        "Waste of talented actors on such a poorly written script",
        "I regret watching this terrible excuse for a movie",
        "The movie dragged on forever with nothing interesting happening",
        "Poorly executed with no redeeming qualities whatsoever",
        "A colossal waste of time and money avoid at all costs",
        "The dialogue was painful to listen to absolutely dreadful",
        "Nothing about this movie worked it was a complete failure",
        "The plot holes were enormous and ruined the entire experience",
        "Dull lifeless and utterly forgettable in every possible way",
        "I found myself checking my phone because the movie was so boring",
        "A mindless cash grab with no artistic merit whatsoever",
        "The acting was atrocious and the script was even worse",
        "This movie made me angry with how bad it was",
        "An unoriginal mess that copies better films poorly",
        "The pacing was terrible making a two hour movie feel like four",
        "Every character was annoying and impossible to root for",
        "The ending was the worst part of an already horrible movie",
        "Lazy filmmaking at its absolute worst avoid this at all costs",
        "The movie tried too hard and failed at everything it attempted",
        "A complete and total waste of potential on a good concept",
        "Painfully unfunny despite being marketed as a comedy",
        "The CGI looked terrible and took me out of the experience",
        "No emotional depth whatsoever just empty spectacle",
        "This movie is the definition of style over substance",
        "A bloated mess that desperately needed better editing",
        "The villain was laughably bad with zero motivation",
        "Predictable from start to finish with zero surprises",
        "The worst thing about this movie is that it exists",
        "A soulless corporate product masquerading as entertainment",
        "The script felt like it was written in five minutes",
        "Absolutely nothing memorable about this forgettable movie",
        "The tonal shifts were jarring and the movie could not find its identity",
        "A franchise killer that should never have been made",
        "Everything about this movie screams laziness and indifference",
    ]

    texts = positive_reviews + negative_reviews
    labels = [1] * len(positive_reviews) + [0] * len(negative_reviews)
    return texts, labels


def train_sentiment_model():
    """
    Train a Multinomial Naive Bayes classifier for sentiment analysis.
    
    Uses TF-IDF vectorization to convert text into numerical features,
    then trains a Naive Bayes model on labeled movie review data.
    
    Returns:
        tuple: (accuracy, model, vectorizer)
    """
    print("Training Sentiment Analysis Model (Naive Bayes + TF-IDF)...")
    
    texts, labels = _get_training_data()
    
    # TF-IDF Vectorization - converts text to numerical features
    # max_features=5000: use top 5000 most important words
    # ngram_range=(1,2): consider single words AND word pairs
    # sublinear_tf=True: apply log normalization to term frequencies
    tfidf = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        stop_words='english'
    )
    
    X = tfidf.fit_transform(texts)
    y = np.array(labels)
    
    # Split data for training and testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train Multinomial Naive Bayes classifier
    # alpha=0.1: Laplace smoothing parameter
    model = MultinomialNB(alpha=0.1)
    model.fit(X_train, y_train)
    
    # Evaluate accuracy
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Save trained model and vectorizer
    with open(SENTIMENT_MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(SENTIMENT_VECTORIZER_PATH, 'wb') as f:
        pickle.dump(tfidf, f)
    
    print(f"   Sentiment Model trained! Accuracy: {accuracy * 100:.1f}%")
    print(f"   Model saved to: {SENTIMENT_MODEL_PATH}")
    print(f"   Vectorizer saved to: {SENTIMENT_VECTORIZER_PATH}")
    
    return accuracy, model, tfidf


def predict_sentiment(text):
    """
    Predict sentiment of a review text using the trained ML model.
    Falls back to basic analysis if model is not available.
    
    Args:
        text (str): The review text to analyze
    
    Returns:
        str: "Positive", "Negative", or "Neutral"
    """
    try:
        if os.path.exists(SENTIMENT_MODEL_PATH) and os.path.exists(SENTIMENT_VECTORIZER_PATH):
            with open(SENTIMENT_MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            with open(SENTIMENT_VECTORIZER_PATH, 'rb') as f:
                tfidf = pickle.load(f)
            
            # Transform text using the same TF-IDF vectorizer
            text_vector = tfidf.transform([text.lower()])
            
            # Get prediction probabilities
            proba = model.predict_proba(text_vector)[0]
            
            # Use confidence threshold for Neutral classification
            confidence = max(proba)
            prediction = model.predict(text_vector)[0]
            
            if confidence < 0.6:
                return "Neutral"
            return "Positive" if prediction == 1 else "Negative"
        else:
            # Fallback to basic sentiment if model not trained
            return _basic_sentiment(text)
    except Exception:
        return _basic_sentiment(text)


def _basic_sentiment(text):
    """Fallback basic sentiment analysis using keyword matching."""
    text = text.lower()
    pos = ['good', 'great', 'awesome', 'excellent', 'love', 'amazing', 'best', 'fantastic',
           'brilliant', 'wonderful', 'superb', 'outstanding', 'perfect', 'beautiful']
    neg = ['bad', 'worst', 'terrible', 'boring', 'awful', 'hate', 'poor', 'stupid',
           'horrible', 'dreadful', 'pathetic', 'disappointing', 'waste', 'garbage']
    score = sum([1 for w in pos if w in text]) - sum([1 for w in neg if w in text])
    return "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"


def get_sentiment_confidence(text):
    """
    Get detailed sentiment prediction with confidence scores.
    
    Returns:
        dict: {'sentiment': str, 'confidence': float, 'positive_prob': float, 'negative_prob': float}
    """
    try:
        if os.path.exists(SENTIMENT_MODEL_PATH) and os.path.exists(SENTIMENT_VECTORIZER_PATH):
            with open(SENTIMENT_MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            with open(SENTIMENT_VECTORIZER_PATH, 'rb') as f:
                tfidf = pickle.load(f)
            
            text_vector = tfidf.transform([text.lower()])
            proba = model.predict_proba(text_vector)[0]
            prediction = model.predict(text_vector)[0]
            
            confidence = max(proba)
            sentiment = "Neutral" if confidence < 0.6 else ("Positive" if prediction == 1 else "Negative")
            
            return {
                'sentiment': sentiment,
                'confidence': round(confidence * 100, 1),
                'positive_prob': round(proba[1] * 100, 1) if len(proba) > 1 else 0,
                'negative_prob': round(proba[0] * 100, 1)
            }
    except Exception:
        pass
    
    # Fallback
    sentiment = _basic_sentiment(text)
    return {'sentiment': sentiment, 'confidence': 50.0, 'positive_prob': 50.0, 'negative_prob': 50.0}


# ==========================================
# 2. MOVIE RATING PREDICTOR MODEL
# ==========================================
def train_rating_predictor(movies_df=None):
    """
    Train a Random Forest Regressor to predict movie ratings.
    
    Uses features extracted from the movie dataset:
    - budget (normalized)
    - runtime
    - genre_count (number of genres)
    - keyword_count (number of keywords)
    - cast_count (number of cast members)
    - vote_count (popularity indicator)
    
    Args:
        movies_df: DataFrame with movie data (loaded from movie_list.pkl if None)
    
    Returns:
        tuple: (rmse_score, feature_importance_dict, model)
    """
    print("\nTraining Rating Predictor (Random Forest Regressor)...")
    
    if movies_df is None:
        if os.path.exists(os.path.join(MODEL_DIR, 'movie_list.pkl')):
            movies_dict = pickle.load(open(os.path.join(MODEL_DIR, 'movie_list.pkl'), 'rb'))
            movies_df = pd.DataFrame(movies_dict)
        else:
            print("   ERROR: movie_list.pkl not found!")
            return None, None, None
    
    # Feature Engineering
    df = movies_df.copy()
    
    # Create numerical features
    df['genre_count'] = df['genres_list'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    df['keyword_count'] = df['keywords'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    df['cast_count'] = df['top_cast'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    df['budget_log'] = np.log1p(pd.to_numeric(df['budget'], errors='coerce').fillna(0))
    df['runtime_clean'] = pd.to_numeric(df['runtime'], errors='coerce').fillna(df['runtime'].median() if 'runtime' in df else 100)
    df['vote_count_log'] = np.log1p(pd.to_numeric(df['vote_count'], errors='coerce').fillna(0))
    df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0)
    
    # Filter out movies with no rating
    df = df[df['vote_average'] > 0].copy()
    
    feature_names = ['budget_log', 'runtime_clean', 'genre_count', 'keyword_count', 'cast_count', 'vote_count_log']
    
    X = df[feature_names].fillna(0)
    y = df['vote_average']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train Random Forest Regressor
    # n_estimators=100: use 100 decision trees
    # max_depth=10: limit tree depth to prevent overfitting
    # min_samples_split=5: minimum samples needed to split a node
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1  # Use all CPU cores
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # Feature importance
    importance = dict(zip(feature_names, model.feature_importances_))
    
    # Save model and feature info
    model_data = {
        'model': model,
        'feature_names': feature_names,
        'feature_importance': importance,
        'rmse': rmse
    }
    with open(RATING_MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    
    # Pretty names for display
    pretty_names = {
        'budget_log': 'Budget',
        'runtime_clean': 'Runtime',
        'genre_count': 'Genre Count',
        'keyword_count': 'Keyword Count',
        'cast_count': 'Cast Size',
        'vote_count_log': 'Popularity (Vote Count)'
    }
    
    with open(RATING_FEATURES_PATH, 'wb') as f:
        pickle.dump(pretty_names, f)
    
    print(f"   Rating Predictor trained! RMSE: {rmse:.2f}")
    print(f"   Feature Importance:")
    for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        print(f"      {pretty_names.get(feat, feat)}: {imp * 100:.1f}%")
    print(f"   Model saved to: {RATING_MODEL_PATH}")
    
    return rmse, importance, model


def predict_rating(movie_row):
    """
    Predict the rating for a movie using the trained Random Forest model.
    
    Args:
        movie_row: A pandas Series or dict representing a movie
    
    Returns:
        dict: {'predicted_rating': float, 'confidence': str} or None if model not available
    """
    try:
        if not os.path.exists(RATING_MODEL_PATH):
            return None
        
        with open(RATING_MODEL_PATH, 'rb') as f:
            model_data = pickle.load(f)
        
        model = model_data['model']
        feature_names = model_data['feature_names']
        
        # Extract features from movie row
        if isinstance(movie_row, dict):
            genres_list = movie_row.get('genres_list', [])
            keywords = movie_row.get('keywords', [])
            top_cast = movie_row.get('top_cast', [])
            budget = movie_row.get('budget', 0)
            runtime = movie_row.get('runtime', 100)
            vote_count = movie_row.get('vote_count', 0)
        else:
            genres_list = movie_row.genres_list if hasattr(movie_row, 'genres_list') and isinstance(movie_row.genres_list, list) else []
            keywords = movie_row.keywords if hasattr(movie_row, 'keywords') and isinstance(movie_row.keywords, list) else []
            top_cast = movie_row.top_cast if hasattr(movie_row, 'top_cast') and isinstance(movie_row.top_cast, list) else []
            budget = getattr(movie_row, 'budget', 0) or 0
            runtime = getattr(movie_row, 'runtime', 100) or 100
            vote_count = getattr(movie_row, 'vote_count', 0) or 0
        
        features = {
            'budget_log': np.log1p(float(budget)),
            'runtime_clean': float(runtime) if runtime else 100.0,
            'genre_count': len(genres_list),
            'keyword_count': len(keywords),
            'cast_count': len(top_cast),
            'vote_count_log': np.log1p(float(vote_count))
        }
        
        X = pd.DataFrame([features])[feature_names]
        predicted = model.predict(X)[0]
        
        # Clamp between 1 and 10
        predicted = max(1.0, min(10.0, predicted))
        
        return {
            'predicted_rating': round(predicted, 1),
            'confidence': 'High' if model_data.get('rmse', 2) < 1.5 else 'Medium'
        }
    except Exception:
        return None


def get_feature_importance():
    """
    Get feature importance from the trained rating predictor.
    
    Returns:
        dict: {feature_pretty_name: importance_percentage} or None
    """
    try:
        if not os.path.exists(RATING_MODEL_PATH) or not os.path.exists(RATING_FEATURES_PATH):
            return None
        
        with open(RATING_MODEL_PATH, 'rb') as f:
            model_data = pickle.load(f)
        with open(RATING_FEATURES_PATH, 'rb') as f:
            pretty_names = pickle.load(f)
        
        importance = model_data.get('feature_importance', {})
        
        return {pretty_names.get(k, k): round(v * 100, 1) for k, v in 
                sorted(importance.items(), key=lambda x: x[1], reverse=True)}
    except Exception:
        return None


def get_model_stats():
    """
    Get statistics about all trained models.
    
    Returns:
        dict with model information
    """
    stats = {
        'sentiment_model_exists': os.path.exists(SENTIMENT_MODEL_PATH),
        'rating_model_exists': os.path.exists(RATING_MODEL_PATH),
    }
    
    if stats['rating_model_exists']:
        try:
            with open(RATING_MODEL_PATH, 'rb') as f:
                model_data = pickle.load(f)
            stats['rating_rmse'] = round(model_data.get('rmse', 0), 2)
            stats['rating_features'] = model_data.get('feature_names', [])
        except Exception:
            pass
    
    return stats


# ==========================================
# Quick test when run directly
# ==========================================
if __name__ == "__main__":
    print("=" * 50)
    print("CineMatch ML Models - Quick Test")
    print("=" * 50)
    
    # Test sentiment
    test_reviews = [
        "This movie was absolutely amazing and wonderful!",
        "Terrible film, worst I've ever seen",
        "The movie was okay, nothing special",
    ]
    
    accuracy, model, tfidf = train_sentiment_model()
    print(f"\nSentiment Model Accuracy: {accuracy * 100:.1f}%\n")
    
    for review in test_reviews:
        result = get_sentiment_confidence(review)
        print(f"Review: \"{review}\"")
        print(f"  → {result['sentiment']} (Confidence: {result['confidence']}%)")
        print()
    
    # Test rating predictor
    rmse, importance, model = train_rating_predictor()
    if rmse:
        print(f"\nRating Predictor RMSE: {rmse:.2f}")
