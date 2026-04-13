/**
 * CineMatch Mobile — Single Page Application
 * Premium movie recommendation PWA
 */

// ===== STATE =====
const S = {
    user: null, role: null, page: 'login',
    detailData: null, detailId: null,
    searchQuery: '', searchType: 'movie',
    recentlyViewed: JSON.parse(localStorage.getItem('cm_recent') || '[]'),
    genreList: [],
};

// ===== API HELPER =====
async function api(endpoint, opts = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `/api/${endpoint}`;
    const config = { headers: { 'Content-Type': 'application/json' }, ...opts };
    if (opts.body && typeof opts.body === 'object') config.body = JSON.stringify(opts.body);
    const res = await fetch(url, config);
    return res.json();
}

// ===== TOAST =====
function toast(msg, type = 'success') {
    const c = document.getElementById('toast-container');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    c.appendChild(el);
    setTimeout(() => el.remove(), 3000);
}

// ===== NAVIGATE =====
function navigate(page, params = {}) {
    Object.assign(S, { page, ...params });
    render();
    window.scrollTo({ top: 0, behavior: 'auto' });
}

// ===== RENDER =====
function render() {
    const app = document.getElementById('app');
    let html = '';
    switch (S.page) {
        case 'login': html = loginPage(); break;
        case 'splash': html = splashPage(); break;
        case 'home': html = appShell(homePage); break;
        case 'search': html = appShell(searchPage); break;
        case 'detail': html = appShell(detailPage); break;
        case 'watchlist': html = appShell(watchlistPage); break;
        case 'liked': html = appShell(likedPage); break;
        case 'insights': html = appShell(insightsPage); break;
        case 'admin': html = appShell(adminPage); break;
        default: html = loginPage();
    }
    app.innerHTML = html;
    bindEvents();
}

// ===== APP SHELL =====
function appShell(contentFn) {
    const isAdmin = S.role === 'admin' || S.user === 'admin';
    return `
    <div class="page-enter">
        <div class="top-bar">
            <div class="top-bar-logo">CINEMATCH</div>
            <div class="top-bar-user">👤 ${S.user}</div>
        </div>
        <div class="search-bar">
            <input class="search-input" id="searchInput" placeholder="Search movies, actors, directors..." value="${S.searchQuery || ''}">
            <button class="search-btn" id="searchBtn">🔍 Go</button>
        </div>
        <div id="content">${contentFn()}</div>
        <div class="bottom-nav">
            <button class="nav-btn ${S.page === 'home' ? 'active' : ''}" onclick="navigate('home')"><span class="nav-icon">🏠</span>Home</button>
            <button class="nav-btn ${S.page === 'watchlist' ? 'active' : ''}" onclick="navigate('watchlist')"><span class="nav-icon">❤️</span>Saved</button>
            <button class="nav-btn ${S.page === 'liked' ? 'active' : ''}" onclick="navigate('liked')"><span class="nav-icon">👍</span>Liked</button>
            <button class="nav-btn ${S.page === 'insights' ? 'active' : ''}" onclick="navigate('insights')"><span class="nav-icon">🧠</span>ML</button>
            ${isAdmin ? `<button class="nav-btn ${S.page === 'admin' ? 'active' : ''}" onclick="navigate('admin')"><span class="nav-icon">📊</span>Admin</button>` : ''}
            <button class="nav-btn" onclick="logout()"><span class="nav-icon">🚪</span>Exit</button>
        </div>
    </div>`;
}

