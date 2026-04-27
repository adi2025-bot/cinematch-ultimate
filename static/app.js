/**
 * CineMatch Mobile — Single Page Application
 * Premium movie recommendation PWA — Full Feature Parity with Desktop
 */

// ===== STATE =====
const S = {
    user: null, role: null, page: 'login',
    detailData: null, detailId: null,
    searchQuery: '', searchType: 'movie',
    filterGenre: '', filterYear: 0, filterRating: 0,
    recentlyViewed: JSON.parse(localStorage.getItem('cm_recent') || '[]'),
    genreList: [],
    trailerPlaying: false,
    suggestTimer: null,
    // Audio/Songs state
    currentSong: null,
    audioPlaying: false,
    // Navigation history stack
    navHistory: [],
};

// Global audio element — persists across page navigations
const cmAudio = new Audio();
cmAudio.addEventListener('ended', () => { S.audioPlaying = false; updateMiniPlayer(); });
cmAudio.addEventListener('timeupdate', updateAudioProgress);

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
function navigate(page, params = {}, skipHistory = false) {
    // Push current page to history before navigating (skip for login/splash/back)
    if (!skipHistory && S.page && S.page !== 'login' && S.page !== 'splash' && S.page !== page) {
        S.navHistory.push({
            page: S.page, searchQuery: S.searchQuery, searchType: S.searchType,
            filterGenre: S.filterGenre, detailId: S.detailId, detailData: S.detailData
        });
        // Keep history stack manageable
        if (S.navHistory.length > 20) S.navHistory.shift();
    }
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
        case 'actor': html = appShell(actorPage); break;
        case 'watchlist': html = appShell(watchlistPage); break;
        case 'liked': html = appShell(likedPage); break;
        case 'recently': html = appShell(recentPage); break;
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
            <div class="top-bar-logo animated-logo">CINEMATCH</div>
            <div class="top-bar-user">👤 ${S.user}</div>
        </div>
        ${S.page === 'search' ? `
        <div class="search-bar" style="flex-wrap:wrap; gap:8px;">
            <div class="search-input-wrapper">
                <input class="search-input" id="searchInput" placeholder="Search..." value="${(S.searchQuery || '').replace(/"/g,'&quot;')}" autocomplete="off">
                <div class="search-suggestions" id="searchSuggestions"></div>
            </div>
            <select id="searchTypeSel" class="form-select" style="width:110px; padding:12px; border-radius:12px; background:var(--bg-deep); color:white; border:1px solid var(--border);">
                <option value="movie" ${S.searchType==='movie'?'selected':''}>Title</option>
                <option value="actor" ${S.searchType==='actor'?'selected':''}>Actor</option>
                <option value="director" ${S.searchType==='director'?'selected':''}>Director</option>
            </select>
            <button class="search-btn" id="searchBtn">🔍 Go</button>
        </div>` : `
        <div class="search-bar">
            <div class="search-input-wrapper">
                <input class="search-input" id="searchInput" placeholder="Search movies, actors, directors..." value="${(S.searchQuery || '').replace(/"/g,'&quot;')}" autocomplete="off">
                <div class="search-suggestions" id="searchSuggestions"></div>
            </div>
            <button class="search-btn" id="searchBtn">🔍 Go</button>
        </div>`}
        <div id="content">${contentFn()}</div>
        ${miniPlayerHtml()}
        <div class="bottom-nav">
            <button class="nav-btn ${S.page === 'home' ? 'active' : ''}" onclick="navigate('home')"><span class="nav-icon">🏠</span>Home</button>
            <button class="nav-btn ${S.page === 'recently' ? 'active' : ''}" onclick="navigate('recently')"><span class="nav-icon">🕐</span>Recent</button>
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
    return `<div id="genreContainer"></div>
    <div class="section-title">🏆 Top Rated</div><div id="movieGrid" class="movie-grid">${loadingCards(12)}</div>`;
}

// ===== SEARCH PAGE =====
function searchPage() {
    let subtitle = S.searchQuery ? `"${S.searchQuery}"` : '';
    if (S.filterGenre) subtitle = `Genre: ${S.filterGenre}`;
    
    let extraSearch = '';
    if (S.filterGenre === 'Adult') {
        extraSearch = `
        <div class="search-bar" style="margin: 0 20px 16px; width: auto; max-width: none;">
            <div class="search-input-wrapper">
                <input class="search-input" id="adultSpecificSearch" placeholder="Search adult movies..." value="${(S.searchQuery || '').replace(/"/g,'&quot;')}" autocomplete="off" oninput="handleAdultSearchInput(event)">
                <div class="search-suggestions" id="adultSearchSuggestions"></div>
            </div>
            <button class="search-btn" onclick="S.searchQuery=document.getElementById('adultSpecificSearch').value.trim(); S.searchPage=1; loadSearch(1); hideAdultSuggestions();">🔍 Search</button>
        </div>`;
    }

    return `<div class="section-title" style="display:flex; justify-content:space-between; align-items:center;">
        <div>🔍 ${subtitle || 'All Movies'}</div>
        <button class="nav-btn" style="background:var(--bg-mid); padding:8px 16px; border-radius:12px; color:white; border:1px solid var(--border)" onclick="navigate('home')">⬅ Back</button>
    </div>
    ${extraSearch}
    <div id="movieGrid" class="movie-grid">${loadingCards(9)}</div>
    <div id="loadMoreContainer" style="text-align:center; padding: 0px 20px 80px; display:none; margin-top: -5px;">
        <button class="btn" style="background-color: #e50914; color: white; border: none; padding: 12px 30px; font-weight: bold; font-size: 1rem; border-radius: 6px; box-shadow: 0 4px 12px rgba(229, 9, 20, 0.4); text-transform: uppercase; letter-spacing: 1px;" onclick="S.searchPage=(S.searchPage||1)+1; loadSearch(S.searchPage)">Load More Movies</button>
    </div>`;
}

