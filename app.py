import streamlit as st
import pickle
import pandas as pd
import hashlib
import os
import requests
import time
import urllib.parse
import plotly.express as px
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from streamlit_lottie import st_lottie

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="CineMatch Ultimate", 
    page_icon="🍿",
    initial_sidebar_state="expanded"
)

# YOUR API KEY
API_KEY = "e9324b946a1cfdd8f612f18690be72d7" 

# --- INIT SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'view_mode' not in st.session_state: st.session_state.view_mode = 'grid'
if 'detail_movie' not in st.session_state: st.session_state.detail_movie = None
if 'selected_movie' not in st.session_state: st.session_state.selected_movie = None
if 'selected_director' not in st.session_state: st.session_state.selected_director = None
if 'selected_actor' not in st.session_state: st.session_state.selected_actor = None
if 'selected_genre' not in st.session_state: st.session_state.selected_genre = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ''
if 'role' not in st.session_state: st.session_state.role = 'user'
if 'search_type' not in st.session_state: st.session_state.search_type = 'movie'
if 'search_query' not in st.session_state: st.session_state.search_query = None
if 'show_splash' not in st.session_state: st.session_state.show_splash = False
# NEW: Enhanced features session state
if 'recently_viewed' not in st.session_state: st.session_state.recently_viewed = []
if 'compare_list' not in st.session_state: st.session_state.compare_list = []