// ===== LOGIN PAGE =====
function loginPage() {
    return `<div class="login-page"><div class="login-box">
        <div class="login-logo">CINEMATCH</div>
        <div class="login-sub">Your gateway to unlimited entertainment</div>
        <div class="tab-group">
            <button class="tab-btn active" onclick="switchTab('login')">🔒 Sign In</button>
            <button class="tab-btn" onclick="switchTab('register')">📝 Register</button>
            <button class="tab-btn" onclick="switchTab('forgot')">🔑 Reset</button>
        </div>
        <div id="tab-login" class="tab-content active">
            <div class="form-group"><label class="form-label">Username</label><input class="form-input" id="loginUser" placeholder="Enter username"></div>
            <div class="form-group"><label class="form-label">Password</label><input class="form-input" id="loginPass" type="password" placeholder="Enter password"></div>
            <button class="btn btn-primary" id="loginBtn">Sign In</button>
        </div>
        <div id="tab-register" class="tab-content">
            <div class="form-group"><label class="form-label">Username</label><input class="form-input" id="regUser" placeholder="Choose username"></div>
            <div class="form-group"><label class="form-label">Password</label><input class="form-input" id="regPass" type="password" placeholder="Choose password (min 4)"></div>
            <div class="form-group"><label class="form-label">Security Question</label>
                <select class="form-select" id="regQuestion">
                    <option>What is your pet's name?</option><option>What city were you born in?</option>
                    <option>What is your favorite movie?</option><option>What was your first school's name?</option>
                </select></div>
            <div class="form-group"><label class="form-label">Security Answer</label><input class="form-input" id="regAnswer" placeholder="Your answer"></div>
            <button class="btn btn-primary" id="regBtn">Create Account</button>
        </div>
        <div id="tab-forgot" class="tab-content">
            <div class="form-group"><label class="form-label">Username</label><input class="form-input" id="forgotUser" placeholder="Your username"></div>
            <button class="btn btn-secondary btn-sm" id="forgotLookupBtn" style="margin-bottom:16px">Look Up</button>
            <div id="forgotFields" style="display:none">
                <div id="forgotQuestion" style="color:var(--accent-light);font-size:0.85rem;margin-bottom:12px;font-weight:500"></div>
                <div class="form-group"><label class="form-label">Answer</label><input class="form-input" id="forgotAns" type="password" placeholder="Security answer"></div>
                <div class="form-group"><label class="form-label">New Password</label><input class="form-input" id="forgotNewPass" type="password" placeholder="New password (min 4)"></div>
                <button class="btn btn-primary" id="forgotResetBtn">Reset Password</button>
            </div>
        </div>
    </div></div>`;
}

function splashPage() {
    return `<div class="splash-screen"><div class="splash-logo">CINEMATCH</div><div class="splash-tagline">Premium Entertainment</div></div>`;
}

// ===== HOME PAGE =====
function homePage() {
    return `<div class="section-title">🏆 Top Rated</div><div id="movieGrid" class="movie-grid">${loadingCards(12)}</div>`;
}

// ===== SEARCH PAGE =====
function searchPage() {
    return `<div class="section-title">🔍 Results for "${S.searchQuery}"</div><div id="movieGrid" class="movie-grid">${loadingCards(9)}</div>`;
}

// ===== WATCHLIST PAGE =====
function watchlistPage() {
    return `<div class="section-title">❤️ My Watchlist</div><div id="movieGrid" class="movie-grid">${loadingCards(6)}</div>`;
}

// ===== LIKED PAGE =====
function likedPage() {
    return `<div class="section-title">👍 Liked Movies</div><div id="movieGrid" class="movie-grid">${loadingCards(6)}</div>`;
}