// ===== WATCHLIST PAGE =====
function watchlistPage() {
    return `<div class="section-title">❤️ My Watchlist</div><div id="movieGrid" class="movie-grid">${loadingCards(6)}</div>`;
}

// ===== LIKED PAGE =====
function likedPage() {
    return `<div class="section-title">👍 Liked Movies</div><div id="movieGrid" class="movie-grid">${loadingCards(6)}</div>`;
}

// ===== RECENTLY VIEWED PAGE =====
function recentPage() {
    return `<div class="section-title">🕐 Recently Viewed</div><div id="movieGrid" class="movie-grid">${loadingCards(6)}</div>`;
}

// ===== DETAIL PAGE =====
function detailPage() {
    if (!S.detailData) return `<div class="loading-container"><div class="spinner"></div><p style="color:var(--text-muted)">Loading movie details...</p></div>`;
    const m = S.detailData;
    const rt = m.runtime ? `${Math.floor(m.runtime/60)}h ${m.runtime%60}m` : 'N/A';
    let budgetStr = 'N/A';
    if (m.budget > 0) {
        budgetStr = `$${(m.budget/1000000).toFixed(1)}M / ₹${((m.budget * 83) / 10000000).toFixed(1)}Cr`;
    }
    
    let revStr = 'N/A';
    if (m.revenue > 0) {
        revStr = `$${(m.revenue/1000000).toFixed(1)}M / ₹${((m.revenue * 83) / 10000000).toFixed(1)}Cr`;
    }
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
    const castList = m.cast_rich && m.cast_rich.length ? m.cast_rich : (m.cast || []).map(n => ({ name: n, photo: `https://placehold.co/120x160/1a1a2e/a5b4fc?text=${encodeURIComponent(n.split(' ')[0])}` }));
    if (castList.length) {
        castHtml = `<div class="detail-section"><div class="detail-section-title"><b>🎭 Top Cast</b></div></div><div class="cast-scroll">${castList.map(c => `<div class="cast-card" onclick="openActorProfile('${c.name.replace(/'/g,"\\'")}', ${c.id || 0})"><img src="${c.photo}" alt="${c.name}" loading="lazy"><div class="cast-card-name">${c.name}</div></div>`).join('')}</div>`;
    }

    // Trailer: thumbnail first, click to play
    let trailerHtml = '';
    if (m.trailer) {
        if (S.trailerPlaying) {
            trailerHtml = `<div class="detail-section"><div class="detail-section-title"><b>🎬 Trailer</b></div></div><div class="trailer-frame"><iframe src="https://www.youtube-nocookie.com/embed/${m.trailer}?autoplay=1" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>`;
        } else {
            trailerHtml = `<div class="detail-section"><div class="detail-section-title"><b>🎬 Trailer</b></div></div>
            <div class="trailer-thumb" onclick="playTrailer()">
                <img src="https://img.youtube.com/vi/${m.trailer}/hqdefault.jpg" alt="Trailer" onerror="this.src='https://img.youtube.com/vi/${m.trailer}/default.jpg'">
                <div class="trailer-play-btn"><div class="trailer-play-icon"></div></div>
            </div>
            <div style="padding:8px 20px"><button class="btn btn-secondary btn-sm" onclick="playTrailer()">▶ Play Trailer</button></div>`;
        }
    } else {
        trailerHtml = `<div style="padding:0 20px"><a href="https://www.youtube.com/results?search_query=${encodeURIComponent(m.title)}+trailer" target="_blank" class="btn btn-secondary" style="margin-bottom:16px">🔎 Search Trailer on YouTube</a></div>`;
    }

    let providersHtml = '';
    if (m.providers && m.providers.length) {
        providersHtml = `<div class="detail-section"><div class="detail-section-title"><b>📺 Where to Watch</b></div></div><div class="provider-row">${m.providers.map(p => `<img src="${p.logo}" title="${p.name}" class="provider-logo" loading="lazy">`).join('')}</div>`;
    }

    const escTitle = m.title.replace(/'/g, "\\'");
    const shareUrl = encodeURIComponent(window.location.origin + `?movie=${m.id}`);
    const shareText = encodeURIComponent(`Check out ${m.title} on CineMatch!`);

    // Director clickable
    const dirHtml = m.director && m.director !== 'Unknown'
        ? `<span class="info-value clickable" onclick="navigate('search',{searchQuery:'${m.director.replace(/'/g,"\\'")}',searchType:'director'})">${m.director}</span>`
        : `<span class="info-value">${m.director || 'Unknown'}</span>`;

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
        <div class="detail-section"><div class="detail-section-title"><b>📖 Overview</b></div><p class="overview-text">${m.overview}</p></div>
        <div class="action-row">
            <button class="action-btn" id="watchlistBtn" onclick="addWatchlist('${escTitle}')">❤️ Watchlist</button>
            <button class="action-btn" id="likeBtn" onclick="addLike('${escTitle}')">👍 Like</button>
        </div>
        <div class="detail-section"><div class="detail-section-title"><b>📤 Share</b></div></div>
        <div class="share-row">
            <a href="https://wa.me/?text=${shareText}%20${shareUrl}" target="_blank" class="share-btn share-wa"><svg viewBox="0 0 24 24" width="22" height="22" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg></a>
            <a href="https://twitter.com/intent/tweet?text=${shareText}&url=${shareUrl}" target="_blank" class="share-btn share-tw"><svg viewBox="0 0 24 24" width="20" height="20" fill="white"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
            <a href="https://www.instagram.com/" target="_blank" class="share-btn share-ig"><svg viewBox="0 0 24 24" width="20" height="20" fill="white"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg></a>
        </div>
        ${castHtml}
        ${trailerHtml}
        <div class="detail-section" id="songsTitleSection"><div class="detail-section-title"><b>🎵 Movie Songs</b></div></div>
        <div id="songsContainer"><div class="loading-container" style="padding:20px"><div class="spinner"></div><p style="color:var(--text-muted);font-size:0.85rem">Loading songs...</p></div></div>
        <div class="info-box">
            <div class="info-row"><span class="info-label">Director</span>${dirHtml}</div>
            <div class="info-row"><span class="info-label">Budget</span><span class="info-value">${budgetStr}</span></div>
            <div class="info-row"><span class="info-label">Revenue</span><span class="info-value">${revStr}</span></div>
            <div class="info-row"><span class="info-label">Genres</span><span class="info-value">${(m.genres_list || []).join(', ') || m.genres}</span></div>
        </div>
        ${providersHtml}
        <div class="detail-section"><div class="detail-section-title"><b>✍️ Rate & Review</b></div></div>
        <div style="padding:0 20px 16px">
            <div class="form-group"><label class="form-label">Your Rating: <span id="ratingVal">8</span>/10</label><input type="range" min="1" max="10" value="8" id="reviewRating" style="width:100%;accent-color:var(--accent)" oninput="document.getElementById('ratingVal').textContent=this.value"></div>
            <div class="form-group"><textarea class="form-textarea" id="reviewText" placeholder="Share your thoughts about this movie..."></textarea></div>
            <button class="btn btn-primary btn-sm" id="submitReviewBtn" onclick="submitReview('${escTitle}')">Submit Review</button>
        </div>
        <div class="detail-section"><div class="detail-section-title"><b>📰 User Reviews</b></div></div>
        <div id="reviewsList"><div class="loading-container"><div class="spinner"></div></div></div>
        <div class="detail-section"><div class="detail-section-title"><b>🎬 Similar Movies</b></div></div>
        <div id="recGrid" class="movie-grid" style="padding-bottom:120px">${loadingCards(6)}</div>
    </div>`;
}

// ===== ACTOR PROFILE PAGE =====
function actorPage() {
    if (!S.actorData) return `<div class="loading-container"><div class="spinner"></div><p style="color:var(--text-muted)">Loading actor details...</p></div>`;
    const a = S.actorData;
    const age = a.birthday ? (() => {
        const bd = new Date(a.birthday);
        const end = a.deathday ? new Date(a.deathday) : new Date();
        return Math.floor((end - bd) / 31557600000);
    })() : null;
    const bioShort = a.biography && a.biography.length > 400 ? a.biography.substring(0, 400) + '...' : a.biography;

    return `<div class="detail-page">
        <div class="detail-back"><button class="btn btn-secondary btn-sm" onclick="goBack()">← Back</button></div>
        <div class="actor-hero">
            ${a.photo ? `<img src="${a.photo}" alt="${a.name}" class="actor-hero-photo">` : `<div class="actor-hero-photo" style="background:var(--bg-card);display:flex;align-items:center;justify-content:center;font-size:3rem">👤</div>`}
            <div class="actor-hero-info">
                <div class="hero-title">${a.name}</div>
                <div class="stat-pills">
                    <span class="stat-pill highlight">${a.known_for}</span>
                    ${a.gender !== 'Unknown' ? `<span class="stat-pill">${a.gender}</span>` : ''}
                    ${age ? `<span class="stat-pill">🎂 ${age} yrs</span>` : ''}
                    <span class="stat-pill">🎬 ${a.total_movies} films</span>
                </div>
            </div>
        </div>
        <div class="detail-section"><div class="detail-section-title"><b>📖 Biography</b></div>
            <p class="overview-text" id="actorBioText">${bioShort || 'No biography available.'}</p>
            ${a.biography && a.biography.length > 400 ? `<button class="btn btn-secondary btn-sm" style="margin:8px 0;width:auto;padding:6px 16px" onclick="document.getElementById('actorBioText').textContent=S.actorData.biography; this.remove()">Read More</button>` : ''}
        </div>
        <div class="info-box">
            ${a.birthday ? `<div class="info-row"><span class="info-label">Born</span><span class="info-value">${a.birthday}${a.deathday ? '' : ` (Age ${age})`}</span></div>` : ''}
            ${a.deathday ? `<div class="info-row"><span class="info-label">Died</span><span class="info-value">${a.deathday} (Age ${age})</span></div>` : ''}
            ${a.birthplace ? `<div class="info-row"><span class="info-label">Birthplace</span><span class="info-value">${a.birthplace}</span></div>` : ''}
            <div class="info-row"><span class="info-label">Popularity</span><span class="info-value">⭐ ${a.popularity}</span></div>
            <div class="info-row"><span class="info-label">Total Films</span><span class="info-value">${a.total_movies}</span></div>
        </div>
        <div class="detail-section"><div class="detail-section-title"><b>🎬 Known For</b></div></div>
        <div id="actorMoviesGrid" class="movie-grid" style="padding-bottom:120px">${a.movies && a.movies.length ? a.movies.map(movieCardHtml).join('') : emptyState('🎬', 'No filmography found')}</div>
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
        <div class="section-title">📊 Genre Popularity Over Decades</div>
        <div id="genreDecadesChart"><div class="loading-container"><div class="spinner"></div></div></div>
        <div class="section-title">👤 Your Taste Profile</div>
        <div id="tasteProfile"><div class="loading-container"><div class="spinner"></div></div></div>
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
    const borders = ['#ec4899', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'];
    const bColor = borders[(m.id || 0) % borders.length];
    
    return `<div class="movie-card" onclick="openMovie(${m.id})" style="animation-delay:${Math.random()*0.15}s; border: 2px solid ${bColor}80; box-shadow: 0 4px 15px ${bColor}20;">
        <img src="${m.poster || `https://placehold.co/500x750/1a1a2e/a5b4fc?text=${encodeURIComponent((m.title||'Movie').substring(0,15))}`}" alt="${m.title}" loading="lazy" onerror="this.src='https://placehold.co/500x750/1a1a2e/a5b4fc?text=Movie'">
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
    document.getElementById('searchBtn')?.addEventListener('click', () => { hideSuggestions(); handleSearch(); });
    document.getElementById('searchInput')?.addEventListener('keydown', e => { if (e.key === 'Enter') { hideSuggestions(); handleSearch(); } });
    document.getElementById('searchInput')?.addEventListener('input', handleSearchInput);
    // Dismiss suggestions on outside tap
    document.addEventListener('click', e => {
        if (!e.target.closest('.search-input-wrapper')) {
            hideSuggestions();
            hideAdultSuggestions();
        }
    });

    // Load data based on page
    if (S.page === 'home') loadHome();
    if (S.page === 'search') loadSearch();
    if (S.page === 'detail') loadDetail();
    if (S.page === 'watchlist') loadWatchlist();
    if (S.page === 'liked') loadLiked();
    if (S.page === 'recently') loadRecent();
    if (S.page === 'insights') loadInsights();
    if (S.page === 'admin') loadAdmin();
    if (S.page === 'actor') loadActorProfile();
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
    if (S.user) {
        localStorage.removeItem(`cm_adult_verified_${S.user}`);
    }
    S.user = null; S.role = null;
    localStorage.removeItem('cm_user');
    navigate('login');
}

// ===== SEARCH & FILTERS =====
function handleSearch() {
    const q = document.getElementById('searchInput')?.value?.trim() || '';
    const t = document.getElementById('searchTypeSel')?.value || S.searchType || 'movie';
    if (!q && !S.filterGenre) return toast('Enter a search query', 'error');
    S.filterGenre = ''; // Clear genre filter when doing text search
    navigate('search', { searchQuery: q, searchType: t });
}

function filterByGenre(g) {
    if (g === 'Adult' || g === '🔞 Adult') {
        if (localStorage.getItem(`cm_adult_verified_${S.user}`) === 'true') {
            executeGenreFilter('Adult');
            return;
        }
        showAgeVerificationModal();
        return;
    }
    executeGenreFilter(g);
}

function executeGenreFilter(g) {
    S.filterGenre = g;
    S.searchQuery = '';
    navigate('search');
}

function showAgeVerificationModal() {
    if (document.getElementById('ageVerifyOverlay')) return;
    
    const curYear = new Date().getFullYear();
    let yearOpts = '<option value="" disabled selected>Year</option>';
    for(let y=curYear; y>=1920; y--) yearOpts += `<option value="${y}">${y}</option>`;
    
    let monthOpts = '<option value="" disabled selected>Month</option>';
    const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    months.forEach((m, i) => monthOpts += `<option value="${i}">${m}</option>`);
    
    let dayOpts = '<option value="" disabled selected>Day</option>';
    for(let d=1; d<=31; d++) dayOpts += `<option value="${d}">${d}</option>`;

    const html = `
    <div id="ageVerifyOverlay" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); backdrop-filter:blur(5px); z-index:9999; display:flex; justify-content:center; align-items:center; opacity:0; transition:opacity 0.3s ease;">
        <div style="background:#ffffff; width:90%; max-width:420px; aspect-ratio: 1 / 1; border-radius:50%; display:flex; flex-direction:column; justify-content:center; align-items:center; box-shadow:20px 20px 60px rgba(0,0,0,0.5), inset -10px -10px 20px rgba(0,0,0,0.05); text-align:center; transform:scale(0.8) translateY(20px); transition:all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); color:#333; position:relative; padding:20px;">
            
            <div style="font-size:4.5rem; font-weight:bold; color:#e74c3c; line-height:1; margin-bottom:10px; text-shadow:2px 4px 10px rgba(231,76,60,0.3);">?</div>
            
            <h2 style="margin:0 0 5px; font-size:1.6rem; color:#2c3e50; font-weight:700;">Are you over 18 years old?</h2>
            <p style="margin:0 0 15px; color:#7f8c8d; font-size:0.9rem;">Please enter your date of birth</p>
            
            <div style="display:flex; gap:8px; justify-content:center; margin-bottom:15px; width:80%;">
                <select id="avDay" style="padding:8px; border-radius:6px; border:1px solid #ddd; background:#f9f9f9; flex:1; outline:none;">${dayOpts}</select>
                <select id="avMonth" style="padding:8px; border-radius:6px; border:1px solid #ddd; background:#f9f9f9; flex:1.5; outline:none;">${monthOpts}</select>
                <select id="avYear" style="padding:8px; border-radius:6px; border:1px solid #ddd; background:#f9f9f9; flex:1.2; outline:none;">${yearOpts}</select>
            </div>
            
            <label style="display:flex; align-items:center; gap:8px; font-size:0.85rem; color:#555; margin-bottom:20px; cursor:pointer;">
                <input type="checkbox" id="avTerms" style="width:16px; height:16px; accent-color:#3498db;">
                I agree with <span style="color:#3498db;">Terms & Condition</span>
            </label>
            
            <div style="display:flex; gap:15px; width:70%; justify-content:center;">
                <button onclick="verifyAgeSubmit()" style="background:#8cc152; color:white; border:none; padding:10px 0; width:50%; border-radius:25px; font-weight:600; font-size:1rem; cursor:pointer; box-shadow:0 4px 10px rgba(140,193,82,0.4); transition:transform 0.2s;">Confirm</button>
                <button onclick="document.getElementById('ageVerifyOverlay').style.opacity='0'; setTimeout(()=>document.getElementById('ageVerifyOverlay').remove(), 300);" style="background:#95a5a6; color:white; border:none; padding:10px 0; width:50%; border-radius:25px; font-weight:600; font-size:1rem; cursor:pointer; box-shadow:0 4px 10px rgba(149,165,166,0.4); transition:transform 0.2s;">Exit</button>
            </div>
        </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', html);
    
    setTimeout(() => {
        const overlay = document.getElementById('ageVerifyOverlay');
        if (overlay) {
            overlay.style.opacity = '1';
            overlay.children[0].style.transform = 'scale(1) translateY(0)';
        }
    }, 20);
}

window.verifyAgeSubmit = function() {
    const d = document.getElementById('avDay').value;
    const m = document.getElementById('avMonth').value;
    const y = document.getElementById('avYear').value;
    const terms = document.getElementById('avTerms').checked;
    
    if (!d || !m || !y) return toast('Please select your complete date of birth.', 'error');
    if (!terms) return toast('You must agree to the Terms & Conditions.', 'error');
    
    const dob = new Date(y, m, d);
    let age = new Date().getFullYear() - dob.getFullYear();
    const mDiff = new Date().getMonth() - dob.getMonth();
    if (mDiff < 0 || (mDiff === 0 && new Date().getDate() < dob.getDate())) {
        age--;
    }
    
    if (age >= 18) {
        localStorage.setItem(`cm_adult_verified_${S.user}`, 'true');
        document.getElementById('ageVerifyOverlay').style.opacity = '0';
        setTimeout(() => {
            document.getElementById('ageVerifyOverlay').remove();
            executeGenreFilter('Adult');
            if (typeof window.hideAdultSuggestions === 'function') {
                window.hideAdultSuggestions(); // clean up if triggered from search
            }
        }, 300);
    } else {
        toast('Sorry, you must be 18 or older to view this content.', 'error');
    }
}

// ===== SEARCH SUGGESTIONS =====
function handleSearchInput(e) {
    const q = e.target.value.trim();
    clearTimeout(S.suggestTimer);
    if (q.length < 2) { hideSuggestions(); return; }
    S.suggestTimer = setTimeout(() => fetchSuggestions(q), 250);
}

async function fetchSuggestions(q) {
    try {
        const results = await api(`movies/suggestions?q=${encodeURIComponent(q)}`);
        showSuggestions(results, q);
    } catch { hideSuggestions(); }
}

function showSuggestions(results, query) {
    const container = document.getElementById('searchSuggestions');
    if (!container || !results.length) { hideSuggestions(); return; }
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    container.innerHTML = results.map(r => {
        const highlighted = r.title.replace(re, '<span class="sg-match">$1</span>');
        return `<div class="sg-item" data-id="${r.id}" data-title="${r.title.replace(/"/g,'&quot;')}">
            <span class="sg-icon">🎬</span>
            <span class="sg-text">${highlighted}</span>
            <span class="sg-arrow">↗</span>
        </div>`;
    }).join('');
    container.classList.add('active');
    // Bind click on each suggestion
    container.querySelectorAll('.sg-item').forEach(item => {
        item.addEventListener('click', () => {
            const id = parseInt(item.dataset.id);
            hideSuggestions();
            openMovie(id);
        });
    });
}

function hideSuggestions() {
    const container = document.getElementById('searchSuggestions');
    if (container) { container.classList.remove('active'); container.innerHTML = ''; }
}

function handleAdultSearchInput(e) {
    const q = e.target.value.trim();
    clearTimeout(S.suggestTimer);
    if (q.length < 2) { hideAdultSuggestions(); return; }
    S.suggestTimer = setTimeout(() => fetchAdultSuggestions(q), 250);
}

async function fetchAdultSuggestions(q) {
    try {
        const results = await api(`movies/suggestions?q=${encodeURIComponent(q)}&genre=Adult`);
        showAdultSuggestions(results, q);
    } catch { hideAdultSuggestions(); }
}

function showAdultSuggestions(results, query) {
    const container = document.getElementById('adultSearchSuggestions');
    if (!container || !results.length) { hideAdultSuggestions(); return; }
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')})`, 'gi');
    container.innerHTML = results.map(r => {
        const highlighted = r.title.replace(re, '<span class="sg-match">$1</span>');
        return `<div class="sg-item" data-id="${r.id}" data-title="${r.title.replace(/"/g,'&quot;')}">
            <span class="sg-icon">🔞</span>
            <span class="sg-text">${highlighted}</span>
            <span class="sg-arrow">↗</span>
        </div>`;
    }).join('');
    container.classList.add('active');
    container.querySelectorAll('.sg-item').forEach(item => {
        item.addEventListener('click', () => {
            const id = parseInt(item.dataset.id);
            hideAdultSuggestions();
            openMovie(id);
        });
    });
}