# ==========================================
# 2. VISUAL STYLE (PREMIUM DARK LOOK)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
    
    /* JIOHOTSTAR DARK PREMIUM BACKGROUND */
    .stApp { 
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%); 
        color: #ffffff; 
    }
    
    #MainMenu, footer {visibility: hidden;} 
    div[data-testid="stVerticalBlock"] > div:first-child { padding-top: 0; }
    
    /* NAVBAR - JioHotstar Style */
    .nav-header {
        background: linear-gradient(90deg, rgba(15, 12, 41, 0.95) 0%, rgba(26, 26, 46, 0.95) 100%);
        backdrop-filter: blur(20px);
        padding: 20px 40px; 
        border-bottom: 1px solid rgba(138, 43, 226, 0.3);
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 30px rgba(138, 43, 226, 0.2);
    }
    .logo { 
        font-size: 32px; font-weight: 800; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 2px; text-transform: uppercase; 
    }
    .user-badge { font-weight: 600; color: #b8b8d1; }
    
    /* MOVIE CARD - JioHotstar Style */
    .movie-card {
        text-decoration: none; color: white; display: block;
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px; overflow: hidden;
        border: 1px solid rgba(138, 43, 226, 0.15); 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        height: 100%; cursor: pointer;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .movie-card:hover { 
        transform: translateY(-8px) scale(1.02); 
        border-color: #8b5cf6; 
        box-shadow: 0 20px 40px rgba(139, 92, 246, 0.3); 
    }
    .movie-card img { width: 100%; aspect-ratio: 2/3; object-fit: cover; display: block;}
    .card-content { padding: 15px; background: linear-gradient(to top, rgba(15, 12, 41, 0.95) 60%, transparent); }
    .card-title { font-size: 1rem; font-weight: 700; margin: 0 0 5px 0; line-height: 1.2; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .card-meta { font-size: 0.85rem; color: #a5b4fc; }
    
    /* RESPONSIVE MOVIE GRID */
    .movies-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 20px;
        padding: 10px 0;
    }
    @media (max-width: 1200px) {
        .movies-grid { grid-template-columns: repeat(4, 1fr); gap: 15px; }
    }
    @media (max-width: 900px) {
        .movies-grid { grid-template-columns: repeat(3, 1fr); gap: 12px; }
    }
    @media (max-width: 600px) {
        .movies-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .movie-card { margin-bottom: 0; border-radius: 12px; }
        .card-content { padding: 10px; }
        .card-title { font-size: 0.85rem; }
        .card-meta { font-size: 0.7rem; }
    }
    @media (max-width: 400px) {
        .movies-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .card-content { padding: 8px; }
        .card-title { font-size: 0.75rem; }
    }
    
    /* HERO SECTION - JioHotstar Style */
    .hero-container {
        position: relative; border-radius: 24px; overflow: hidden; 
        box-shadow: 0 25px 60px rgba(0,0,0,0.5); margin-bottom: 30px;
        background-size: cover; background-position: center; min-height: 500px;
        border: 1px solid rgba(138, 43, 226, 0.2);
    }
    .hero-overlay {
        background: linear-gradient(to right, rgba(15, 12, 41, 0.98) 30%, rgba(26, 26, 46, 0.85) 60%, rgba(22, 33, 62, 0.4));
        padding: 50px; display: flex; gap: 40px; align-items: center; height: 100%; min-height: 500px;
    }
    .hero-poster { 
        width: 280px; border-radius: 16px; 
        box-shadow: 0 15px 50px rgba(0,0,0,0.6); 
        border: 3px solid rgba(138, 43, 226, 0.3); 
    }
    .hero-content { color: white; flex: 1; max-width: 800px;}
    .hero-title { font-size: 3.5rem; font-weight: 800; line-height: 1.1; margin-bottom: 15px; text-shadow: 0 4px 30px rgba(0,0,0,0.8); }
    .tagline { font-size: 1.2rem; font-style: italic; color: #a78bfa; margin-bottom: 25px; font-weight: 500;}
    
    /* STATS ROW - JioHotstar Style */
    .stats-row { display: flex; gap: 10px; margin-bottom: 25px; flex-wrap: wrap; align-items: center; }
    .stat-pill { 
        background: rgba(139, 92, 246, 0.15); 
        backdrop-filter: blur(10px); 
        padding: 8px 16px; 
        border-radius: 20px; 
        font-weight: 500; 
        font-size: 0.8rem; 
        border: 1px solid rgba(139, 92, 246, 0.3);
        color: #e0e7ff;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .stat-pill:first-child {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%);
        border-color: rgba(168, 85, 247, 0.5);
        color: #fff;
    }

    /* CAST CIRCLES */
    .cast-container { text-align: center; margin-bottom: 15px; }
    .cast-img { 
        border-radius: 50%; 
        width: 100%; 
        object-fit: cover; 
        aspect-ratio: 1/1; 
        margin-bottom: 8px; 
        box-shadow: 0 5px 20px rgba(0,0,0,0.5);
        border: 3px solid rgba(139, 92, 246, 0.2);
        transition: all 0.3s ease;
    }
    .cast-img:hover {
        border-color: #8b5cf6;
        transform: scale(1.08);
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
    }
    
    /* Cast name buttons - uniform size */
    [data-testid="column"] .stButton > button {
        min-height: 36px !important;
        max-height: 36px !important;
        font-size: 0.75rem !important;
        padding: 4px 2px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        line-height: 1 !important;
    }
    
    /* SIDEBAR INFO BOX - JioHotstar */
    .info-box { 
        background: linear-gradient(145deg, rgba(26, 26, 46, 0.9) 0%, rgba(22, 33, 62, 0.9) 100%); 
        padding: 25px; 
        border-radius: 16px; 
        border: 1px solid rgba(139, 92, 246, 0.2); 
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    .info-label { color: #a5b4fc; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px; }
    .info-val { font-size: 1.1rem; font-weight: 600; margin-bottom: 18px; color: #fff; }

    /* REVIEWS - JioHotstar */
    .review-card { 
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%); 
        padding: 15px; border-radius: 12px; margin-bottom: 10px; 
        border-left: 4px solid #8b5cf6; 
    }
    .sentiment-pos { color: #34d399; font-weight: bold; font-size: 0.8rem; float: right; }
    
    /* PREMIUM BUTTON STYLES - JioHotstar Purple Theme */
    .stButton>button { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; 
        border-radius: 10px; 
        border: none; 
        font-weight: 600; 
        padding: 12px 24px; 
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        width: 100%; 
        letter-spacing: 0.5px;
        text-transform: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .stButton>button:hover { 
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-3px); 
        box-shadow: 0 10px 30px rgba(139, 92, 246, 0.5); 
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Secondary Button Style */
    div[data-testid="stButton"]:has(button:contains("Back")) button,
    div[data-testid="stButton"]:has(button:contains("←")) button {
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.3);
    }
    div[data-testid="stButton"]:has(button:contains("Back")) button:hover,
    div[data-testid="stButton"]:has(button:contains("←")) button:hover {
        background: rgba(139, 92, 246, 0.25);
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
    }
    
    /* SIDEBAR STYLING - JioHotstar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
        border-right: 1px solid rgba(139, 92, 246, 0.2);
    }
    section[data-testid="stSidebar"] .stButton>button {
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.3);
        color: #e0e7ff;
        margin-bottom: 8px;
        box-shadow: none;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-color: transparent;
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
        color: #fff;
    }
    
    /* Sidebar Search Button - Accent */
    section[data-testid="stSidebar"] div:first-of-type .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: #fff;
    }
    
    /* Logout Button */
    section[data-testid="stSidebar"] .stButton>button:last-of-type {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #a5b4fc;
    }
    section[data-testid="stSidebar"] .stButton>button:last-of-type:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
        box-shadow: none;
    }
    
    /* Selectbox styling - JioHotstar */
    .stSelectbox > div > div {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 10px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(139, 92, 246, 0.1);
        border-radius: 10px;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    /* Slider styling - JioHotstar */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    section[data-testid="stSidebar"] div:first-of-type .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
    }
    
    /* Logout Button */
    section[data-testid="stSidebar"] .stButton>button:last-of-type {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #888;
    }
    section[data-testid="stSidebar"] .stButton>button:last-of-type:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
        box-shadow: none;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: #1a1a1a;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
    }

    /* --- LOGIN PREMIUM STYLES - JioHotstar --- */
    .login-container {
        background: linear-gradient(145deg, rgba(15, 12, 41, 0.95) 0%, rgba(26, 26, 46, 0.95) 100%);
        padding: 50px 40px;
        border-radius: 20px;
        box-shadow: 0 25px 60px rgba(0,0,0,0.5), 0 0 40px rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.2);
        text-align: center;
        margin-top: 60px;
        backdrop-filter: blur(20px);
    }
    .login-title { 
        font-size: 3.5rem; font-weight: 900; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 1px; margin-bottom: 5px; 
    }
    .login-subtitle { color: #a5b4fc; font-size: 1rem; margin-bottom: 35px; font-weight: 300; }
    
    /* Input Fields Styling - JioHotstar */
    .stTextInput > div > div > input { 
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%); 
        color: white; border-radius: 10px; 
        border: 1px solid rgba(139, 92, 246, 0.2); 
        padding: 14px; font-size: 16px; 
    }
    .stTextInput > div > div > input:focus { 
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%); 
        color: white; 
        border: 1px solid #8b5cf6;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
    }
    
    /* Tabs styling - JioHotstar */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; color: #a5b4fc; }
    .stTabs [aria-selected="true"] { color: #8b5cf6; border-bottom: 2px solid #8b5cf6; }
    
    /* JIOHOTSTAR STYLE SPLASH SCREEN */
    .hotstar-splash {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        overflow: hidden;
    }
    
    /* Central Starburst Effect - Purple */
    .starburst {
        position: absolute;
        width: 600px;
        height: 600px;
        animation: starburstAnim 2s ease-out forwards;
    }
    .starburst::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.8) 0%, rgba(168, 85, 247, 0.4) 30%, transparent 70%);
        transform: translate(-50%, -50%);
        animation: burstGlow 2s ease-out forwards;
    }
    @keyframes starburstAnim {
        0% { transform: scale(0); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.8; }
        100% { transform: scale(2); opacity: 0; }
    }
    @keyframes burstGlow {
        0% { opacity: 1; filter: blur(0px); }
        100% { opacity: 0; filter: blur(20px); }
    }
    
    /* Light Rays - Purple/Pink */
    .light-rays {
        position: absolute;
        width: 100%;
        height: 100%;
    }
    .ray {
        position: absolute;
        top: 50%;
        left: 50%;
        width: 3px;
        height: 200px;
        background: linear-gradient(to top, transparent, rgba(168, 85, 247, 0.8), transparent);
        transform-origin: bottom center;
        animation: rayShoot 1.5s ease-out forwards;
        opacity: 0;
    }
    @keyframes rayShoot {
        0% { height: 0; opacity: 0; }
        30% { opacity: 1; }
        100% { height: 300px; opacity: 0; }
    }
    
    /* Star Sparkles - Purple/Pink */
    .sparkle {
        position: absolute;
        width: 8px;
        height: 8px;
        background: linear-gradient(135deg, #a78bfa 0%, #f093fb 100%);
        clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%);
        animation: sparkleAnim 1.5s ease-out forwards;
        opacity: 0;
    }
    @keyframes sparkleAnim {
        0% { transform: scale(0) rotate(0deg); opacity: 0; }
        50% { opacity: 1; }
        100% { transform: scale(1) rotate(180deg); opacity: 0; }
    }
    
    /* Main Logo Text */
    .hotstar-logo {
        position: relative;
        z-index: 10;
        animation: logoReveal 1.2s cubic-bezier(0.34, 1.56, 0.64, 1) 0.3s forwards;
        opacity: 0;
        transform: scale(0);
    }
    @keyframes logoReveal {
        0% { transform: scale(0); opacity: 0; }
        60% { transform: scale(1.15); opacity: 1; }
        80% { transform: scale(0.95); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .logo-text {
        font-size: 4.5rem;
        font-weight: 900;
        letter-spacing: 6px;
        text-transform: uppercase;
        position: relative;
    }
    .logo-text .cine {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .logo-text .match {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Glow Ring - Purple */
    .glow-ring {
        position: absolute;
        width: 350px;
        height: 350px;
        border: 2px solid rgba(139, 92, 246, 0.5);
        border-radius: 50%;
        animation: ringExpand 1.5s ease-out forwards;
        opacity: 0;
    }
    @keyframes ringExpand {
        0% { transform: scale(0); opacity: 0; border-width: 4px; }
        50% { opacity: 1; }
        100% { transform: scale(2.5); opacity: 0; border-width: 1px; }
    }
    
    /* Tagline */
    .hotstar-tagline {
        color: #a5b4fc;
        font-size: 1rem;
        letter-spacing: 8px;
        text-transform: uppercase;
        margin-top: 25px;
        animation: taglineReveal 0.8s ease-out 1s forwards;
        opacity: 0;
    }
    @keyframes taglineReveal {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    /* Shimmer effect on logo */
    .logo-text::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: shimmer 2s ease-in-out 0.8s;
    }
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    /* NEW: Rating Circle */
    .rating-circle {
        width: 50px; height: 50px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.9rem;
        background: conic-gradient(#46d369 var(--rating-pct), #333 0);
        position: relative;
    }
    .rating-circle::before {
        content: ''; position: absolute; width: 40px; height: 40px;
        background: #121212; border-radius: 50%;
    }
    .rating-circle span { position: relative; z-index: 1; color: white; }
    
    /* NEW: Section Header */
    .section-header {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 20px; padding-bottom: 10px;
        border-bottom: 2px solid rgba(229, 9, 20, 0.3);
    }
    .section-title { font-size: 1.5rem; font-weight: 700; color: #fff; }
    
    /* SHARE BUTTONS - Circular Icons */
    .share-container {
        display: flex;
        align-items: center;
        gap: 15px;
        margin: 15px 0;
    }
    .share-label {
        color: #fff;
        font-size: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .share-icons {
        display: flex;
        gap: 12px;
    }
    .share-icon {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        transition: all 0.3s ease;
        font-size: 1.3rem;
    }
    .share-icon:hover {
        transform: scale(1.15);
        box-shadow: 0 5px 20px rgba(0,0,0,0.4);
    }
    .share-facebook {
        background: linear-gradient(135deg, #4267B2 0%, #3b5998 100%);
        color: white;
    }
    .share-twitter {
        background: linear-gradient(135deg, #1DA1F2 0%, #0d8bd9 100%);
        color: white;
    }
    .share-whatsapp {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white;
    }
    .share-telegram {
        background: linear-gradient(135deg, #0088cc 0%, #006699 100%);
        color: white;
    }
    
    /* ========================================== */
    /* MOBILE RESPONSIVE - Phone & Tablet */
    /* ========================================== */
    
    /* Tablet (768px and below) */
    @media (max-width: 768px) {
        .nav-header {
            padding: 15px 20px;
            flex-direction: column;
            gap: 10px;
        }
        .logo { font-size: 24px; }
        
        .hero-container { min-height: 400px; border-radius: 16px; }
        .hero-overlay { 
            padding: 25px; 
            flex-direction: column; 
            min-height: 400px;
            text-align: center;
        }
        .hero-poster { width: 200px; margin: 0 auto; }
        .hero-title { font-size: 2rem; }
        .hero-content { max-width: 100%; }
        
        .stats-row { justify-content: center; }
        .stat-pill { font-size: 0.75rem; padding: 6px 12px; }
        
        .movie-card { margin-bottom: 15px; }
        .card-title { font-size: 0.9rem; }
        
        .info-box { padding: 15px; }
        .share-icon { width: 40px; height: 40px; }
    }
    
    /* Mobile Phone (480px and below) */
    @media (max-width: 480px) {
        .stApp { padding: 0 !important; }
        
        .nav-header {
            padding: 12px 15px;
            border-radius: 0;
            margin-bottom: 15px;
        }
        .logo { font-size: 20px; letter-spacing: 1px; }
        
        .hero-container { 
            min-height: 350px; 
            border-radius: 12px; 
            margin: 0 10px 20px 10px;
        }
        .hero-overlay { 
            padding: 20px 15px; 
            min-height: 350px;
        }
        .hero-poster { width: 160px; border-radius: 10px; }
        .hero-title { font-size: 1.6rem; margin-bottom: 10px; }
        .tagline { font-size: 1rem; margin-bottom: 15px; }
        
        .stats-row { gap: 6px; }
        .stat-pill { 
            font-size: 0.7rem; 
            padding: 5px 10px; 
            border-radius: 15px;
        }
        
        .movie-card { 
            border-radius: 10px; 
            margin-bottom: 12px;
        }
        .card-content { padding: 10px; }
        .card-title { font-size: 0.85rem; }
        .card-meta { font-size: 0.75rem; }
        
        .cast-img { 
            width: 60px !important; 
            height: 60px !important; 
        }
        
        .info-box { 
            padding: 12px; 
            border-radius: 12px;
            margin-bottom: 15px;
        }
        .info-label { font-size: 0.65rem; }
        .info-val { font-size: 0.95rem; margin-bottom: 12px; }
        
        .review-card { 
            padding: 12px; 
            border-radius: 8px;
        }
        
        .share-icon { 
            width: 38px; 
            height: 38px; 
        }
        .share-icons { gap: 10px; }
        
        /* Button adjustments for mobile */
        .stButton>button {
            padding: 10px 16px;
            font-size: 0.9rem;
            border-radius: 8px;
        }
        
        /* Sidebar mobile */
        section[data-testid="stSidebar"] {
            min-width: 250px !important;
        }
        section[data-testid="stSidebar"] .stButton>button {
            padding: 10px 12px;
            font-size: 0.85rem;
        }
        
        /* Login container mobile */
        .login-container {
            padding: 30px 20px;
            margin-top: 30px;
            border-radius: 16px;
        }
        .login-title { font-size: 2.5rem; }
        .login-subtitle { font-size: 0.9rem; }
    }
    
    /* Extra small phones (360px and below) */
    @media (max-width: 360px) {
        .logo { font-size: 18px; }
        .hero-poster { width: 140px; }
        .hero-title { font-size: 1.4rem; }
        .stat-pill { font-size: 0.65rem; padding: 4px 8px; }
        .login-title { font-size: 2rem; }
    }
    
    /* Touch-friendly hover effects for mobile */
    @media (hover: none) {
        .movie-card:hover { transform: none; }
        .share-icon:hover { transform: none; }
        .cast-img:hover { transform: none; }
        
        .movie-card:active { 
            transform: scale(0.98); 
            opacity: 0.9;
        }
        .stButton>button:active {
            transform: scale(0.98);
        }
    }
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATABASE & AUTH & ANIMATION HELPERS
# ==========================================
def make_hashes(p): return hashlib.sha256(str.encode(p)).hexdigest()

def create_dbs():
    if not os.path.exists('users.csv'): pd.DataFrame(columns=['username','password','role']).to_csv('users.csv',index=False)
    if not os.path.exists('watchlist.csv'): pd.DataFrame(columns=['username','movie','date']).to_csv('watchlist.csv',index=False)
    if not os.path.exists('feedback.csv'): pd.DataFrame(columns=['username','movie','feedback','date']).to_csv('feedback.csv',index=False)
    if not os.path.exists('reviews.csv'): 
        pd.DataFrame(columns=['username','movie','rating','review','sentiment','date']).to_csv('reviews.csv',index=False)
    else:
        df = pd.read_csv('reviews.csv')
        if 'sentiment' not in df.columns:
            df['sentiment'] = 'Neutral'; df.to_csv('reviews.csv', index=False)

def add_user(u,p):
    create_dbs(); df=pd.read_csv('users.csv')
    if u in df['username'].values: return False
    new=pd.DataFrame({'username':[u],'password':[make_hashes(p)],'role':['user']}); df=pd.concat([df,new],ignore_index=True); df.to_csv('users.csv',index=False); return True

def login_user(u,p):
    create_dbs(); df=pd.read_csv('users.csv'); h=make_hashes(p)
    res=df[(df['username']==u)&(df['password']==h)]
    if not res.empty: return True, res.iloc[0]['role']
    return False, None

def add_to_watchlist(u,m):
    create_dbs(); df=pd.read_csv('watchlist.csv')
    if not ((df['username']==u)&(df['movie']==m)).any():
        new=pd.DataFrame({'username':[u],'movie':[m],'date':[str(datetime.now().date())]}); df=pd.concat([df,new],ignore_index=True); df.to_csv('watchlist.csv',index=False); return True
    return False

def save_feedback(u,m,f):
    create_dbs(); df=pd.read_csv('feedback.csv')
    df = df[~((df['username']==u) & (df['movie']==m))] 
    new=pd.DataFrame({'username':[u],'movie':[m],'feedback':[f],'date':[str(datetime.now().date())]}); df=pd.concat([df,new],ignore_index=True); df.to_csv('feedback.csv',index=False)

def analyze_sentiment(text):
    text = text.lower()
    pos = ['good', 'great', 'awesome', 'excellent', 'love', 'amazing', 'best', 'fantastic']
    neg = ['bad', 'worst', 'terrible', 'boring', 'awful', 'hate', 'poor', 'stupid']
    score = sum([1 for w in pos if w in text]) - sum([1 for w in neg if w in text])
    return "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"

def add_review(u, m, r, text):
    create_dbs(); sentiment = analyze_sentiment(text); df = pd.read_csv('reviews.csv')
    new = pd.DataFrame({'username':[u], 'movie':[m], 'rating':[r], 'review':[text], 'sentiment':[sentiment], 'date':[str(datetime.now().date())]})
    df = pd.concat([df, new], ignore_index=True); df.to_csv('reviews.csv', index=False)

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

def get_reviews(m): create_dbs(); df = pd.read_csv('reviews.csv'); return df[df['movie'] == m]
def get_watchlist(u): create_dbs(); df=pd.read_csv('watchlist.csv'); return df[df['username']==u]
def get_liked_movies(u): create_dbs(); df=pd.read_csv('feedback.csv'); return df[(df['username']==u) & (df['feedback']=='Like')]
def get_all_users(): return pd.read_csv('users.csv')

# NEW: Track recently viewed
def add_to_recently_viewed(movie_id, title):
    if 'recently_viewed' not in st.session_state:
        st.session_state.recently_viewed = []
    item = {'id': movie_id, 'title': title}
    st.session_state.recently_viewed = [i for i in st.session_state.recently_viewed if i['id'] != movie_id]
    st.session_state.recently_viewed.insert(0, item)
    st.session_state.recently_viewed = st.session_state.recently_viewed[:10]

# ==========================================
# 4. DATA ENGINE
# ==========================================
session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

@st.cache_data(ttl=3600)
def fetch_poster_only(movie_id, title="Movie"):
    clean_title = urllib.parse.quote(str(title))
    placeholder = f"https://placehold.co/500x750/1f1f1f/FFFFFF?text={clean_title}"
    try:
        mid = int(float(movie_id))
        url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={API_KEY}&language=en-US"
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('poster_path'):
                return "https://image.tmdb.org/t/p/w500" + data['poster_path']
        return placeholder
    except Exception:
        return placeholder

def extract_strict_certification(release_dates):
    if not release_dates or 'results' not in release_dates: return None
    ranking_map = {'A': 18, 'UA 16+': 16, 'UA 13+': 13, 'UA': 12, 'U': 0, 'NC-17': 18, 'R': 17, 'PG-13': 13, 'PG': 10, 'G': 0, 'NR': 0, '18+': 18, '18': 18, '16+': 16, '16': 16, '13+': 13, '12+': 12}
    results = release_dates['results']
    country_data = next((item for item in results if item['iso_3166_1'] == 'IN'), None)
    if not country_data: country_data = next((item for item in results if item['iso_3166_1'] == 'US'), None)
    if not country_data: return None
    found_certs = [rel.get('certification', '').strip().upper() for rel in country_data['release_dates'] if rel.get('certification', '').strip()]
    if not found_certs: return None
    found_certs.sort(key=lambda x: ranking_map.get(x, 0), reverse=True)
    return found_certs[0]

@st.cache_data(ttl=3600)
def fetch_full_details(movie_id, title="Movie"):
    poster = fetch_poster_only(movie_id, title)
    clean_title = urllib.parse.quote(str(title))
    backdrop = f"https://placehold.co/1200x600/1f1f1f/FFFFFF?text={clean_title}"
    trailer = None; cast_rich = []; director = "Unknown"; providers = []
    api_is_adult = False; official_cert = None
    try:
        mid = int(float(movie_id))
        url = f"https://api.themoviedb.org/3/movie/{mid}?api_key={API_KEY}&append_to_response=credits,videos,watch/providers,release_dates"
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            main = response.json()
            api_is_adult = main.get('adult', False)
            if 'release_dates' in main: official_cert = extract_strict_certification(main['release_dates'])
            if main.get('backdrop_path'): backdrop = "https://image.tmdb.org/t/p/original" + main['backdrop_path']
            if 'credits' in main:
                if 'cast' in main['credits']:
                    for c in main['credits']['cast'][:6]:
                        pic = "https://image.tmdb.org/t/p/w200" + c['profile_path'] if c.get('profile_path') else f"https://via.placeholder.com/200?text={urllib.parse.quote(c['name'])}"
                        cast_rich.append({'name': c['name'], 'photo': pic})
                if 'crew' in main['credits']:
                    director = next((x['name'] for x in main['credits']['crew'] if x['job'] == 'Director'), "Unknown")
            if 'videos' in main:
                for t_type in ['Trailer', 'Teaser', 'Clip']:
                    found = next((v['key'] for v in main['videos'].get('results', []) if v['site']=='YouTube' and v['type']==t_type), None)
                    if found: trailer = found; break
            if 'watch/providers' in main and 'results' in main['watch/providers']:
                res = main['watch/providers']['results']
                region = 'IN' if 'IN' in res else 'US'
                if region in res and 'flatrate' in res[region]:
                    providers = [{'name': p['provider_name'], 'logo': "https://image.tmdb.org/t/p/original" + p['logo_path']} for p in res[region]['flatrate'] if p.get('logo_path')]
    except: pass
    return {'poster': poster, 'backdrop': backdrop, 'trailer': trailer, 'cast_rich': cast_rich, 'director': director, 'providers': providers, 'api_is_adult': api_is_adult, 'official_cert': official_cert}

@st.cache_resource
def load_data():
    try:
        if not os.path.exists('movie_list.pkl'): return None, None
        movies_dict = pickle.load(open('movie_list.pkl','rb'))
        
        # Use compressed similarity file for GitHub (under 100MB limit)
        import gzip
        if os.path.exists('similarity.pkl.gz'):
            with gzip.open('similarity.pkl.gz', 'rb') as f:
                similarity = pickle.load(f)
        elif os.path.exists('similarity.pkl'):
            similarity = pickle.load(open('similarity.pkl','rb'))
        else:
            similarity = None
            
        movies = pd.DataFrame(movies_dict)
        movies['year_int'] = pd.to_datetime(movies['release_date'], errors='coerce').dt.year.fillna(0).astype(int)
        movies['vote_average'] = pd.to_numeric(movies['vote_average'], errors='coerce').fillna(0)
        if 'movie_id' not in movies.columns and 'id' in movies.columns:
            movies.rename(columns={'id': 'movie_id'}, inplace=True)
        if 'adult' not in movies.columns:
            movies['adult'] = False
            adult_keywords = ['sex', 'erotic', 'kill', 'murder', 'horror', 'nude', 'violence', 'blood', 'crime', 'deadpool', 'joker']
            mask_keywords = movies['overview'].fillna('').apply(lambda x: any(k in x.lower() for k in adult_keywords))
            movies.loc[mask_keywords, 'adult'] = True
        return movies, similarity
    except Exception as e: 
        st.error(f"Error loading data files: {e}"); return None, None

movies, similarity = load_data()

def process_movie_for_ui(row):
    details = fetch_full_details(row.movie_id, row.title)
    genres = "N/A"
    if 'genres_list' in row:
        val = row.genres_list
        if isinstance(val, list): genres = ", ".join(val)
        elif isinstance(val, str): genres = val
    final_cast = details['cast_rich']
    if not final_cast and 'top_cast' in row:
        local_cast = row.top_cast if isinstance(row.top_cast, list) else []
        for actor_name in local_cast[:6]: 
            final_cast.append({'name': actor_name, 'photo': "https://via.placeholder.com/200?text=" + actor_name.split()[0]})
    
    # Currency formatter with USD and INR
    def fmt_curr(val): 
        if val and val > 0:
            usd = "${:,.0f}".format(val)
            inr = "₹{:,.0f} Cr".format((val * 83) / 10000000)  # Convert to Crores
            return f"{usd} ({inr})"
        return "N/A"
    def fmt_run(val): return f"{int(val//60)}h {int(val%60)}m" if val and val > 0 else "N/A"
    rating_val = f"{int(row.vote_average * 10)}%" if row.vote_average > 0 else "NR"
    year_val = str(row.release_date)[:4] if row.release_date and str(row.release_date) != "nan" else "N/A"
    display_cert = "12+"
    is_adult_flag = details.get('api_is_adult', False) or (row.adult if hasattr(row, 'adult') and row.adult else False)
    if details.get('official_cert'): display_cert = details['official_cert']
    elif is_adult_flag: display_cert = "18+"
    strict_ratings = ['A', 'NC-17', 'R', '18+', '18', 'UA 16+', '16+']
    is_strict = display_cert in strict_ratings
    color_hex = '#e50914' if is_strict else 'rgba(255,255,255,0.15)'
    border_hex = '#ff0000' if is_strict else 'rgba(255,255,255,0.2)'
    return {
        'id': row.movie_id, 'title': row.title, 'year': year_val, 'rating_perc': rating_val,
        'runtime': fmt_run(row.runtime) if 'runtime' in row else "N/A",
        'genres': genres, 'tagline': row.tagline if hasattr(row, 'tagline') and row.tagline else "",
        'overview': row.overview if row.overview else "No summary available.",
        'cast_rich': final_cast, 'director': details['director'],
        'poster': details['poster'], 'backdrop': details['backdrop'], 'trailer': details['trailer'],
        'providers': details['providers'], 'budget': fmt_curr(row.budget) if 'budget' in row else "N/A",
        'revenue': fmt_curr(row.revenue) if 'revenue' in row else "N/A",
        'production': row.production_str if 'production_str' in row else "N/A",
        'status': row.status if 'status' in row else "Released",
        'certification_text': f"🔞 {display_cert}" if is_strict else f"✅ {display_cert}",
        'cert_color': color_hex, 'cert_border': border_hex, 'vote_avg': row.vote_average
    }

def process_grid_item(row):
    poster = fetch_poster_only(row.movie_id, row.title)
    year_val = str(row.release_date)[:4] if row.release_date and str(row.release_date) != "nan" else "N/A"
    rating_val = f"⭐ {int(row.vote_average * 10)}%" if row.vote_average > 0 else "NR"
    return {'id': row.movie_id, 'title': row.title, 'poster': poster, 'year': year_val, 'rating': rating_val}

def recommend(movie_title):
    try:
        idx = movies[movies['title'] == movie_title].index[0]
        distances = similarity[idx]
        m_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(process_grid_item, [movies.iloc[i[0]] for i in m_list]))
        return results
    except: return []

def get_top_movies():
    C=movies['vote_average'].mean(); m=movies['vote_count'].quantile(0.9)
    q=movies.copy().loc[movies['vote_count']>=m]
    q['score']=q.apply(lambda x: (x['vote_count']/(x['vote_count']+m)*x['vote_average'])+(m/(m+x['vote_count'])*C), axis=1)
    return q.sort_values('score',ascending=False).head(20)

def display_movies_grid(movies_to_show):
    if not movies_to_show:
        st.info("No movies found."); return
    for i in range(0, len(movies_to_show), 5):
        cols = st.columns(5, gap="medium")
        batch = movies_to_show[i:i+5]
        for idx, data in enumerate(batch):
            with cols[idx]:
                link_url = f"?id={data['id']}&user={st.session_state.username}"
                st.markdown(f"""
                <a href="{link_url}" target="_self" style="text-decoration:none;">
                    <div class="movie-card">
                        <img src="{data['poster']}">
                        <div class="card-content">
                            <div class="card-title">{data['title']}</div>
                            <div class="card-meta">{data['rating']}</div>
                        </div>
                    </div>
                </a>""", unsafe_allow_html=True)

def set_detail(movie_id): 
    row = movies[movies['movie_id'] == movie_id].iloc[0]
    data = process_movie_for_ui(row)
    st.session_state.view_mode='detail'; st.session_state.detail_movie=data
    st.query_params["id"] = movie_id
    add_to_recently_viewed(movie_id, row.title)

def go_grid(): 
    st.session_state.view_mode='grid'; st.session_state.detail_movie=None
    if "id" in st.query_params: del st.query_params["id"]

def set_page(p): st.session_state.page=p; st.session_state.view_mode='grid'
def search_movie(movie_name): st.session_state.page='search'; st.session_state.view_mode='grid'; st.session_state.search_type='movie'; st.session_state.search_query=movie_name
def search_director_movies(director_name): st.session_state.page='search'; st.session_state.view_mode='grid'; st.session_state.search_type='director'; st.session_state.search_query=director_name
def search_actor_movies(actor_name): st.session_state.page='search'; st.session_state.view_mode='grid'; st.session_state.search_type='actor'; st.session_state.search_query=actor_name

# ==========================================
# 5. MAIN APPLICATION
# ==========================================
if 'id' in st.query_params and not st.session_state.detail_movie and movies is not None:
    try: mid = int(st.query_params["id"]); set_detail(mid)
    except: pass

if not st.session_state.logged_in:
    if "user" in st.query_params: st.session_state.logged_in=True; st.session_state.username=st.query_params["user"]; st.rerun()
    lc1, lc2, lc3 = st.columns([1, 1, 1])
    with lc2:
        st.markdown("""<div class='login-container'><div class='login-title'>CineMatch</div><div class='login-subtitle'>Your gateway to unlimited entertainment.</div></div>""", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔒 Sign In", "📝 Register"])
        with tab_login:
            with st.form("login_form"):
                st.markdown("<br>", unsafe_allow_html=True)
                u = st.text_input("Username", placeholder="Username")
                p = st.text_input("Password", type='password', placeholder="Password")
                st.markdown("""<div style='text-align: right; margin-top: -10px; margin-bottom: 20px;'><a href='#' style='color: #b3b3b3; font-size: 0.8rem; text-decoration: none;'>Forgot Password?</a></div>""", unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                if submitted:
                    v, r = login_user(u, p)
                    if v: 
                        st.session_state.logged_in = True; st.session_state.username = u; st.session_state.role = r
                        st.session_state.show_splash = True; st.query_params["user"] = u; st.rerun()
                    else: st.error("Incorrect username or password")
        with tab_register:
            with st.form("register_form"):
                st.markdown("<br>", unsafe_allow_html=True)
                nu = st.text_input("Choose Username", placeholder="New username")
                np = st.text_input("Choose Password", type='password', placeholder="New password")
                st.markdown("<br>", unsafe_allow_html=True)
                reg_submitted = st.form_submit_button("Create Account", use_container_width=True)
                if reg_submitted: 
                    if nu and np:
                        if add_user(nu, np): st.success("Account created! Please Sign In.")
                        else: st.error("Username already taken.")
                    else: st.warning("Please fill in all fields.")
else:
    if st.session_state.show_splash:
        splash_container = st.empty()
        with splash_container.container():
            st.markdown('''
            <div class="hotstar-splash">
                <div class="starburst"></div>
                <div class="glow-ring" style="animation-delay: 0s;"></div>
                <div class="glow-ring" style="animation-delay: 0.3s;"></div>
                <div class="glow-ring" style="animation-delay: 0.6s;"></div>
                <div class="light-rays">
                    <div class="ray" style="transform: translate(-50%, 0) rotate(0deg);"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(30deg); animation-delay: 0.05s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(60deg); animation-delay: 0.1s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(90deg); animation-delay: 0.15s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(120deg); animation-delay: 0.2s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(150deg); animation-delay: 0.25s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(180deg); animation-delay: 0.3s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(210deg); animation-delay: 0.35s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(240deg); animation-delay: 0.4s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(270deg); animation-delay: 0.45s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(300deg); animation-delay: 0.5s;"></div>
                    <div class="ray" style="transform: translate(-50%, 0) rotate(330deg); animation-delay: 0.55s;"></div>
                </div>
                <div class="sparkle" style="left: 40%; top: 35%; animation-delay: 0.3s;"></div>
                <div class="sparkle" style="left: 60%; top: 40%; animation-delay: 0.5s;"></div>
                <div class="sparkle" style="left: 35%; top: 55%; animation-delay: 0.4s;"></div>
                <div class="sparkle" style="left: 65%; top: 60%; animation-delay: 0.6s;"></div>
                <div class="sparkle" style="left: 50%; top: 30%; animation-delay: 0.2s;"></div>
                <div class="sparkle" style="left: 45%; top: 65%; animation-delay: 0.7s;"></div>
                <div class="hotstar-logo">
                    <div class="logo-text">
                        <span class="cine">CINE</span><span class="match">MATCH</span>
                    </div>
                </div>
                <div class="hotstar-tagline">Premium Entertainment</div>
            </div>
            ''', unsafe_allow_html=True)
        
        time.sleep(3.5); st.session_state.show_splash = False; st.rerun()
    else:
        st.markdown(f"""<div class="nav-header"><div class="logo">CineMatch</div><div class="user-badge">👤 {st.session_state.username}</div></div>""", unsafe_allow_html=True)
        with st.sidebar:
            st.markdown("### 🔍 Quick Search")
            if movies is not None:
                search_q = st.selectbox("Find Movie", movies['title'].values, index=None, placeholder="Type movie name...", label_visibility="collapsed")
                if st.button("Go Search", type="primary", use_container_width=True):
                    if search_q: search_movie(search_q); st.rerun()
            st.markdown("---")
            st.button("🏠 Home", use_container_width=True, on_click=set_page, args=('home',))
            st.button("🕐 Recently Viewed", use_container_width=True, on_click=set_page, args=('recent',))
            st.button("❤️ Watchlist", use_container_width=True, on_click=set_page, args=('watchlist',))
            st.button("👍 Liked", use_container_width=True, on_click=set_page, args=('liked',))
            if st.session_state.username == 'admin': 
                if st.button("📊 Admin Dashboard", use_container_width=True): st.session_state.page='admin'; st.session_state.view_mode='grid'; st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("☰ Filters"):
                if movies is not None:
                    all_genres = set()
                    for sublist in movies['genres_list']:
                        if isinstance(sublist, list):
                            for g in sublist: all_genres.add(g)
                    genre_options = ["All", "Adult"] + sorted(list(all_genres))
                    sel_g = st.selectbox("By Genre", genre_options)
                    st.markdown("#### Year Range")
                    min_yr, max_yr = st.slider("Year", 1950, 2024, (1990, 2024))
                    st.markdown("#### Min Rating")
                    min_rat = st.slider("Rating %", 0, 100, 0)
                    if st.button("Apply Filters"): 
                        st.session_state.page='filtered'; st.session_state.selected_genre=sel_g
                        st.session_state.min_year=min_yr; st.session_state.max_year=max_yr
                        st.session_state.min_rating=min_rat; st.session_state.view_mode='grid'; st.rerun()
            st.markdown("---")
            if st.button("Logout"): st.session_state.logged_in=False; st.query_params.clear(); st.rerun()

        if movies is None:
            st.error("⚠️ Data files not found!")
        else:
            if st.session_state.view_mode == 'detail' and st.session_state.detail_movie:
                m = st.session_state.detail_movie
                back_label = "← Back"
                if st.session_state.page == 'home': back_label = "← Back to Home"
                elif st.session_state.page == 'genre': back_label = f"← Back to {st.session_state.selected_genre}"
                elif st.session_state.page == 'search': back_label = "← Back to Search Results"
                if st.button(back_label, type="secondary"): go_grid(); st.rerun()
                st.markdown(f"""
                <div class="hero-container" style="background-image: url('{m['backdrop']}');">
                    <div class="hero-overlay">
                        <img src="{m['poster']}" class="hero-poster">
                        <div class="hero-content">
                            <h1 class="hero-title">{m['title']}</h1>
                            <div class="tagline">{m['tagline']}</div>
                            <div class="stats-row">
                                <span class="stat-pill" style="background: {m['cert_color']}; border-color: {m['cert_border']}">{m['certification_text']}</span>
                                <span class="stat-pill">⭐ {m['rating_perc']} Match</span>
                                <span class="stat-pill">📅 {m['year']}</span>
                                <span class="stat-pill">⏱ {m['runtime']}</span>
                                <span class="stat-pill">🎭 {m['genres']}</span>
                            </div>
                            <p style="font-size:1.2rem; line-height:1.6; opacity:0.9; margin-top:20px;">{m['overview']}</p>
                        </div>
                </div>
                </div>""", unsafe_allow_html=True)
                
                # Main content columns
                col_left, col_right = st.columns([3, 2], gap="large")
                
                with col_left:
                    # TOP CAST SECTION
                    st.markdown("### 🎭 Top Cast")
                    if m['cast_rich']:
                        cols = st.columns(6)
                        for i, actor in enumerate(m['cast_rich'][:6]):
                            with cols[i]:
                                st.markdown(f"""<div class="cast-container"><img src="{actor['photo']}" class="cast-img"></div>""", unsafe_allow_html=True)
                                if st.button(actor['name'].split()[0], key=f"act_{i}", use_container_width=True): 
                                    search_actor_movies(actor['name']); st.rerun()
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # TRAILER SECTION
                    st.markdown("### 🎬 Trailer")
                    if m['trailer']: 
                        st.video(f"https://www.youtube.com/watch?v={m['trailer']}")
                    else: 
                        st.link_button("🔎 Search on YouTube", f"https://www.youtube.com/results?search_query={m['title']}+trailer", use_container_width=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # RATE THIS MOVIE - Now under Trailer
                    st.markdown("### ✍️ Rate & Review")
                    with st.form("rev_form"):
                        rev_score = st.slider("Your Rating", 1, 10, 8)
                        rev_txt = st.text_area("Write your review...", height=100, placeholder="Share your thoughts about this movie...")
                        if st.form_submit_button("Submit Review", use_container_width=True): 
                            add_review(st.session_state.username, m['title'], rev_score, rev_txt)
                            st.success("Review posted!"); st.rerun()
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # USER REVIEWS SECTION
                    st.markdown("### 📰 User Reviews")
                    revs = get_reviews(m['title'])
                    if not revs.empty:
                        for _, r in revs.iterrows():
                            st.markdown(f"""<div class="review-card"><strong>{r['username']}</strong> <span class="sentiment-pos">{r['sentiment']}</span><div style="margin-top:5px; color:#ddd;">"{r['review']}"</div></div>""", unsafe_allow_html=True)
                    else: 
                        st.caption("No reviews yet. Be the first to review!")
                
                with col_right:
                    # ACTION BUTTONS
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("❤️ Watchlist", use_container_width=True): 
                            add_to_watchlist(st.session_state.username, m['title']); st.toast("Added to Watchlist!")
                    with c2:
                        if st.button("👍 Like", use_container_width=True): 
                            save_feedback(st.session_state.username, m['title'], "Like"); st.toast("Liked!")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # SHARE SECTION
                    st.markdown("### 📤 Share")
                    share_url = f"https://your-app.streamlit.app/?id={m['id']}"
                    share_text = f"Check out {m['title']}!"
                    st.markdown(f'''
                    <div class="share-container" style="margin-bottom: 20px;">
                        <div class="share-icons">
                            <a href="https://www.facebook.com/sharer/sharer.php?u={share_url}" target="_blank" class="share-icon share-facebook" title="Facebook">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>
                            </a>
                            <a href="https://twitter.com/intent/tweet?text={share_text}&url={share_url}" target="_blank" class="share-icon share-twitter" title="Twitter">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"/></svg>
                            </a>
                            <a href="https://wa.me/?text={share_text} {share_url}" target="_blank" class="share-icon share-whatsapp" title="WhatsApp">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>
                            </a>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    # MOVIE INFO SECTION
                    st.markdown("### 🎬 Movie Info")
                    st.markdown("""<div class="info-box">""", unsafe_allow_html=True)
                    st.markdown(f"<div class='info-label'>Director</div><div class='info-val'>{m['director']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='info-label'>Budget</div><div class='info-val'>{m['budget']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='info-label'>Revenue</div><div class='info-val'>{m['revenue']}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # WHERE TO WATCH SECTION
                    st.markdown("### 📺 Where to Watch")
                    if m['providers']:
                        html = '<div style="display:flex; flex-wrap:wrap; gap:12px; margin-bottom: 15px;">'
                        for p in m['providers']:
                            html += f'<img src="{p["logo"]}" title="{p["name"]}" style="width:50px; height:50px; border-radius:12px; border: 2px solid rgba(139, 92, 246, 0.3); transition: transform 0.2s;" onmouseover="this.style.transform=\'scale(1.1)\'" onmouseout="this.style.transform=\'scale(1)\'">'
                        html += '</div>'
                        st.markdown(html, unsafe_allow_html=True)
                    else: 
                        st.info("Not streaming in your region.")
            elif st.session_state.page == 'admin':
                st.title("📊 Admin Dashboard")
                try:
                    df_likes = pd.read_csv('feedback.csv'); df_watch = pd.read_csv('watchlist.csv'); df_reviews = pd.read_csv('reviews.csv')
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Likes", len(df_likes)); c2.metric("Watchlist", len(df_watch)); c3.metric("Reviews", len(df_reviews))
                    if not df_likes.empty:
                        top_likes = df_likes['movie'].value_counts().reset_index(); top_likes.columns = ['Movie', 'Count']
                        fig = px.bar(top_likes.head(10), x='Movie', y='Count', color='Count', title="Top 10 Liked")
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e: st.error(f"Error: {e}")
            else:
                if st.session_state.page == 'home':
                    st.markdown("### 🔥 Trending Now")
                    top_df = get_top_movies()
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        movies_to_show = list(executor.map(process_grid_item, [row for _, row in top_df.iterrows()]))
                    display_movies_grid(movies_to_show)
                elif st.session_state.page == 'recent':
                    st.markdown("### 🕐 Recently Viewed")
                    if st.session_state.recently_viewed:
                        recent_ids = [r['id'] for r in st.session_state.recently_viewed]
                        sub_df = movies[movies['movie_id'].isin(recent_ids)]
                        with ThreadPoolExecutor(max_workers=3) as executor:
                            movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                        display_movies_grid(movies_to_show)
                    else: st.info("No recently viewed movies.")
                elif st.session_state.page == 'genre':
                    g = st.session_state.selected_genre
                    if g == "All": sub_df = movies.head(20)
                    elif g == "Adult": sub_df = movies[movies['adult'] == True].head(20) if 'adult' in movies.columns else pd.DataFrame()
                    else: sub_df = movies[movies['genres_list'].apply(lambda x: g in x if isinstance(x, list) else False)].head(20)
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                    st.markdown(f"### 📂 Genre: {g}"); display_movies_grid(movies_to_show)
                elif st.session_state.page == 'filtered':
                    g = st.session_state.selected_genre
                    min_y, max_y = st.session_state.min_year, st.session_state.max_year
                    min_r = st.session_state.min_rating
                    sub_df = movies[(movies['year_int'] >= min_y) & (movies['year_int'] <= max_y) & (movies['vote_average'] * 10 >= min_r)]
                    if g != "All" and g != "Adult":
                        sub_df = sub_df[sub_df['genres_list'].apply(lambda x: g in x if isinstance(x, list) else False)]
                    elif g == "Adult":
                        sub_df = sub_df[sub_df['adult'] == True] if 'adult' in sub_df.columns else pd.DataFrame()
                    sub_df = sub_df.head(30)
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                    st.markdown(f"### 🔍 Filtered Results ({len(movies_to_show)} movies)"); display_movies_grid(movies_to_show)
                elif st.session_state.page == 'search':
                    q_type = st.session_state.search_type; query = st.session_state.search_query
                    if q_type == 'movie':
                        exact = movies[movies['title'].str.lower() == query.lower()]
                        if not exact.empty:
                            em = exact.iloc[0]; st.markdown(f"### Result: {em['title']}")
                            eg = process_grid_item(em)
                            cols = st.columns(5)
                            with cols[0]:
                                st.markdown(f"""<a href="?id={eg['id']}&user={st.session_state.username}" target="_self" style="text-decoration:none;"><div class="movie-card"><img src="{eg['poster']}"><div class="card-content"><div class="card-title">{eg['title']}</div></div></div></a>""", unsafe_allow_html=True)
                            st.markdown(f"### Similar to {em['title']}"); recs = recommend(em['title']); display_movies_grid(recs)
                        else:
                            mask = movies['title'].str.contains(query, case=False, regex=False, na=False)
                            results = movies[mask].head(20)
                            with ThreadPoolExecutor(max_workers=3) as executor:
                                movies_to_show = list(executor.map(process_grid_item, [row for _, row in results.iterrows()]))
                            st.markdown(f"### Results for: {query}"); display_movies_grid(movies_to_show)
                    elif q_type == 'director':
                        sub_df = movies[movies['director'].apply(lambda x: query in str(x))]
                        with ThreadPoolExecutor(max_workers=3) as executor:
                            movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                        st.markdown(f"### Director: {query}"); display_movies_grid(movies_to_show)
                    elif q_type == 'actor':
                        sub_df = movies[movies['top_cast'].apply(lambda x: query in x if isinstance(x, list) else False)]
                        with ThreadPoolExecutor(max_workers=3) as executor:
                            movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                        st.markdown(f"### Actor: {query}"); display_movies_grid(movies_to_show)
                elif st.session_state.page == 'watchlist':
                    wl = get_watchlist(st.session_state.username)
                    if not wl.empty:
                        sub_df = movies[movies['title'].isin(wl['movie'])]
                        with ThreadPoolExecutor(max_workers=3) as executor:
                            movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                        st.markdown("### ❤️ My Watchlist"); display_movies_grid(movies_to_show)
                    else: st.info("Watchlist is empty.")
                elif st.session_state.page == 'liked':
                    lk = get_liked_movies(st.session_state.username)
                    if not lk.empty:
                        sub_df = movies[movies['title'].isin(lk['movie'])]
                        with ThreadPoolExecutor(max_workers=3) as executor:
                            movies_to_show = list(executor.map(process_grid_item, [row for _, row in sub_df.iterrows()]))
                        st.markdown("### 👍 Liked Movies"); display_movies_grid(movies_to_show)
                    else: st.info("No liked movies yet.")