// ===== DETAIL PAGE =====
function detailPage() {
    if (!S.detailData) return `<div class="loading-container"><div class="spinner"></div><p style="color:var(--text-muted)">Loading movie details...</p></div>`;
    const m = S.detailData;
    const rt = m.runtime ? `${Math.floor(m.runtime/60)}h ${m.runtime%60}m` : 'N/A';
    const budgetStr = m.budget > 0 ? `$${(m.budget/1000000).toFixed(1)}M` : 'N/A';
    const revStr = m.revenue > 0 ? `$${(m.revenue/1000000).toFixed(1)}M` : 'N/A';
    const backdrop = m.backdrop || m.poster;
    let certClass = '';
    const strictCerts = ['A', 'NC-17', 'R', '18+', '18', 'UA 16+'];
    if (strictCerts.includes(m.certification)) certClass = 'style="background:#e50914;border-color:#ff0000;color:white"';

    let aiHtml = '';
    if (m.ai_prediction) {
        const pred = m.ai_prediction.predicted_rating;
        const actual = m.rating;
        const diff = Math.abs(pred - actual);
        const accColor = diff < 1 ? 'var(--success)' : diff < 2 ? 'var(--warning)' : 'var(--error)';
        aiHtml = `<div class="ai-card"><div class="ai-emoji">🤖</div><div style="flex:1"><div class="ai-label">AI Predicted Rating</div><div class="ai-value">${pred}/10 <span style="font-size:0.8rem;color:${accColor};margin-left:8px">vs Actual: ${actual}/10</span></div><div class="ai-sub">Random Forest model | Confidence: ${m.ai_prediction.confidence}</div></div></div>`;
    }

    let castHtml = '';
    const castList = m.cast_rich && m.cast_rich.length ? m.cast_rich : (m.cast || []).map(n => ({ name: n, photo: `https://placehold.co/200x200/1a1a2e/a5b4fc?text=${encodeURIComponent(n.split(' ')[0])}` }));
    if (castList.length) {
        castHtml = `<div class="detail-section"><div class="detail-section-title">🎭 Top Cast</div></div><div class="cast-scroll">${castList.map(c => `<div class="cast-circle" onclick="navigate('search',{searchQuery:'${c.name.replace(/'/g,"\\'")}',searchType:'actor'})"><img src="${c.photo}" alt="${c.name}" loading="lazy"><div class="cast-name">${c.name.split(' ')[0]}</div></div>`).join('')}</div>`;
    }

    let trailerHtml = '';
    if (m.trailer) {
        trailerHtml = `<div class="detail-section"><div class="detail-section-title">🎬 Trailer</div></div><div class="trailer-frame"><iframe src="https://www.youtube-nocookie.com/embed/${m.trailer}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>`;
    } else {
        trailerHtml = `<div style="padding:0 20px"><a href="https://www.youtube.com/results?search_query=${encodeURIComponent(m.title)}+trailer" target="_blank" class="btn btn-secondary" style="margin-bottom:16px">🔎 Search Trailer on YouTube</a></div>`;
    }

    let providersHtml = '';
    if (m.providers && m.providers.length) {
        providersHtml = `<div class="detail-section"><div class="detail-section-title">📺 Where to Watch</div></div><div class="provider-row">${m.providers.map(p => `<img src="${p.logo}" title="${p.name}" class="provider-logo" loading="lazy">`).join('')}</div>`;
    }

    const shareUrl = encodeURIComponent(window.location.origin + `?movie=${m.id}`);
    const shareText = encodeURIComponent(`Check out ${m.title} on CineMatch!`);

    return `<div class="detail-page">
        <div class="detail-back"><button class="btn btn-secondary btn-sm" onclick="goBack()">← Back</button></div>
        <div class="hero-section" style="background-image:url('${backdrop}')">
            <div class="hero-gradient">
                <div class="hero-poster"><img src="${m.poster}" alt="${m.title}" loading="lazy"></div>
                <div class="hero-info">
                    <div class="hero-title">${m.title}</div>
                    ${m.tagline ? `<div class="hero-tagline">"${m.tagline}"</div>` : ''}
                    <div class="stat-pills">
                        <span class="stat-pill" ${certClass}>${m.certification || 'UA'}</span>
                        <span class="stat-pill highlight">⭐ ${m.rating}/10</span>
                        <span class="stat-pill">📅 ${m.year}</span>
                        <span class="stat-pill">⏱ ${rt}</span>
                    </div>
                </div>
            </div>
        </div>
        ${aiHtml}
        <div class="detail-section"><div class="detail-section-title">📖 Overview</div><p class="overview-text">${m.overview}</p></div>
        <div class="action-row">
            <button class="action-btn" id="watchlistBtn" onclick="addWatchlist('${m.title.replace(/'/g,"\\'")}')">❤️ Watchlist</button>
            <button class="action-btn" id="likeBtn" onclick="addLike('${m.title.replace(/'/g,"\\'")}')">👍 Like</button>
        </div>
        <div class="detail-section"><div class="detail-section-title">📤 Share</div></div>
        <div class="share-row">
            <a href="https://wa.me/?text=${shareText}%20${shareUrl}" target="_blank" class="share-btn share-wa">💬</a>
            <a href="https://twitter.com/intent/tweet?text=${shareText}&url=${shareUrl}" target="_blank" class="share-btn share-tw">🐦</a>
            <a href="https://www.facebook.com/sharer/sharer.php?u=${shareUrl}" target="_blank" class="share-btn share-fb">📘</a>
        </div>
        ${castHtml}
        ${trailerHtml}
        <div class="info-box">
            <div class="info-row"><span class="info-label">Director</span><span class="info-value">${m.director}</span></div>
            <div class="info-row"><span class="info-label">Budget</span><span class="info-value">${budgetStr}</span></div>
            <div class="info-row"><span class="info-label">Revenue</span><span class="info-value">${revStr}</span></div>
            <div class="info-row"><span class="info-label">Genres</span><span class="info-value">${(m.genres_list || []).join(', ') || m.genres}</span></div>
        </div>
        ${providersHtml}
        <div class="detail-section"><div class="detail-section-title">✍️ Rate & Review</div></div>
        <div style="padding:0 20px 16px">
            <div class="form-group"><label class="form-label">Your Rating: <span id="ratingVal">8</span>/10</label><input type="range" min="1" max="10" value="8" id="reviewRating" style="width:100%;accent-color:var(--accent)" oninput="document.getElementById('ratingVal').textContent=this.value"></div>
            <div class="form-group"><textarea class="form-textarea" id="reviewText" placeholder="Share your thoughts about this movie..."></textarea></div>
            <button class="btn btn-primary btn-sm" id="submitReviewBtn" onclick="submitReview('${m.title.replace(/'/g,"\\'")}')">Submit Review</button>
        </div>
        <div class="detail-section"><div class="detail-section-title">📰 User Reviews</div></div>
        <div id="reviewsList"><div class="loading-container"><div class="spinner"></div></div></div>
        <div class="detail-section"><div class="detail-section-title">🎬 Similar Movies</div></div>
        <div id="recGrid" class="movie-grid" style="padding-bottom:120px">${loadingCards(6)}</div>
    </div>`;
}