function hideAdultSuggestions() {
    const container = document.getElementById('adultSearchSuggestions');
    if (container) { container.classList.remove('active'); container.innerHTML = ''; }
}

// ===== TRAILER =====
function playTrailer() {
    S.trailerPlaying = true;
    const content = document.getElementById('content');
    if (content) content.innerHTML = detailPage();
    // Reload reviews and recs
    if (S.detailData) {
        loadReviews(S.detailData.title);
        loadRecommendations(S.detailData.id);
    }
}

// ===== MOVIE ACTIONS =====
async function openMovie(id) {
    S.detailData = null; S.detailId = id; S.trailerPlaying = false;
    navigate('detail');
}

function goBack() {
    if (S.navHistory.length > 0) {
        const prev = S.navHistory.pop();
        Object.assign(S, {
            searchQuery: prev.searchQuery || '',
            searchType: prev.searchType || 'movie',
            filterGenre: prev.filterGenre || '',
            detailId: prev.detailId,
            detailData: prev.detailData,
        });
        navigate(prev.page, {}, true); // skipHistory=true so we don't re-push
    } else {
        navigate('home', {}, true);
    }
}

async function openActorProfile(name, personId) {
    if (personId && personId > 0) {
        S.actorData = null;
        S.actorPersonId = personId;
        navigate('actor');
    } else {
        // Fallback: search by actor name
        navigate('search', { searchQuery: name, searchType: 'actor' });
    }
}