// ===== ML INSIGHTS PAGE =====
function insightsPage() {
    return `<div class="section-title">🧠 ML Insights Dashboard</div>
        <p style="padding:0 20px 16px;color:var(--text-secondary);font-size:0.85rem">Machine learning analytics powered by <b>Naive Bayes</b>, <b>Random Forest</b>, and <b>TF-IDF</b> models.</p>
        <div id="insightCards" class="insight-cards">${loadingCards(3)}</div>
        <div class="section-title">🎬 Top Directors by Rating</div>
        <div id="directorsChart"><div class="loading-container"><div class="spinner"></div></div></div>
        <div class="section-title">🎯 Movie Success Factors</div>
        <div id="factorsChart"><div class="loading-container"><div class="spinner"></div></div></div>
        <div class="section-title">💬 Review Sentiment</div>
        <div id="sentimentChart"><div class="loading-container"><div class="spinner"></div></div></div>
        <div class="section-title">🔬 Live Sentiment Analyzer</div>
        <p style="padding:0 20px 8px;color:var(--text-secondary);font-size:0.85rem">Type any movie review to see ML analysis in real-time.</p>
        <div style="padding:0 20px 16px">
            <textarea class="form-textarea" id="sentimentInput" placeholder="e.g., This movie was absolutely brilliant with stunning visuals..."></textarea>
            <button class="btn btn-primary btn-sm" style="margin-top:8px" onclick="analyzeSentiment()">Analyze Sentiment</button>
        </div>
        <div id="sentimentResult"></div>
        <div style="height:100px"></div>`;
}

// ===== ADMIN PAGE =====
function adminPage() {
    return `<div class="section-title">📊 Admin Dashboard</div>
        <div id="adminMetrics" class="metric-row">${loadingCards(3)}</div>
        <div class="section-title">🏆 Top Liked Movies</div>
        <div id="topLiked"><div class="loading-container"><div class="spinner"></div></div></div>
        <div class="section-title">🔐 Reset User Password</div>
        <div style="padding:0 20px 120px">
            <div class="form-group"><label class="form-label">Select User</label><select class="form-select" id="adminUserSelect"><option>Loading...</option></select></div>
            <div class="form-group"><label class="form-label">New Password</label><input class="form-input" id="adminNewPass" type="password" placeholder="New password"></div>
            <button class="btn btn-danger btn-sm" onclick="adminResetPassword()">🔄 Reset Password</button>
        </div>`;
}