async function loadActorProfile() {
    if (!S.actorPersonId) return;
    try {
        const data = await api(`person/${S.actorPersonId}`);
        S.actorData = data;
        document.getElementById('content').innerHTML = actorPage();
    } catch {
        document.getElementById('content').innerHTML = emptyState('⚠️', 'Failed to load actor details');
    }
}

async function addWatchlist(title) {
    const res = await api('watchlist', { method: 'POST', body: { username: S.user, movie: title } });
    toast(res.message || (res.success ? '❤️ Added to Watchlist!' : 'Already saved'));
    if (res.success) triggerBurst('❤️,💖,💕,💗,❤️');
}

async function addLike(title) {
    const res = await api('liked', { method: 'POST', body: { username: S.user, movie: title } });
    toast(res.message || '👍 Liked!');
    triggerBurst('👍,⭐,✨,🎉,👍,⭐');
}

// Floating emoji burst animation
function triggerBurst(emojisStr) {
    const emojis = emojisStr.split(',');
    const container = document.createElement('div');
    container.className = 'burst-container';
    emojis.forEach((e, i) => {
        const el = document.createElement('div');
        el.className = 'float-emoji';
        el.textContent = e;
        el.style.left = (15 + Math.random() * 70) + '%';
        el.style.bottom = '30%';
        el.style.animationDelay = (i * 0.08) + 's';
        container.appendChild(el);
    });
    // Add confetti
    const colors = ['#ff6b6b', '#4ecdc4', '#ffe66d', '#95e1d3', '#f38181', '#aa96da', '#fcbad3'];
    for (let i = 0; i < 10; i++) {
        const c = document.createElement('div');
        c.className = 'confetti-piece';
        c.style.left = (10 + Math.random() * 80) + '%';
        c.style.top = (30 + Math.random() * 20) + '%';
        c.style.background = colors[i % colors.length];
        c.style.animationDelay = (Math.random() * 0.3) + 's';
        container.appendChild(c);
    }
    document.body.appendChild(container);
    setTimeout(() => container.remove(), 2000);
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
    // Load genres for chips
    loadGenreChips();
    // Load top movies
    const grid = document.getElementById('movieGrid');
    try {
        const movies = await api('movies/top');
        grid.innerHTML = movies.length ? movies.map(movieCardHtml).join('') : emptyState('🎬', 'No movies found');
    } catch { grid.innerHTML = emptyState('⚠️', 'Failed to load movies'); }
}