// ===== COMPONENTS =====
function movieCardHtml(m) {
    return `<div class="movie-card" onclick="openMovie(${m.id})" style="animation-delay:${Math.random()*0.15}s">
        <img src="${m.poster || `https://placehold.co/500x750/1a1a2e/a5b4fc?text=${encodeURIComponent(m.title?.substring(0,15))}`}" alt="${m.title}" loading="lazy" onerror="this.src='https://placehold.co/500x750/1a1a2e/a5b4fc?text=Movie'">
        <div class="card-info"><div class="card-title">${m.title}</div><div class="card-meta"><span class="card-rating">⭐ ${m.rating}</span><span>${m.year}</span></div></div>
    </div>`;
}

function loadingCards(n) {
    return Array(n).fill(`<div><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-text"></div></div>`).join('');
}

function emptyState(icon, text) {
    return `<div class="empty-state"><div class="empty-icon">${icon}</div><div class="empty-text">${text}</div></div>`;
}

// ===== EVENT BINDING =====
function bindEvents() {
    // Login
    document.getElementById('loginBtn')?.addEventListener('click', handleLogin);
    document.getElementById('loginPass')?.addEventListener('keydown', e => { if (e.key === 'Enter') handleLogin(); });
    document.getElementById('regBtn')?.addEventListener('click', handleRegister);
    document.getElementById('forgotLookupBtn')?.addEventListener('click', handleForgotLookup);
    document.getElementById('forgotResetBtn')?.addEventListener('click', handleForgotReset);

    // Search
    document.getElementById('searchBtn')?.addEventListener('click', handleSearch);
    document.getElementById('searchInput')?.addEventListener('keydown', e => { if (e.key === 'Enter') handleSearch(); });

    // Load data based on page
    if (S.page === 'home') loadHome();
    if (S.page === 'search') loadSearch();
    if (S.page === 'detail') loadDetail();
    if (S.page === 'watchlist') loadWatchlist();
    if (S.page === 'liked') loadLiked();
    if (S.page === 'insights') loadInsights();
    if (S.page === 'admin') loadAdmin();
}

// ===== AUTH HANDLERS =====
async function handleLogin() {
    const u = document.getElementById('loginUser')?.value?.trim();
    const p = document.getElementById('loginPass')?.value;
    if (!u || !p) return toast('Fill all fields', 'error');
    const res = await api('login', { method: 'POST', body: { username: u, password: p } });
    if (res.success) {
        S.user = res.username; S.role = res.role;
        localStorage.setItem('cm_user', JSON.stringify({ user: S.user, role: S.role }));
        navigate('splash');
        setTimeout(() => navigate('home'), 2500);
    } else toast(res.message, 'error');
}

async function handleRegister() {
    const u = document.getElementById('regUser')?.value?.trim();
    const p = document.getElementById('regPass')?.value;
    const sq = document.getElementById('regQuestion')?.value;
    const sa = document.getElementById('regAnswer')?.value;
    if (!u || !p || !sa) return toast('Fill all fields', 'error');
    const res = await api('register', { method: 'POST', body: { username: u, password: p, security_question: sq, security_answer: sa } });
    if (res.success) { toast('Account created! Sign in now.'); switchTab('login'); }
    else toast(res.message, 'error');
}

async function handleForgotLookup() {
    const u = document.getElementById('forgotUser')?.value?.trim();
    if (!u) return toast('Enter username', 'error');
    const res = await api(`security-question/${u}`);
    if (!res.found) return toast('Username not found', 'error');
    if (!res.has_question) return toast('No security question set for this account', 'error');
    document.getElementById('forgotQuestion').textContent = `❓ ${res.question}`;
    document.getElementById('forgotFields').style.display = 'block';
}