async function loadGenreChips() {
    const container = document.getElementById('genreContainer');
    if (!container) return;
    try {
        const genres = await api('genres');
        if (genres && genres.length) {
            S.genreList = genres;
            const colors = ['#e74c3c', '#2ecc71', '#3498db', '#9b59b6', '#f1c40f', '#00cec9', '#e84393', '#fdcb6e'];
            container.innerHTML = `<div class="genre-scroll" style="display:flex; gap:12px; padding:10px 20px; overflow-x:auto;">${genres.map((g, i) => {
                const c = colors[i % colors.length];
                return `<div class="genre-chip" style="border: 2px solid ${c}; background: transparent; color: white; padding: 6px 20px; border-radius: 25px; box-shadow: 0 0 12px ${c}40, inset 0 0 8px ${c}20; font-weight: 600; letter-spacing: 0.5px; flex-shrink: 0; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;" onclick="filterByGenre('${g}')" onmouseover="this.style.boxShadow='0 0 20px ${c}80, inset 0 0 12px ${c}40'; this.style.transform='scale(1.05)';" onmouseout="this.style.boxShadow='0 0 12px ${c}40, inset 0 0 8px ${c}20'; this.style.transform='scale(1)';">${g}</div>`
            }).join('')}</div>`;
        }
    } catch {}
}