async function handleForgotReset() {
    const u = document.getElementById('forgotUser')?.value?.trim();
    const ans = document.getElementById('forgotAns')?.value;
    const np = document.getElementById('forgotNewPass')?.value;
    if (!u || !ans || !np) return toast('Fill all fields', 'error');
    const res = await api('forgot-password', { method: 'POST', body: { username: u, answer: ans, new_password: np } });
    if (res.success) { toast('Password reset! Sign in now.'); switchTab('login'); }
    else toast(res.message, 'error');
}

function switchTab(name) {
    document.querySelectorAll('.tab-btn').forEach((b, i) => {
        const tabs = ['login', 'register', 'forgot'];
        b.classList.toggle('active', tabs[i] === name);
    });
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${name}`)?.classList.add('active');
}

function logout() {
    S.user = null; S.role = null;
    localStorage.removeItem('cm_user');
    navigate('login');
}

// ===== SEARCH =====
function handleSearch() {
    const q = document.getElementById('searchInput')?.value?.trim();
    if (!q) return;
    navigate('search', { searchQuery: q, searchType: 'movie' });
}

// ===== MOVIE ACTIONS =====
async function openMovie(id) {
    S.detailData = null; S.detailId = id;
    navigate('detail');
}

function goBack() {
    if (S.page === 'detail') navigate('home');
    else navigate('home');
}

async function addWatchlist(title) {
    const res = await api('watchlist', { method: 'POST', body: { username: S.user, movie: title } });
    toast(res.message || (res.success ? '❤️ Added to Watchlist!' : 'Already saved'));
}

async function addLike(title) {
    const res = await api('liked', { method: 'POST', body: { username: S.user, movie: title } });
    toast(res.message || '👍 Liked!');
}

async function submitReview(title) {
    const rating = document.getElementById('reviewRating')?.value || 8;
    const text = document.getElementById('reviewText')?.value?.trim();
    if (!text) return toast('Write a review first', 'error');
    const res = await api('review', { method: 'POST', body: { username: S.user, movie: title, rating: parseInt(rating), review: text } });
    if (res.success) {
        toast(`Review posted! Sentiment: ${res.sentiment}`);
        document.getElementById('reviewText').value = '';
        loadReviews(title);
    }
}

// ===== DATA LOADERS =====
async function loadHome() {
    const grid = document.getElementById('movieGrid');
    try {
        const movies = await api('movies/top');
        grid.innerHTML = movies.length ? movies.map(movieCardHtml).join('') : emptyState('🎬', 'No movies found');
    } catch { grid.innerHTML = emptyState('⚠️', 'Failed to load movies'); }
}

async function loadSearch() {
    const grid = document.getElementById('movieGrid');
    try {
        const movies = await api(`movies/search?q=${encodeURIComponent(S.searchQuery)}&type=${S.searchType}`);
        grid.innerHTML = movies.length ? movies.map(movieCardHtml).join('') : emptyState('🔍', 'No results found');
    } catch { grid.innerHTML = emptyState('⚠️', 'Search failed'); }
}

async function loadDetail() {
    try {
        const m = await api(`movies/${S.detailId}`);
        S.detailData = m;
        // Add to recently viewed
        S.recentlyViewed = S.recentlyViewed.filter(r => r.id !== m.id);
        S.recentlyViewed.unshift({ id: m.id, title: m.title });
        S.recentlyViewed = S.recentlyViewed.slice(0, 10);
        localStorage.setItem('cm_recent', JSON.stringify(S.recentlyViewed));
        // Re-render with data
        document.getElementById('content').innerHTML = detailPage();
        // Load reviews & recommendations
        loadReviews(m.title);
        loadRecommendations(m.id);
    } catch { document.getElementById('content').innerHTML = emptyState('⚠️', 'Failed to load movie'); }
}

async function loadReviews(title) {
    const container = document.getElementById('reviewsList');
    if (!container) return;
    try {
        const reviews = await api(`reviews/${encodeURIComponent(title)}`);
        if (!reviews.length) { container.innerHTML = `<p style="padding:0 20px;color:var(--text-muted);font-size:0.85rem">No reviews yet. Be the first!</p>`; return; }
        container.innerHTML = reviews.map(r => {
            const sentClass = r.sentiment === 'Positive' ? 'positive' : r.sentiment === 'Negative' ? 'negative' : 'neutral';
            const sentEmoji = r.sentiment === 'Positive' ? '😊' : r.sentiment === 'Negative' ? '😞' : '😐';
            return `<div class="review-card"><div class="review-header"><span class="review-user">${r.username}</span><span class="review-sentiment ${sentClass}">${sentEmoji} ${r.sentiment} (${r.confidence}%)</span></div><div class="review-text">"${r.review}"</div></div>`;
        }).join('');
    } catch { container.innerHTML = ''; }
}

async function loadRecommendations(id) {
    const grid = document.getElementById('recGrid');
    if (!grid) return;
    try {
        const movies = await api(`movies/${id}/recommend`);
        grid.innerHTML = movies.length ? movies.map(movieCardHtml).join('') : emptyState('🎬', 'No recommendations');
    } catch { grid.innerHTML = ''; }
}

async function loadWatchlist() {
    const grid = document.getElementById('movieGrid');
    try {
        const movies = await api(`watchlist?username=${S.user}`);
        grid.innerHTML = movies.length ? movies.map(movieCardHtml).join('') : emptyState('❤️', 'Your watchlist is empty. Save movies to see them here!');
    } catch { grid.innerHTML = emptyState('⚠️', 'Failed to load'); }
}

async function loadLiked() {
    const grid = document.getElementById('movieGrid');
    try {
        const movies = await api(`liked?username=${S.user}`);
        grid.innerHTML = movies.length ? movies.map(movieCardHtml).join('') : emptyState('👍', 'No liked movies yet. Like movies to see them here!');
    } catch { grid.innerHTML = emptyState('⚠️', 'Failed to load'); }
}

// ===== ML INSIGHTS LOADERS =====
async function loadInsights() {
    // Model stats
    try {
        const stats = await api('ml/stats');
        const cardsEl = document.getElementById('insightCards');
        cardsEl.innerHTML = `
            <div class="insight-card"><div class="status">${stats.sentiment_model_exists ? '🟢' : '🔴'}</div><div class="value">${stats.sentiment_model_exists ? 'Active' : 'Inactive'}</div><div class="label">Sentiment Model</div></div>
            <div class="insight-card"><div class="status">${stats.rating_model_exists ? '🟢' : '🔴'}</div><div class="value">${stats.rating_model_exists ? 'Active' : 'Inactive'}</div><div class="label">Rating Predictor</div></div>
            <div class="insight-card"><div class="status">🟢</div><div class="value">Active</div><div class="label">TF-IDF Engine</div></div>`;
    } catch {}
    // Top Directors
    try {
        const dirs = await api('ml/top-directors');
        const container = document.getElementById('directorsChart');
        if (dirs.length) {
            const max = Math.max(...dirs.map(d => d.avg_rating));
            container.innerHTML = `<div class="bar-chart">${dirs.map(d => `<div class="bar-row"><div class="bar-label">${d.director}</div><div class="bar-track"><div class="bar-fill" style="width:${(d.avg_rating/max*100).toFixed(0)}%"><span class="bar-value">${d.avg_rating}</span></div></div></div>`).join('')}</div>`;
        } else container.innerHTML = emptyState('🎬', 'Not enough data');
    } catch {}
    // Feature Importance
    try {
        const fi = await api('ml/feature-importance');
        const container = document.getElementById('factorsChart');
        const entries = Object.entries(fi);
        if (entries.length) {
            const max = Math.max(...entries.map(e => e[1]));
            container.innerHTML = `<div class="bar-chart">${entries.map(([k, v]) => `<div class="bar-row"><div class="bar-label">${k}</div><div class="bar-track"><div class="bar-fill" style="width:${(v/max*100).toFixed(0)}%;background:linear-gradient(90deg,#f093fb,#764ba2)"><span class="bar-value">${v}%</span></div></div></div>`).join('')}</div>`;
        } else container.innerHTML = emptyState('🎯', 'Train models to see factors');
    } catch {}
    // Sentiment Distribution
    try {
        const sd = await api('ml/sentiment-distribution');
        const container = document.getElementById('sentimentChart');
        const entries = Object.entries(sd);
        if (entries.length) {
            const total = entries.reduce((s, e) => s + e[1], 0);
            const colors = { Positive: 'var(--success)', Negative: 'var(--error)', Neutral: 'var(--warning)' };
            container.innerHTML = `<div class="bar-chart">${entries.map(([k, v]) => `<div class="bar-row"><div class="bar-label">${k}</div><div class="bar-track"><div class="bar-fill" style="width:${(v/total*100).toFixed(0)}%;background:${colors[k] || 'var(--accent)'}"><span class="bar-value">${v}</span></div></div></div>`).join('')}</div>`;
        } else container.innerHTML = emptyState('💬', 'No reviews yet');
    } catch {}
}

async function analyzeSentiment() {
    const text = document.getElementById('sentimentInput')?.value?.trim();
    if (!text) return toast('Enter some text first', 'error');
    const container = document.getElementById('sentimentResult');
    container.innerHTML = `<div class="loading-container"><div class="spinner"></div></div>`;
    try {
        const res = await api('ml/sentiment', { method: 'POST', body: { text } });
        const emoji = res.sentiment === 'Positive' ? '😊' : res.sentiment === 'Negative' ? '😞' : '😐';
        const color = res.sentiment === 'Positive' ? 'var(--success)' : res.sentiment === 'Negative' ? 'var(--error)' : 'var(--warning)';
        container.innerHTML = `<div class="sentiment-result">
            <div class="sentiment-header"><div class="sentiment-emoji">${emoji}</div><div><div class="sentiment-label" style="color:${color}">${res.sentiment}</div><div style="font-size:0.8rem;color:var(--text-secondary)">Confidence: ${res.confidence}%</div></div></div>
            <div class="sentiment-bars"><div class="sentiment-bar pos"><div class="sbar-label" style="color:var(--success)">Positive</div><div class="sbar-value">${res.positive_prob}%</div></div><div class="sentiment-bar neg"><div class="sbar-label" style="color:var(--error)">Negative</div><div class="sbar-value">${res.negative_prob}%</div></div></div>
        </div>`;
    } catch { container.innerHTML = emptyState('⚠️', 'Analysis failed'); }
}

// ===== ADMIN LOADERS =====
async function loadAdmin() {
    try {
        const stats = await api('admin/stats');
        document.getElementById('adminMetrics').innerHTML = `
            <div class="metric-card"><div class="metric-value">${stats.total_likes}</div><div class="metric-label">Total Likes</div></div>
            <div class="metric-card"><div class="metric-value">${stats.total_watchlist}</div><div class="metric-label">Watchlist</div></div>
            <div class="metric-card"><div class="metric-value">${stats.total_reviews}</div><div class="metric-label">Reviews</div></div>`;
        const topLiked = document.getElementById('topLiked');
        const entries = Object.entries(stats.top_liked || {});
        if (entries.length) {
            const max = Math.max(...entries.map(e => e[1]));
            topLiked.innerHTML = `<div class="bar-chart">${entries.map(([k, v]) => `<div class="bar-row"><div class="bar-label">${k}</div><div class="bar-track"><div class="bar-fill" style="width:${(v/max*100).toFixed(0)}%"><span class="bar-value">${v}</span></div></div></div>`).join('')}</div>`;
        } else topLiked.innerHTML = emptyState('📊', 'No data yet');

        const users = await api('admin/users');
        const sel = document.getElementById('adminUserSelect');
        sel.innerHTML = users.map(u => `<option value="${u}">${u}</option>`).join('');
    } catch {}
}

async function adminResetPassword() {
    const u = document.getElementById('adminUserSelect')?.value;
    const p = document.getElementById('adminNewPass')?.value;
    if (!u || !p) return toast('Fill all fields', 'error');
    const res = await api('admin/reset-password', { method: 'POST', body: { username: u, new_password: p } });
    if (res.success) { toast(`Password reset for ${u}`); document.getElementById('adminNewPass').value = ''; }
    else toast(res.message, 'error');
}

// ===== INIT =====
(function init() {
    // Check saved session
    const saved = JSON.parse(localStorage.getItem('cm_user') || 'null');
    if (saved && saved.user) {
        S.user = saved.user;
        S.role = saved.role;
        navigate('home');
    } else {
        navigate('login');
    }

    // Register Service Worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
})();