async function loadSearch(page = 1) {
    S.searchPage = page;
    const grid = document.getElementById('movieGrid');
    const loadMoreBtn = document.getElementById('loadMoreContainer');
    if (page === 1) {
        grid.innerHTML = loadingCards(9);
        if (loadMoreBtn) loadMoreBtn.style.display = 'none';
    }
    try {
        let movies;
        if (S.filterGenre) {
            // Genre filter mode — use the filter API with pagination and query
            movies = await api(`movies/filter?genre=${encodeURIComponent(S.filterGenre)}&q=${encodeURIComponent(S.searchQuery || '')}&page=${page}`);
        } else if (S.searchQuery) {
            // Text search mode — use search API
            movies = await api(`movies/search?q=${encodeURIComponent(S.searchQuery)}&type=${S.searchType}`);
        } else {
            movies = [];
        }
        
        const html = movies.length ? movies.map(movieCardHtml).join('') : '';
        if (page === 1) {
            grid.innerHTML = html || emptyState('🔍', 'No results found. Try a different search.');
        } else if (html) {
            grid.innerHTML += html;
        }
        
        if (loadMoreBtn) {
            loadMoreBtn.style.display = (S.filterGenre && movies.length === 30) ? 'block' : 'none';
        }
    } catch (err) {
        console.error('Search error:', err);
        if (page === 1) grid.innerHTML = emptyState('⚠️', 'Search failed. Please try again.');
    }
}

async function loadDetail() {
    try {
        const m = await api(`movies/${S.detailId}`);
        S.detailData = m;
        // Add to recently viewed with poster data
        S.recentlyViewed = S.recentlyViewed.filter(r => r.id !== m.id);
        S.recentlyViewed.unshift({ id: m.id, title: m.title, poster: m.poster, rating: m.rating, year: m.year });
        S.recentlyViewed = S.recentlyViewed.slice(0, 15);
        localStorage.setItem('cm_recent', JSON.stringify(S.recentlyViewed));
        // Re-render with data
        document.getElementById('content').innerHTML = detailPage();
        // Load reviews, recommendations & songs
        loadReviews(m.title);
        loadRecommendations(m.id);
        loadSongs(m.title);
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

// ===== SONGS =====
function miniPlayerHtml() {
    if (!S.currentSong) return '';
    const song = S.currentSong;
    const playIcon = S.audioPlaying ? '⏸️' : '▶️';
    const curTime = formatDuration(cmAudio.currentTime || 0);
    const totalTime = formatDuration(cmAudio.duration || song.duration || 0);
    return `
    <div class="mini-player" id="miniPlayer">
        <div class="mini-player-top">
            <img src="${song.image}" alt="${song.name}" class="mini-player-art">
            <div class="mini-player-info">
                <div class="mini-player-title">${song.name}</div>
                <div class="mini-player-artist">${song.artist}</div>
            </div>
            <button class="mini-player-close" onclick="stopSong()">✕</button>
        </div>
        <div class="mini-player-seek" id="miniSeek" onclick="seekAudio(event)">
            <div class="mini-player-seek-fill" id="miniSeekFill"></div>
            <div class="mini-player-seek-thumb" id="miniSeekThumb"></div>
        </div>
        <div class="mini-player-controls">
            <span class="mini-player-time" id="miniTimeLeft">${curTime}</span>
            <button class="mini-ctrl-btn" onclick="skipAudio(-10)" title="Back 10s">⏪</button>
            <button class="mini-player-btn" onclick="togglePlayPause()">${playIcon}</button>
            <button class="mini-ctrl-btn" onclick="skipAudio(10)" title="Forward 10s">⏩</button>
            <span class="mini-player-time" id="miniTimeRight">${totalTime}</span>
        </div>
    </div>`;
}

function formatDuration(secs) {
    if (!secs) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
}

async function loadSongs(title) {
    const container = document.getElementById('songsContainer');
    if (!container) return;
    try {
        const year = S.detailData ? (S.detailData.year || '') : '';
        const songs = await api(`songs/search?q=${encodeURIComponent(title)}&year=${year}`);
        if (!songs || !songs.length) {
            const titleSection = document.getElementById('songsTitleSection');
            if (titleSection) titleSection.style.display = 'none';
            container.style.display = 'none';
            return;
        }
        container.innerHTML = `<div class="songs-list">${songs.map((song, i) => {
            const isPlaying = S.currentSong && S.currentSong.id === song.id && S.audioPlaying;
            const playIcon = isPlaying ? '⏸️' : '▶️';
            const activeClass = isPlaying ? 'song-active' : '';
            return `
            <div class="song-card ${activeClass}" onclick="playSong(${i}, '${btoa(encodeURIComponent(JSON.stringify(songs)))}')" id="song-${song.id}">
                <img src="${song.image || 'https://placehold.co/60x60/1a1a2e/a5b4fc?text=🎵'}" alt="${song.name}" class="song-art" loading="lazy">
                <div class="song-info">
                    <div class="song-name">${song.name}</div>
                    <div class="song-artist">${song.artist}</div>
                    <div class="song-meta">${song.album ? song.album + ' • ' : ''}${formatDuration(song.duration)}</div>
                </div>
                <div class="song-play-btn">${playIcon}</div>
            </div>`;
        }).join('')}</div>`;
    } catch (err) {
        console.error('Songs load error:', err);
        container.innerHTML = `<div style="padding:0 20px 16px"><p style="color:var(--text-muted);font-size:0.85rem">Could not load songs.</p></div>`;
    }
}

function playSong(index, encodedSongs) {
    try {
        const songs = JSON.parse(decodeURIComponent(atob(encodedSongs)));
        const song = songs[index];
        if (!song || !song.url) { toast('Song not available', 'error'); return; }

        // If same song, toggle play/pause
        if (S.currentSong && S.currentSong.id === song.id) {
            togglePlayPause();
            return;
        }

        // Play new song
        S.currentSong = song;
        S.audioPlaying = true;
        cmAudio.src = song.url;
        cmAudio.play().catch(e => { console.error('Audio play error:', e); toast('Unable to play song', 'error'); });

        // Update UI
        updateSongCards();
        updateMiniPlayer();
        toast(`🎵 Now playing: ${song.name}`);
    } catch (e) {
        console.error('playSong error:', e);
    }
}

function togglePlayPause() {
    if (!S.currentSong) return;
    if (S.audioPlaying) {
        cmAudio.pause();
        S.audioPlaying = false;
    } else {
        cmAudio.play().catch(() => {});
        S.audioPlaying = true;
    }
    updateSongCards();
    updateMiniPlayer();
}

function stopSong() {
    cmAudio.pause();
    cmAudio.src = '';
    S.currentSong = null;
    S.audioPlaying = false;
    updateMiniPlayer();
    updateSongCards();
}

function updateMiniPlayer() {
    const existing = document.getElementById('miniPlayer');
    if (S.currentSong) {
        const html = miniPlayerHtml();
        if (existing) {
            existing.outerHTML = html;
        } else {
            // Insert before bottom-nav
            const nav = document.querySelector('.bottom-nav');
            if (nav) nav.insertAdjacentHTML('beforebegin', html);
        }
    } else if (existing) {
        existing.remove();
    }
}

function updateSongCards() {
    document.querySelectorAll('.song-card').forEach(card => {
        const id = card.id.replace('song-', '');
        const isPlaying = S.currentSong && S.currentSong.id === id && S.audioPlaying;
        card.classList.toggle('song-active', isPlaying);
        const btn = card.querySelector('.song-play-btn');
        if (btn) btn.textContent = isPlaying ? '⏸️' : '▶️';
    });
}

function updateAudioProgress() {
    const fill = document.getElementById('miniSeekFill');
    const thumb = document.getElementById('miniSeekThumb');
    const timeLeft = document.getElementById('miniTimeLeft');
    const timeRight = document.getElementById('miniTimeRight');
    if (fill && cmAudio.duration) {
        const pct = (cmAudio.currentTime / cmAudio.duration) * 100;
        fill.style.width = pct + '%';
        if (thumb) thumb.style.left = pct + '%';
    }
    if (timeLeft) timeLeft.textContent = formatDuration(cmAudio.currentTime || 0);
    if (timeRight) timeRight.textContent = formatDuration(cmAudio.duration || 0);
}

function seekAudio(e) {
    const bar = document.getElementById('miniSeek');
    if (!bar || !cmAudio.duration) return;
    const rect = bar.getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    cmAudio.currentTime = pct * cmAudio.duration;
}

function skipAudio(seconds) {
    if (!cmAudio.duration) return;
    cmAudio.currentTime = Math.max(0, Math.min(cmAudio.duration, cmAudio.currentTime + seconds));
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

async function loadRecent() {
    const grid = document.getElementById('movieGrid');
    if (!S.recentlyViewed.length) {
        grid.innerHTML = emptyState('🕐', 'No recently viewed movies. Browse and click on movies to see them here!');
        return;
    }
    // Show from localStorage (has poster data)
    const cards = S.recentlyViewed.map(r => ({
        id: r.id, title: r.title,
        poster: r.poster || `https://placehold.co/500x750/1a1a2e/a5b4fc?text=${encodeURIComponent((r.title||'Movie').substring(0,15))}`,
        rating: r.rating || 0, year: r.year || 'N/A'
    }));
    grid.innerHTML = cards.map(movieCardHtml).join('');
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
    // Genre Decades
    try {
        const gd = await api('ml/genre-decades');
        const container = document.getElementById('genreDecadesChart');
        if (gd && gd.length) {
            // Group by decade
            const decades = {};
            gd.forEach(item => {
                if (!decades[item.decade]) decades[item.decade] = {};
                decades[item.decade][item.genre] = item.count;
            });
            const allGenres = [...new Set(gd.map(i => i.genre))];
            const genreColors = ['#667eea','#f093fb','#34d399','#fbbf24','#f87171','#00d4ff','#a78bfa','#ff6b6b'];
            // Legend
            let legendHtml = `<div style="display:flex;flex-wrap:wrap;gap:8px;padding:0 20px 12px">${allGenres.map((g,i) => `<span style="font-size:0.7rem;color:${genreColors[i%genreColors.length]};font-weight:600">● ${g}</span>`).join('')}</div>`;
            // Bars per decade
            let barsHtml = '<div class="bar-chart">';
            Object.keys(decades).sort().forEach(decade => {
                const maxInDecade = Math.max(...Object.values(decades[decade]));
                allGenres.forEach((genre, gi) => {
                    const count = decades[decade][genre] || 0;
                    if (count > 0) {
                        barsHtml += `<div class="bar-row"><div class="bar-label" style="width:80px">${decade} ${genre.substring(0,6)}</div><div class="bar-track"><div class="bar-fill" style="width:${(count/maxInDecade*100).toFixed(0)}%;background:${genreColors[gi%genreColors.length]}"><span class="bar-value">${count}</span></div></div></div>`;
                    }
                });
            });
            barsHtml += '</div>';
            container.innerHTML = legendHtml + barsHtml;
        } else container.innerHTML = emptyState('📊', 'Not enough data');
    } catch {}
    // Taste Profile
    try {
        const tp = await api(`ml/taste-profile?username=${S.user}`);
        const container = document.getElementById('tasteProfile');
        const entries = Object.entries(tp);
        if (entries.length) {
            const max = Math.max(...entries.map(e => e[1]));
            const colors = ['#667eea','#f093fb','#34d399','#fbbf24','#f87171','#00d4ff','#a78bfa','#ff6b6b'];
            container.innerHTML = `<div class="taste-grid">${entries.map(([genre, count], i) => `
                <div class="taste-item">
                    <div class="taste-genre">${genre}</div>
                    <div class="taste-bar-bg"><div class="taste-bar-fill" style="width:${(count/max*100).toFixed(0)}%;background:${colors[i%colors.length]}"></div></div>
                    <div class="taste-count">${count} movies</div>
                </div>
            `).join('')}</div>`;
        } else container.innerHTML = emptyState('👤', 'Add movies to watchlist or likes to see your taste profile!');
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

    // Android hardware back button / browser back
    window.addEventListener('popstate', (e) => {
        if (S.page === 'login') return;
        if (S.page === 'detail') { goBack(); }
        else if (S.page !== 'home') { goBack(); }
        // Push a dummy state so we can catch the next back press
        history.pushState(null, '', '');
    });
    // Push initial state
    history.pushState(null, '', '');
})();
