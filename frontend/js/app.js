/**
 * Aura — Main Application Controller
 * Handles navigation, screen switching, data loading, and all interactions.
 */

document.addEventListener('DOMContentLoaded', () => {

    // ═══════════════════════════════════════════════
    // SPLASH / ONBOARDING SCREEN
    // ═══════════════════════════════════════════════
    const splash = document.getElementById('splash-screen');
    const btnGetStarted = document.getElementById('btn-get-started');
    
    if (splash) {
        const hasOnboarded = localStorage.getItem('aura_onboarded');
        if (hasOnboarded) {
            // Already onboarded — show splash for 3 seconds then transition
            setTimeout(() => splash.classList.add('hidden'), 3000);
        } else {
            // New user, show Get Started button after a short delay
            setTimeout(() => {
                btnGetStarted.classList.remove('hidden');
            }, 2000);
            
            btnGetStarted.addEventListener('click', () => {
                localStorage.setItem('aura_onboarded', 'true');
                splash.classList.add('hidden');
            });
        }
    }

    // ═══════════════════════════════════════════════
    // NAVIGATION
    // ═══════════════════════════════════════════════

    const screens = document.querySelectorAll('.screen');
    const navItems = document.querySelectorAll('.nav-item');
    let activeScreen = 'home';

    function switchScreen(screenId) {
        if (screenId === activeScreen) return;

        screens.forEach(s => s.classList.remove('active'));
        navItems.forEach(n => n.classList.remove('active'));

        document.getElementById(`screen-${screenId}`).classList.add('active');
        document.querySelector(`[data-screen="${screenId}"]`).classList.add('active');

        // Start/stop camera + compass when switching to/from Scan
        if (screenId === 'scan') {
            AuraCamera.start();
            if (typeof AuraOrientation !== 'undefined') {
                AuraOrientation.start();
            }
        } else if (activeScreen === 'scan') {
            AuraCamera.stop();
            if (typeof AuraOrientation !== 'undefined') {
                AuraOrientation.stop();
            }
        }

        // Load tips when switching to Tips
        if (screenId === 'tips') {
            loadTips();
        }

        // Load profile when switching to Profile
        if (screenId === 'profile') {
            loadProfile();
        }

        activeScreen = screenId;
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            switchScreen(item.dataset.screen);
        });
    });


    // ═══════════════════════════════════════════════
    // HOME — Greeting
    // ═══════════════════════════════════════════════

    function updateGreeting() {
        const hour = new Date().getHours();
        const el = document.getElementById('home-greeting');
        if (hour < 6)       el.textContent = 'Good night ✦';
        else if (hour < 12) el.textContent = 'Good morning ✦';
        else if (hour < 17) el.textContent = 'Good afternoon ✦';
        else if (hour < 21) el.textContent = 'Good evening ✦';
        else                el.textContent = 'Good night ✦';
    }

    function updateTime() {
        const now = new Date();
        const opts = { weekday: 'short', month: 'short', day: 'numeric' };
        document.getElementById('header-time').textContent = now.toLocaleDateString('en-IE', opts);
    }

    updateGreeting();
    updateTime();


    // ═══════════════════════════════════════════════
    // HOME — Weather Widget
    // ═══════════════════════════════════════════════

    async function loadWeather() {
        try {
            // Get user location or default to Dublin
            let lat = 53.3498;
            let lon = -6.2603;
            
            try {
                const pos = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, {timeout: 5000});
                });
                lat = pos.coords.latitude;
                lon = pos.coords.longitude;
            } catch(e) {
                console.log("[Aura] Using default location (Dublin). Location access denied or timed out.");
            }

            const [weather, sun] = await Promise.all([
                AuraAPI.getWeather(lat, lon),
                AuraAPI.getSunPosition(lat, lon),
            ]);
            window.currentWeather = weather;
            window.currentSun = sun;

            // Temperature
            const tempEl = document.getElementById('weather-temp');
            if (weather.temperature != null) {
                tempEl.textContent = `${Math.round(weather.temperature)}°C`;
            } else {
                tempEl.textContent = '--°C';
            }

            // Description
            const descEl = document.getElementById('weather-desc');
            descEl.textContent = weather.weather_description || 'Weather data';

            // Outdoor Locations (Adım 8)
            loadOutdoorPlaces(lat, lon);

            // Humidity
            const humEl = document.getElementById('weather-humidity');
            humEl.textContent = weather.humidity != null ? `${weather.humidity}%` : '--%';

            // Sun
            const sunEl = document.getElementById('weather-sun');
            if (sun.light_quality) {
                const labels = {
                    night: '🌙 Night',
                    twilight: '🌅 Twilight',
                    low_angle: '🌤️ Low sun',
                    good: '☀️ Good light',
                    unknown: '--',
                };
                sunEl.textContent = labels[sun.light_quality] || sun.light_quality;
            }
            // Insight
            const insightEl = document.getElementById('weather-insight');
            if (sun.is_daylight === false) {
                insightEl.textContent = '🌙 It\'s dark outside — focus on indoor ambient lighting for comfort.';
            } else if (weather.rain && weather.rain > 0) {
                insightEl.textContent = '🌧️ Rain expected — keep windows closed but check ventilation.';
            } else if (sun.light_quality === 'good') {
                insightEl.textContent = '☀️ Great natural light — open curtains and let the sun in!';
            } else {
                insightEl.textContent = '💡 Make the most of available light with mirrors and light colours.';
            }
        } catch {
            document.getElementById('weather-insight').textContent = '⚠️ Could not load weather — check backend connection.';
        }
    }

    loadWeather();
    loadLifestyle();

    // ═══════════════════════════════════════════════
    // HOME — Mood Selector
    // ═══════════════════════════════════════════════

    // ─── Spotify playlist data (mirrors backend/core/music.py) ───
    const MOOD_PLAYLISTS = {
        stressed: { name: "Peaceful Meditation",  desc: "Slow your breath and let the tension go.",          url: "https://open.spotify.com/playlist/37i9dQZF1DWZd79rJ6a7lp" },
        tired:    { name: "Morning Motivation",    desc: "Wake up your body and spark some energy.",          url: "https://open.spotify.com/playlist/37i9dQZF1DXc5e2bJhV6pu" },
        anxious:  { name: "Anxiety Relief",        desc: "Gentle, grounding music to ease your mind.",       url: "https://open.spotify.com/playlist/37i9dQZF1DWXe9gFZP0gtP" },
        calm:     { name: "Cozy Evenings",         desc: "Warm, unhurried tones for a quiet evening in.",    url: "https://open.spotify.com/playlist/37i9dQZF1DX4E3UdUs7fUx" },
        energetic:{ name: "Power Hour",            desc: "High-energy tracks to match your unstoppable mood.",url: "https://open.spotify.com/playlist/37i9dQZF1DX76Wlfdnj7AP" },
        creative: { name: "Creative Flow",         desc: "Instrumental vibes to keep your ideas flowing.",   url: "https://open.spotify.com/playlist/37i9dQZF1DWXLeA8Omikj7" },
        sad:      { name: "Comfort Songs",         desc: "Warm, tender music that feels like a hug.",        url: "https://open.spotify.com/playlist/37i9dQZF1DX7gIoKXt0gmx" },
        angry:    { name: "Release the Tension",   desc: "Channel the energy and let it move through you.",  url: "https://open.spotify.com/playlist/37i9dQZF1DWTggY0yqBxES" },
        happy:    { name: "Happy Hits",            desc: "Pure joy — turn it up and enjoy the good vibes!", url: "https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC" },
        focused:  { name: "Deep Focus",            desc: "Minimal distractions, maximum concentration.",     url: "https://open.spotify.com/playlist/37i9dQZF1DWZeKCadgRdKQ" },
    };

    const moodGrid = document.getElementById('mood-grid');
    moodGrid.addEventListener('click', (e) => {
        const btn = e.target.closest('.mood-btn');
        if (!btn) return;

        moodGrid.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');

        const mood = btn.dataset.mood;
        
        AuraAPI.logMood(mood, window.currentWeather || {}, window.currentSun || {}).then(res => {
            if (res.insight) {
                // Save to localStorage for home screen card
                localStorage.setItem('aura_mood_insight', res.insight);
                
                // Show on home screen
                const card = document.getElementById('home-mood-insight');
                const text = document.getElementById('mood-insight-text');
                if (card && text) {
                    text.textContent = res.insight;
                    card.style.display = 'block';
                }
                
                // Also show in chat
                setTimeout(() => {
                    AuraChat.addAuraMessage(`**Memory Insight:** ${res.insight}`);
                }, 1500);
            }

            // Show mood activity cards on home screen
            if (res.activities && res.activities.length > 0) {
                const actContainer = document.getElementById('mood-activities-container');
                if (actContainer) {
                    actContainer.innerHTML = '';
                    actContainer.style.display = 'block';
                    
                    const title = document.createElement('h3');
                    title.className = 'section-title';
                    title.textContent = '✨ Aura Suggests';
                    title.style.marginBottom = '12px';
                    actContainer.appendChild(title);

                    res.activities.forEach(act => {
                        const card = document.createElement('div');
                        card.className = 'mood-activity-card';
                        card.innerHTML = `
                            <div class="mood-act-icon">${act.icon}</div>
                            <div class="mood-act-content">
                                <div class="mood-act-category">${act.category}</div>
                                <div class="mood-act-text">${act.suggestion}</div>
                            </div>
                        `;
                        card.appendChild(_makeSuggestionCheckbox(act.suggestion));
                        actContainer.appendChild(card);
                    });

                    // Spotify music card — slides in after activity cards
                    const playlist = MOOD_PLAYLISTS[mood];
                    if (playlist) {
                        const musicCard = document.createElement('div');
                        musicCard.className = 'spotify-card';
                        musicCard.style.animationDelay = `${res.activities.length * 0.1 + 0.15}s`;
                        musicCard.innerHTML = `
                            <div class="spotify-card-icon">♪</div>
                            <div class="spotify-card-body">
                                <div class="spotify-card-name">${playlist.name}</div>
                                <div class="spotify-card-desc">${playlist.desc}</div>
                                <a class="spotify-card-btn" href="${playlist.url}" target="_blank" rel="noopener noreferrer">
                                    Open in Spotify →
                                </a>
                            </div>
                        `;
                        actContainer.appendChild(musicCard);
                    }
                }
            }
        }).catch(err => console.error("Could not log mood:", err));

        // Open chat with mood-based message
        openChat();
        setTimeout(() => {
            AuraChat.sendMessage(`I'm feeling ${mood} today. Any suggestions for my space?`);
        }, 400);
    });


    // ═══════════════════════════════════════════════
    // HOME — Outdoor Places (Adım 8)
    // ═══════════════════════════════════════════════
    async function loadOutdoorPlaces(lat, lon) {
        try {
            const places = await AuraAPI.getNearbyOutdoor(lat, lon);
            if (places && places.length > 0) {
                const card = document.getElementById('outdoor-card');
                const container = document.getElementById('outdoor-places');
                container.innerHTML = '';
                
                places.forEach(p => {
                    const el = document.createElement('div');
                    el.className = 'outdoor-place-item';
                    el.innerHTML = `
                        <span class="outdoor-place-name">${p.name}</span>
                        <span class="outdoor-place-dist">📍 ${Math.round(p.distance_m)}m</span>
                    `;
                    container.appendChild(el);
                });
                
                // Only show card if there's no active rain (handled by backend or simple check)
                if (window.currentWeather && window.currentWeather.rain && window.currentWeather.rain > 0) {
                    document.getElementById('outdoor-subtitle').textContent = "It's raining. Save these for later!";
                }
                card.style.display = 'block';
            }
        } catch(e) {
            console.error("Could not load outdoor places");
        }
    }


    // ═══════════════════════════════════════════════
    // HOME — See All Tips
    // ═══════════════════════════════════════════════

    document.getElementById('btn-see-all-tips').addEventListener('click', () => {
        switchScreen('tips');
    });


    // ═══════════════════════════════════════════════
    // SCAN — Camera & Analysis
    // ═══════════════════════════════════════════════

    // Image Capture
    document.getElementById('btn-capture').addEventListener('click', async () => {
        const blob = await AuraCamera.capture();
        if (!blob) return;

        // Reset demo state — real scan uses the logged-in user profile only
        _demoProfile = null;
        window.currentUserId = 'default';
        document.querySelectorAll('.demo-chip').forEach(c => c.classList.remove('active'));
        document.getElementById('demo-scan-action').classList.add('hidden');
        document.getElementById('demo-profile-bar').classList.add('hidden');

        // Clear any previous zone overlay before starting a new capture
        _clearZones();

        // Run zone analysis in parallel with the main space analysis
        runZoneAnalysis(blob);

        // Show results panel with loading state (also hides any lingering reopen pill)
        _resetAnalysisState();
        document.getElementById('result-description').textContent = 'Analysing your space…';
        document.getElementById('result-objects').innerHTML = '<span class="shimmer" style="width:60px;height:20px;display:inline-block"></span>';
        document.getElementById('result-suggestions').innerHTML = '<div class="shimmer" style="height:60px;margin-bottom:8px"></div>'.repeat(3);
        _showAnalysisPanel();

        try {
            const _scanUserId = window.currentUserId || 'default';
            const _compassHeading = (typeof AuraOrientation !== 'undefined') ? AuraOrientation.getHeading() : null;
            const result = await AuraAPI.analyseImage(blob, _scanUserId, _compassHeading);

            // Description
            document.getElementById('result-description').textContent =
                result.description || 'Space analysed successfully.';

            // Objects
            const objContainer = document.getElementById('result-objects');
            objContainer.innerHTML = '';
            if (result.objects_detected && result.objects_detected.length) {
                result.objects_detected.forEach(obj => {
                    const tag = document.createElement('span');
                    tag.className = 'result-tag';
                    tag.textContent = obj;
                    objContainer.appendChild(tag);
                });
            } else {
                objContainer.innerHTML = '<span class="result-tag">No objects detected</span>';
            }

            // Risks
            const risksContainer = document.getElementById('result-risks') || objContainer; // Fallback to objects if risks container doesn't exist
            if (result.risks_identified && result.risks_identified.length) {
                result.risks_identified.forEach(risk => {
                    const tag = document.createElement('span');
                    tag.className = 'result-tag risk-tag';
                    tag.style.background = 'rgba(239, 68, 68, 0.1)';
                    tag.style.color = '#EF4444';
                    tag.textContent = risk;
                    risksContainer.appendChild(tag);
                });
            }

            // Suggestions
            const sugContainer = document.getElementById('result-suggestions');
            sugContainer.innerHTML = '';
            if (result.suggestions && result.suggestions.length) {
                result.suggestions.forEach((s, i) => {
                    const item = document.createElement('div');
                    item.className = 'suggestion-item';

                    const suggestionText = typeof s === 'object' ? (s.action || '') : s;

                    if (typeof s === 'object') {
                        item.innerHTML = `
                            <span class="suggestion-num">${i + 1}</span>
                            <div style="display:flex; flex-direction:column; gap: 4px; flex:1; min-width:0;">
                                <span class="suggestion-text"><strong>${s.action || ''}</strong></span>
                                <span style="font-size: 0.8rem; color: var(--text-secondary);"><em>${s.why_this_matters || ''}</em></span>
                                <span style="font-size: 0.75rem; color: var(--text-tertiary);">Confidence: ${s.confidence || 0}%</span>
                            </div>
                        `;
                    } else {
                        item.innerHTML = `
                            <span class="suggestion-num">${i + 1}</span>
                            <span class="suggestion-text" style="flex:1; min-width:0;">${s}</span>
                        `;
                    }
                    item.appendChild(_makeSuggestionCheckbox(suggestionText));
                    sugContainer.appendChild(item);
                });
            } else {
                sugContainer.innerHTML = '<p style="color:var(--text-secondary);font-size:var(--fs-sm)">No specific suggestions at this time.</p>';
            }

            // Space Score
            if (result.score) {
                document.getElementById('score-section').style.display = 'block';
                document.getElementById('score-number').textContent = result.score.overall || 0;
                document.getElementById('score-light').textContent = result.score.light || 0;
                document.getElementById('score-air').textContent = result.score.air || 0;
                document.getElementById('score-safety').textContent = result.score.safety || 0;
                document.getElementById('score-comfort').textContent = result.score.comfort || 0;
                
                // Animate SVG circle
                const activeDash = result.score.overall || 0;
                setTimeout(() => {
                    document.getElementById('score-ring').style.strokeDasharray = `${activeDash}, 100`;
                }, 100);
                
                const diffEl = document.getElementById('score-diff');
                if (result.comparison) {
                    diffEl.textContent = result.comparison;
                } else {
                    diffEl.textContent = "";
                }
            } else {
                document.getElementById('score-section').style.display = 'none';
            }
        } catch {
            document.getElementById('result-description').textContent =
                'Could not analyse — make sure Ollama is running with LLaVA.';
            document.getElementById('result-objects').innerHTML = '';
            document.getElementById('result-suggestions').innerHTML = '';
        }
    });

    const _analysisPanel = document.getElementById('analysis-results');
    const _reopenPill    = document.getElementById('analysis-reopen-pill');

    function _showAnalysisPanel()  { _analysisPanel.classList.remove('hidden'); _reopenPill.classList.add('hidden'); }
    function _hideAnalysisPanel()  { _analysisPanel.classList.add('hidden');    _reopenPill.classList.remove('hidden'); }
    function _resetAnalysisState() { _analysisPanel.classList.add('hidden');    _reopenPill.classList.add('hidden'); }

    document.getElementById('btn-close-results').addEventListener('click', () => {
        _hideAnalysisPanel();
        document.getElementById('room-label-row').style.display = 'none';
        document.getElementById('room-label-input').value = '';
    });

    document.getElementById('btn-reopen-analysis').addEventListener('click', _showAnalysisPanel);

    // ═══════════════════════════════════════════════
    // SHARED — Points toast + suggestion checkbox
    // ═══════════════════════════════════════════════

    function _showPointsToast(points) {
        let toast = document.getElementById('aura-points-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'aura-points-toast';
            document.body.appendChild(toast);
        }
        toast.textContent = `+${points} Aura Points ✓`;
        toast.classList.add('show');
        clearTimeout(toast._hideTimer);
        toast._hideTimer = setTimeout(() => toast.classList.remove('show'), 2500);
    }

    function _makeSuggestionCheckbox(suggestionText) {
        const btn = document.createElement('button');
        btn.className = 'suggestion-checkbox';
        btn.setAttribute('aria-label', 'Mark as done');
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (btn.classList.contains('checked')) return;
            btn.textContent = '✓';
            btn.classList.add('checked');
            const card = btn.closest('.suggestion-item, .zone-card');
            if (card) card.classList.add('done');
            try {
                const userId = window.currentUserId || 'default';
                const res = await AuraAPI.completeSuggestion(suggestionText, userId);
                _showPointsToast(res.points_awarded ?? 5);
            } catch (err) {
                console.error('[Aura] Could not save completion:', err);
            }
        });
        return btn;
    }

    // ═══════════════════════════════════════════════
    // SCAN — Zone Analysis
    // ═══════════════════════════════════════════════

    const ZONE_COLORS = {
        red:    { fill: 'rgba(239,68,68,0.22)',   stroke: '#EF4444', label: '#fff' },
        yellow: { fill: 'rgba(251,191,36,0.22)',  stroke: '#FBBF24', label: '#000' },
        green:  { fill: 'rgba(52,211,153,0.22)',  stroke: '#34D399', label: '#000' },
        blue:   { fill: 'rgba(96,165,250,0.22)',  stroke: '#60A5FA', label: '#fff' },
    };
    const ZONE_ICONS = { danger: '🔴', caution: '🟡', opportunity: '🟢', suggestion: '🔵' };

    let _currentZones = [];

    /** Seek a video blob to its middle frame and return a JPEG blob via canvas. */
    function _extractMiddleFrame(videoBlob) {
        return new Promise((resolve, reject) => {
            const video = document.createElement('video');
            video.muted = true;
            video.playsInline = true;
            video.preload = 'metadata';
            const url = URL.createObjectURL(videoBlob);
            video.src = url;

            video.addEventListener('loadedmetadata', () => {
                video.currentTime = video.duration > 0 ? video.duration / 2 : 0;
            });

            video.addEventListener('seeked', () => {
                try {
                    const c = document.createElement('canvas');
                    c.width  = video.videoWidth  || 640;
                    c.height = video.videoHeight || 480;
                    c.getContext('2d').drawImage(video, 0, 0, c.width, c.height);
                    c.toBlob(blob => {
                        URL.revokeObjectURL(url);
                        blob ? resolve(blob) : reject(new Error('toBlob failed'));
                    }, 'image/jpeg', 0.85);
                } catch (e) { URL.revokeObjectURL(url); reject(e); }
            });

            video.addEventListener('error', e => { URL.revokeObjectURL(url); reject(e); });
        });
    }

    /** Draw a blob as a cover-fitted image on a canvas 2D context. */
    function _drawBlobOnCanvas(ctx, blob, w, h) {
        return new Promise(resolve => {
            const img = new Image();
            const url = URL.createObjectURL(blob);
            img.onload  = () => { ctx.drawImage(img, 0, 0, w, h); URL.revokeObjectURL(url); resolve(); };
            img.onerror = () => { URL.revokeObjectURL(url); resolve(); };
            img.src = url;
        });
    }

    async function runZoneAnalysis(blob) {
        const overlay    = document.getElementById('zone-overlay');
        const viewfinder = document.querySelector('.camera-viewfinder');
        const userId     = window.currentUserId || 'default';

        // Size the overlay canvas to the viewfinder's rendered dimensions
        const ow = viewfinder.clientWidth;
        const oh = viewfinder.clientHeight;
        overlay.width  = ow;
        overlay.height = oh;

        const ctx = overlay.getContext('2d');

        const drawCapturedImage = () => new Promise(resolve => {
            const img = new Image();
            img.onload = () => { ctx.drawImage(img, 0, 0, ow, oh); resolve(); };
            img.src = URL.createObjectURL(blob);
        });

        // Loading state — draw frozen frame + dim overlay
        await drawCapturedImage();
        ctx.fillStyle = 'rgba(0,0,0,0.45)';
        ctx.fillRect(0, 0, ow, oh);
        ctx.fillStyle = '#c084fc';
        ctx.font = 'bold 15px "Plus Jakarta Sans", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Identifying zones\u2026', ow / 2, oh / 2);

        overlay.classList.add('visible');
        document.getElementById('btn-clear-zones').classList.remove('hidden');
        // Keep entire demo bar and video controls hidden while a real scan overlay is showing
        document.getElementById('demo-scan-action').classList.add('hidden');
        document.getElementById('demo-profile-bar').classList.add('hidden');
        document.getElementById('video-controls').classList.add('hidden');

        try {
            const result = await AuraAPI.analyseZones(blob, userId);
            _currentZones = result.zones || [];

            // Redraw clean captured image then animate zones on top
            ctx.clearRect(0, 0, ow, oh);
            await drawCapturedImage();
            _drawZones(overlay, _currentZones);

            // Show zone report cards below camera
            _renderZoneReport(result);
            document.getElementById('zone-report').classList.remove('hidden');

        } catch (err) {
            console.error('[Aura Zones] Zone analysis failed:', err);
            ctx.clearRect(0, 0, ow, oh);
            await drawCapturedImage();
            ctx.fillStyle = 'rgba(239,68,68,0.4)';
            ctx.fillRect(0, 0, ow, oh);
            ctx.fillStyle = '#fff';
            ctx.font = '14px "Plus Jakarta Sans", sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('Zone analysis unavailable', ow / 2, oh / 2);
        }
    }

    function _drawZones(canvas, zones) {
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;

        // Cap at 4 zones (highest priority first — already sorted by priority asc)
        const visibleZones = zones.slice(0, 4);

        visibleZones.forEach((zone, idx) => {
            // Stagger each zone by 200 ms for animated fade-in effect
            setTimeout(() => {
                const x  = (zone.x_percent       / 100) * w;
                const y  = (zone.y_percent        / 100) * h;
                const zw = (zone.width_percent    / 100) * w;
                const zh = (zone.height_percent   / 100) * h;
                const c  = ZONE_COLORS[zone.color] || ZONE_COLORS.blue;

                // Semi-transparent fill
                ctx.fillStyle = c.fill;
                ctx.fillRect(x, y, zw, zh);

                // Coloured border
                ctx.strokeStyle = c.stroke;
                ctx.lineWidth = 2;
                ctx.strokeRect(x, y, zw, zh);

                // Label badge positioning: avoid right overflow and left-edge clipping
                ctx.font = 'bold 11px "Plus Jakarta Sans", sans-serif';
                ctx.textBaseline = 'middle';
                ctx.textAlign = 'left';
                const textW  = ctx.measureText(zone.label).width;
                const badgeW = Math.min(textW + 16, zw);
                const badgeH = 20;
                let labelX;
                if (x + badgeW > w) {
                    // Would overflow right edge — push left
                    labelX = Math.max(4, w - badgeW);
                } else if (x < w * 0.15) {
                    // Near left edge — nudge inside the zone so text isn't clipped
                    labelX = x + 4;
                } else {
                    labelX = x;
                }
                ctx.fillStyle = c.stroke;
                ctx.fillRect(labelX, y, badgeW, badgeH);
                ctx.fillStyle = c.label;
                ctx.fillText(zone.label, labelX + 8, y + badgeH / 2);
            }, idx * 200);
        });

        // Tap/click → show zone detail card
        canvas.onclick = (e) => {
            const rect   = canvas.getBoundingClientRect();
            const scaleX = canvas.width  / rect.width;
            const scaleY = canvas.height / rect.height;
            const cx = (e.clientX - rect.left) * scaleX;
            const cy = (e.clientY - rect.top)  * scaleY;

            const tapped = _currentZones.find(zone => {
                const x  = (zone.x_percent       / 100) * canvas.width;
                const y  = (zone.y_percent        / 100) * canvas.height;
                const zw = (zone.width_percent    / 100) * canvas.width;
                const zh = (zone.height_percent   / 100) * canvas.height;
                return cx >= x && cx <= x + zw && cy >= y && cy <= y + zh;
            });
            if (tapped) _showZoneDetail(tapped);
        };
    }

    function _showZoneDetail(zone) {
        document.getElementById('zone-detail-icon').textContent          = ZONE_ICONS[zone.type] || '●';
        document.getElementById('zone-detail-label').textContent         = zone.label;
        document.getElementById('zone-detail-description').textContent   = zone.description;
        document.getElementById('zone-detail-recommendation').textContent = zone.recommendation;
        document.getElementById('zone-detail-card').classList.remove('hidden');
    }

    function _renderZoneReport(result) {
        document.getElementById('zone-overall-score').textContent = result.overall_score ?? '--';
        document.getElementById('zone-summary').textContent       = result.summary || '';

        const list = document.getElementById('zone-cards-list');
        list.innerHTML = '';
        (result.zones || []).forEach(zone => {
            const card = document.createElement('div');
            card.className = `zone-card ${zone.type}`;
            card.innerHTML = `
                <span class="zone-card-icon">${ZONE_ICONS[zone.type] || '●'}</span>
                <div class="zone-card-body">
                    <div class="zone-card-label">${zone.label}</div>
                    <div class="zone-card-rec">${zone.recommendation}</div>
                </div>
            `;
            card.appendChild(_makeSuggestionCheckbox(zone.recommendation));
            card.addEventListener('click', () => _showZoneDetail(zone));
            list.appendChild(card);
        });
    }

    // restoreDemo=true only when the user explicitly presses X — not during scan setup
    function _clearZones(restoreDemo = false) {
        const overlay = document.getElementById('zone-overlay');
        overlay.classList.remove('visible');
        const ctx = overlay.getContext('2d');
        ctx.clearRect(0, 0, overlay.width, overlay.height);
        document.getElementById('zone-report').classList.add('hidden');
        document.getElementById('zone-detail-card').classList.add('hidden');
        document.getElementById('btn-clear-zones').classList.add('hidden');
        _currentZones = [];
        if (restoreDemo) {
            // Pressing X returns the user to idle scan state — restore live-camera UI
            document.getElementById('video-controls').classList.remove('hidden');
            document.getElementById('demo-profile-bar').classList.remove('hidden');
            if (_demoProfile) {
                document.getElementById('demo-scan-action').classList.remove('hidden');
            }
        }
    }

    // Close zone detail card
    document.getElementById('btn-zone-detail-close').addEventListener('click', () => {
        document.getElementById('zone-detail-card').classList.add('hidden');
    });

    // Clear zone overlay → back to live camera (pass restoreDemo=true)
    document.getElementById('btn-clear-zones').addEventListener('click', () => _clearZones(true));

    // ═══════════════════════════════════════════════
    // SCAN — Demo Mode
    // ═══════════════════════════════════════════════

    const DEMO_META = {
        sarah:     { label: 'Sarah',      avatar: 'S', subtitle: 'Young mum · Cork',   bg: 'living_room' },
        seamus:    { label: 'Seamus',     avatar: 'S', subtitle: 'Elder · Galway',      bg: 'hallway'     },
        ms_murphy: { label: 'Ms. Murphy', avatar: 'M', subtitle: 'Teacher · Dublin',    bg: 'classroom'   },
    };

    let _demoProfile = null;

    document.getElementById('demo-profile-bar').addEventListener('click', (e) => {
        const chip = e.target.closest('.demo-chip');
        if (!chip) return;

        _demoProfile = chip.dataset.profile;
        // Route ALL API calls through this demo user so the LLM receives the correct profile
        window.currentUserId = _demoProfile;
        const meta = DEMO_META[_demoProfile];

        // Update active chip
        document.querySelectorAll('.demo-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');

        // Populate and show the demo-scan-action panel
        document.getElementById('demo-scan-avatar').textContent  = meta.avatar;
        document.getElementById('demo-scan-name').textContent    = meta.label;
        document.getElementById('demo-scan-subtitle').textContent = meta.subtitle;
        document.getElementById('demo-scan-action').classList.remove('hidden');
    });

    document.getElementById('btn-demo-scan').addEventListener('click', () => {
        if (_demoProfile) _runDemoScan(_demoProfile);
    });

    async function _runDemoScan(userId) {
        const overlay    = document.getElementById('zone-overlay');
        const viewfinder = document.querySelector('.camera-viewfinder');

        const ow = viewfinder.clientWidth;
        const oh = viewfinder.clientHeight;
        overlay.width  = ow;
        overlay.height = oh;

        const ctx = overlay.getContext('2d');
        const bg  = DEMO_META[userId]?.bg || 'living_room';

        // Clear any existing zones first
        _clearZones();
        overlay.width  = ow;
        overlay.height = oh;

        // Draw the room illustration
        _drawRoomBackground(ctx, ow, oh, bg);

        // Loading overlay
        ctx.fillStyle = 'rgba(0,0,0,0.4)';
        ctx.fillRect(0, 0, ow, oh);
        ctx.fillStyle = '#c084fc';
        ctx.font = 'bold 15px "Plus Jakarta Sans", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Loading demo zones\u2026', ow / 2, oh / 2);

        overlay.classList.add('visible');
        document.getElementById('btn-clear-zones').classList.remove('hidden');
        document.getElementById('video-controls').classList.add('hidden');

        try {
            const result = await AuraAPI.getDemoZones(userId);
            _currentZones = result.zones || [];

            ctx.clearRect(0, 0, ow, oh);
            _drawRoomBackground(ctx, ow, oh, bg);
            _drawZones(overlay, _currentZones);

            _renderZoneReport(result);
            document.getElementById('zone-report').classList.remove('hidden');

            // Hide the profile pill + scan button — X button will restore them
            document.getElementById('demo-scan-action').classList.add('hidden');

        } catch (err) {
            console.error('[Aura Demo] Failed to load demo zones:', err);
            ctx.clearRect(0, 0, ow, oh);
            _drawRoomBackground(ctx, ow, oh, bg);
            ctx.fillStyle = 'rgba(239,68,68,0.5)';
            ctx.fillRect(0, 0, ow, oh);
            ctx.fillStyle = '#fff';
            ctx.font = '13px "Plus Jakarta Sans", sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('Demo unavailable — run server seed first', ow / 2, oh / 2);
        }
    }

    // ── Room background drawing ──────────────────

    function _drawRoomBackground(ctx, w, h, type) {
        if      (type === 'living_room') _drawLivingRoom(ctx, w, h);
        else if (type === 'hallway')     _drawHallway(ctx, w, h);
        else if (type === 'classroom')   _drawClassroom(ctx, w, h);
    }

    function _drawLivingRoom(ctx, w, h) {
        // ── Wall ────────────────────────────────────────
        const wallGrad = ctx.createLinearGradient(0, 0, 0, h * 0.62);
        wallGrad.addColorStop(0, '#f2e4c8');
        wallGrad.addColorStop(1, '#e4d09a');
        ctx.fillStyle = wallGrad;
        ctx.fillRect(0, 0, w, h * 0.62);

        // ── Floor ───────────────────────────────────────
        const floorGrad = ctx.createLinearGradient(0, h * 0.62, 0, h);
        floorGrad.addColorStop(0, '#c8944a');
        floorGrad.addColorStop(1, '#a87030');
        ctx.fillStyle = floorGrad;
        ctx.fillRect(0, h * 0.62, w, h * 0.38);

        // Floor plank lines
        ctx.strokeStyle = 'rgba(100, 60, 20, 0.18)';
        ctx.lineWidth = 1;
        for (let y = h * 0.65; y < h; y += h * 0.07) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }

        // Baseboard
        ctx.fillStyle = '#d4a860';
        ctx.fillRect(0, h * 0.60, w, h * 0.04);

        // ── Window (right, maps to Window Cord zone ~70%,8%) ──
        ctx.fillStyle = '#87ceeb';
        ctx.fillRect(w * 0.68, h * 0.05, w * 0.24, h * 0.37);
        ctx.strokeStyle = '#c8a060';
        ctx.lineWidth = 3;
        ctx.strokeRect(w * 0.68, h * 0.05, w * 0.24, h * 0.37);
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(w * 0.80, h * 0.05); ctx.lineTo(w * 0.80, h * 0.42);
        ctx.moveTo(w * 0.68, h * 0.22); ctx.lineTo(w * 0.92, h * 0.22);
        ctx.stroke();
        // Blind cord (hazard)
        ctx.strokeStyle = '#a07040';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 3]);
        ctx.beginPath(); ctx.moveTo(w * 0.82, h * 0.05); ctx.lineTo(w * 0.82, h * 0.50); ctx.stroke();
        ctx.setLineDash([]);

        // Light through window
        const winLight = ctx.createLinearGradient(w * 0.68, 0, w, 0);
        winLight.addColorStop(0, 'rgba(255,240,180,0)');
        winLight.addColorStop(1, 'rgba(255,240,180,0.12)');
        ctx.fillStyle = winLight;
        ctx.fillRect(0, 0, w, h * 0.62);

        // ── Rug / play zone glow (~14%,28%) ─────────────
        const rugGrad = ctx.createRadialGradient(w*0.32, h*0.48, 0, w*0.32, h*0.48, w*0.22);
        rugGrad.addColorStop(0, 'rgba(200,148,70,0.45)');
        rugGrad.addColorStop(1, 'rgba(200,148,70,0)');
        ctx.fillStyle = rugGrad;
        ctx.fillRect(w*0.08, h*0.22, w*0.44, h*0.42);

        // ── Sofa ────────────────────────────────────────
        ctx.fillStyle = '#8a6845';
        ctx.fillRect(w * 0.12, h * 0.44, w * 0.55, h * 0.20);
        ctx.fillStyle = '#7a5838';
        ctx.fillRect(w * 0.12, h * 0.42, w * 0.55, h * 0.06);
        ctx.fillStyle = '#9e7a52';
        ctx.fillRect(w * 0.14, h * 0.46, w * 0.24, h * 0.16);
        ctx.fillRect(w * 0.42, h * 0.46, w * 0.22, h * 0.16);

        // ── Coffee table (hazard, ~28%,42%) ─────────────
        ctx.fillStyle = '#7a4020';
        ctx.fillRect(w * 0.24, h * 0.55, w * 0.26, h * 0.09);
        ctx.fillStyle = '#5a2c10';
        ctx.fillRect(w * 0.25, h * 0.63, w * 0.03, h * 0.04);
        ctx.fillRect(w * 0.46, h * 0.63, w * 0.03, h * 0.04);

        // ── Wall lamp (left) ────────────────────────────
        ctx.fillStyle = '#c8a060';
        ctx.fillRect(w * 0.05, h * 0.29, w * 0.04, h * 0.18);
        ctx.fillStyle = '#fffacd';
        ctx.beginPath();
        ctx.moveTo(w*0.02, h*0.29); ctx.lineTo(w*0.11, h*0.29);
        ctx.lineTo(w*0.09, h*0.17); ctx.lineTo(w*0.04, h*0.17);
        ctx.closePath(); ctx.fill();
        // Glow
        const lampG = ctx.createRadialGradient(w*0.065, h*0.23, 0, w*0.065, h*0.23, w*0.10);
        lampG.addColorStop(0, 'rgba(255,245,180,0.4)');
        lampG.addColorStop(1, 'rgba(255,245,180,0)');
        ctx.fillStyle = lampG;
        ctx.fillRect(0, h*0.12, w*0.18, h*0.24);

        // ── Socket (floor level, ~5%,72%) ───────────────
        ctx.fillStyle = '#e8d4a8';
        ctx.fillRect(w*0.03, h*0.70, w*0.07, h*0.06);
        ctx.strokeStyle = '#b09050';
        ctx.lineWidth = 1;
        ctx.strokeRect(w*0.03, h*0.70, w*0.07, h*0.06);
        ctx.fillStyle = '#80603a';
        ctx.fillRect(w*0.044, h*0.72, w*0.013, h*0.02);
        ctx.fillRect(w*0.062, h*0.72, w*0.013, h*0.02);

        // Wall texture
        ctx.strokeStyle = 'rgba(180,150,80,0.12)';
        ctx.lineWidth = 1;
        for (let y = h * 0.12; y < h * 0.62; y += h * 0.08) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
        }
    }

    function _drawHallway(ctx, w, h) {
        const cx = w * 0.50, cy = h * 0.38;

        // ── Ceiling ──────────────────────────────────────
        ctx.fillStyle = '#e2ddd6';
        ctx.beginPath();
        ctx.moveTo(0, 0); ctx.lineTo(w, 0);
        ctx.lineTo(cx + w*0.16, cy - h*0.13);
        ctx.lineTo(cx - w*0.16, cy - h*0.13);
        ctx.closePath(); ctx.fill();

        // ── Left wall ────────────────────────────────────
        ctx.fillStyle = '#cec9c2';
        ctx.beginPath();
        ctx.moveTo(0, 0); ctx.lineTo(cx - w*0.16, cy - h*0.13);
        ctx.lineTo(cx - w*0.11, cy + h*0.12); ctx.lineTo(0, h);
        ctx.closePath(); ctx.fill();
        // Grab rail suggestion area dashed border (~5%,28%)
        ctx.strokeStyle = 'rgba(130,110,90,0.35)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 4]);
        ctx.strokeRect(w*0.01, h*0.25, w*0.16, h*0.46);
        ctx.setLineDash([]);

        // ── Right wall ───────────────────────────────────
        const rwGrad = ctx.createLinearGradient(cx + w*0.11, 0, w, 0);
        rwGrad.addColorStop(0, '#beb9b2');
        rwGrad.addColorStop(1, '#6a6560');
        ctx.fillStyle = rwGrad;
        ctx.beginPath();
        ctx.moveTo(w, 0); ctx.lineTo(cx + w*0.16, cy - h*0.13);
        ctx.lineTo(cx + w*0.11, cy + h*0.12); ctx.lineTo(w, h);
        ctx.closePath(); ctx.fill();

        // ── Floor ────────────────────────────────────────
        const floorG = ctx.createLinearGradient(0, h, 0, cy + h*0.12);
        floorG.addColorStop(0, '#6a6560');
        floorG.addColorStop(1, '#8a8480');
        ctx.fillStyle = floorG;
        ctx.beginPath();
        ctx.moveTo(0, h); ctx.lineTo(cx - w*0.11, cy + h*0.12);
        ctx.lineTo(cx + w*0.11, cy + h*0.12); ctx.lineTo(w, h);
        ctx.closePath(); ctx.fill();
        // Floor tile lines
        ctx.strokeStyle = 'rgba(90,85,80,0.25)';
        ctx.lineWidth = 1;
        for (let i = 1; i <= 4; i++) {
            const t = i / 5;
            const ly = cy + h*0.12 + (h - cy - h*0.12) * (1-t);
            const lx = (0 - (cx-w*0.11)) * t + (cx-w*0.11);
            const rx = (w - (cx+w*0.11)) * t + (cx+w*0.11);
            ctx.beginPath(); ctx.moveTo(lx, ly); ctx.lineTo(rx, ly); ctx.stroke();
        }

        // ── Back wall + door ─────────────────────────────
        ctx.fillStyle = '#b0a89e';
        ctx.fillRect(cx - w*0.16, cy - h*0.13, w*0.32, h*0.25);
        ctx.fillStyle = '#a09080';
        ctx.fillRect(cx - w*0.08, cy - h*0.11, w*0.14, h*0.24);
        ctx.strokeStyle = '#806858';
        ctx.lineWidth = 2;
        ctx.strokeRect(cx - w*0.08, cy - h*0.11, w*0.14, h*0.24);
        // Door panels
        ctx.strokeStyle = 'rgba(70,58,44,0.4)';
        ctx.lineWidth = 1;
        ctx.strokeRect(cx - w*0.06, cy - h*0.09, w*0.10, h*0.09);
        ctx.strokeRect(cx - w*0.06, cy + h*0.02, w*0.10, h*0.09);
        // Knob
        ctx.fillStyle = '#c8a878';
        ctx.beginPath(); ctx.arc(cx + w*0.04, cy + h*0.02, 4, 0, Math.PI*2); ctx.fill();

        // ── Loose rug (~20%,48%) ─────────────────────────
        ctx.save();
        ctx.translate(w*0.38, h*0.60);
        ctx.scale(1, 0.35);
        ctx.fillStyle = 'rgba(140,80,40,0.6)';
        ctx.beginPath(); ctx.ellipse(0, 0, w*0.26, h*0.24, 0, 0, Math.PI*2); ctx.fill();
        ctx.strokeStyle = 'rgba(180,110,60,0.8)';
        ctx.lineWidth = 4;
        ctx.stroke();
        ctx.restore();

        // ── Ceiling light ────────────────────────────────
        ctx.fillStyle = '#fffacd';
        ctx.beginPath(); ctx.arc(cx, cy - h*0.11, 10, 0, Math.PI*2); ctx.fill();
        const glow = ctx.createRadialGradient(cx, cy - h*0.11, 0, cx, cy - h*0.11, w*0.18);
        glow.addColorStop(0, 'rgba(255,248,200,0.55)');
        glow.addColorStop(1, 'rgba(255,248,200,0)');
        ctx.fillStyle = glow;
        ctx.beginPath(); ctx.arc(cx, cy - h*0.11, w*0.18, 0, Math.PI*2); ctx.fill();
    }

    function _drawClassroom(ctx, w, h) {
        // Minimal light-grey classroom sketch — just enough context for zones to read clearly

        // ── Wall (upper 60%) ─────────────────────────────
        ctx.fillStyle = '#e8e8e8';
        ctx.fillRect(0, 0, w, h * 0.60);

        // ── Floor (lower 40%) ────────────────────────────
        ctx.fillStyle = '#d4d0c8';
        ctx.fillRect(0, h * 0.60, w, h * 0.40);

        // Floor perspective lines
        ctx.strokeStyle = 'rgba(160,155,145,0.35)';
        ctx.lineWidth = 1;
        for (let i = 1; i <= 5; i++) {
            const ty = h * 0.60 + (h * 0.40) * (i / 6);
            ctx.beginPath(); ctx.moveTo(0, ty); ctx.lineTo(w, ty); ctx.stroke();
        }

        // ── Whiteboard outline only (~8%,5%) ─────────────
        ctx.strokeStyle = '#aaaaaa';
        ctx.lineWidth = 2;
        ctx.strokeRect(w * 0.05, h * 0.05, w * 0.46, h * 0.36);
        // Tray strip
        ctx.fillStyle = '#cccccc';
        ctx.fillRect(w * 0.05, h * 0.39, w * 0.46, h * 0.02);
    }

    // ── Video Controls ──
    const btnRecordVideo = document.getElementById('btn-record-video');
    const inputVideoFile = document.getElementById('video-file-input');

    if (btnRecordVideo) {
        btnRecordVideo.addEventListener('click', async () => {
            if (AuraCamera.isCurrentlyRecording()) {
                const blob = await AuraCamera.stopRecording();
                if (blob) handleVideoUpload(blob);
            } else {
                AuraCamera.startRecording();
            }
        });
    }

    if (inputVideoFile) {
        inputVideoFile.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) handleVideoUpload(file, true);
        });
    }

    let currentVideoAnalysis = null;

    async function handleVideoUpload(videoData, isFile = false) {
        // Reset demo state — video upload is always a real scan
        _demoProfile = null;
        window.currentUserId = 'default';
        document.querySelectorAll('.demo-chip').forEach(c => c.classList.remove('active'));
        document.getElementById('demo-scan-action').classList.add('hidden');
        document.getElementById('demo-profile-bar').classList.add('hidden');

        const videoUserId = 'default';

        // ── Zone overlay: extract middle frame and fire zone analysis ──────────
        const overlay    = document.getElementById('zone-overlay');
        const viewfinder = document.querySelector('.camera-viewfinder');
        const ow = viewfinder.clientWidth;
        const oh = viewfinder.clientHeight;
        overlay.width  = ow;
        overlay.height = oh;
        const ctx = overlay.getContext('2d');

        // Extract middle frame from the video client-side
        let frameBlob = null;
        try {
            frameBlob = await _extractMiddleFrame(videoData);
        } catch (e) {
            console.warn('[Aura Video] Frame extraction failed:', e);
        }

        // Draw frame (or black fallback) + loading state on overlay
        if (frameBlob) {
            await _drawBlobOnCanvas(ctx, frameBlob, ow, oh);
        } else {
            ctx.fillStyle = '#111';
            ctx.fillRect(0, 0, ow, oh);
        }
        ctx.fillStyle = 'rgba(0,0,0,0.45)';
        ctx.fillRect(0, 0, ow, oh);
        ctx.fillStyle = '#c084fc';
        ctx.font = 'bold 15px "Plus Jakarta Sans", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Identifying zones\u2026', ow / 2, oh / 2);

        overlay.classList.add('visible');
        document.getElementById('btn-clear-zones').classList.remove('hidden');
        document.getElementById('video-controls').classList.add('hidden');

        // Fire zone analysis on the extracted frame (non-blocking — runs in parallel)
        if (frameBlob) {
            AuraAPI.analyseZones(frameBlob, videoUserId).then(async zoneResult => {
                _currentZones = zoneResult.zones || [];
                ctx.clearRect(0, 0, ow, oh);
                await _drawBlobOnCanvas(ctx, frameBlob, ow, oh);
                _drawZones(overlay, _currentZones);
                _renderZoneReport(zoneResult);
                document.getElementById('zone-report').classList.remove('hidden');
            }).catch(err => {
                console.error('[Aura Video] Zone analysis failed:', err);
                ctx.clearRect(0, 0, ow, oh);
                _drawBlobOnCanvas(ctx, frameBlob, ow, oh);
            });
        }

        // ── Text analysis panel: full video upload ─────────────────────────────
        _resetAnalysisState();
        document.getElementById('result-description').textContent = 'Analysing video frames (this may take a minute)…';
        document.getElementById('result-objects').innerHTML = '<span class="shimmer" style="width:60px;height:20px;display:inline-block"></span>';
        document.getElementById('result-suggestions').innerHTML = '<div class="shimmer" style="height:60px;margin-bottom:8px"></div>'.repeat(3);
        document.getElementById('score-section').style.display = 'none';
        document.getElementById('room-label-row').style.display = 'flex';
        _showAnalysisPanel();
        currentVideoAnalysis = null;

        try {
            const result = isFile
                ? await AuraAPI.uploadVideoFile(videoData, null, videoUserId)
                : await AuraAPI.uploadVideo(videoData, null, videoUserId);

            const analysis = result.analysis || {};
            currentVideoAnalysis = analysis;

            document.getElementById('result-description').textContent =
                analysis.description || 'Video analysed successfully.';

            const objContainer = document.getElementById('result-objects');
            objContainer.innerHTML = '';
            if (analysis.objects_detected && analysis.objects_detected.length) {
                analysis.objects_detected.forEach(obj => {
                    const tag = document.createElement('span');
                    tag.className = 'result-tag';
                    tag.textContent = obj;
                    objContainer.appendChild(tag);
                });
            } else {
                objContainer.innerHTML = '<span class="result-tag">No objects detected</span>';
            }

            const sugContainer = document.getElementById('result-suggestions');
            sugContainer.innerHTML = '';
            if (analysis.suggestions && analysis.suggestions.length) {
                analysis.suggestions.forEach((s, i) => {
                    const item = document.createElement('div');
                    item.className = 'suggestion-item';
                    item.innerHTML = `
                        <span class="suggestion-num">${i + 1}</span>
                        <span class="suggestion-text">${typeof s === 'string' ? s : (s.action || JSON.stringify(s))}</span>
                    `;
                    sugContainer.appendChild(item);
                });
            } else {
                sugContainer.innerHTML = '<p style="color:var(--text-secondary);font-size:var(--fs-sm)">No specific suggestions at this time.</p>';
            }

            // Space Score ring
            if (analysis.score) {
                document.getElementById('score-section').style.display = 'block';
                document.getElementById('score-number').textContent  = analysis.score.overall || 0;
                document.getElementById('score-light').textContent   = analysis.score.light   || 0;
                document.getElementById('score-air').textContent     = analysis.score.air     || 0;
                document.getElementById('score-safety').textContent  = analysis.score.safety  || 0;
                document.getElementById('score-comfort').textContent = analysis.score.comfort || 0;
                setTimeout(() => {
                    document.getElementById('score-ring').style.strokeDasharray =
                        `${analysis.score.overall || 0}, 100`;
                }, 100);
                document.getElementById('score-diff').textContent = '';
            }

        } catch (err) {
            console.error('[Aura Video] Text analysis failed:', err);
            document.getElementById('result-description').textContent =
                'Video analysis failed. Please ensure the backend supports OpenCV and Gemma.';
            document.getElementById('result-objects').innerHTML = '';
            document.getElementById('result-suggestions').innerHTML = '';
        }
    }

    // Save Room Label
    const btnSaveRoom = document.getElementById('btn-save-room-label');
    if (btnSaveRoom) {
        btnSaveRoom.addEventListener('click', async () => {
            const label = document.getElementById('room-label-input').value.trim();
            if (!label) return;
            
            btnSaveRoom.textContent = '...';
            try {
                // Pass the saved analytics so they attach to the room
                await AuraAPI.labelRoom(label, '', currentVideoAnalysis);
                btnSaveRoom.textContent = 'Saved ✓';
                setTimeout(() => {
                    document.getElementById('room-label-row').style.display = 'none';
                    btnSaveRoom.textContent = 'Save 💾';
                }, 2000);
            } catch {
                btnSaveRoom.textContent = 'Error';
            }
        });
    }

    // ═══════════════════════════════════════════════
    // TIPS — Load & Filter
    // ═══════════════════════════════════════════════

    const allTips = [
        { icon: '💡', title: 'Mirror Light Trick', desc: 'Place a mirror directly opposite your brightest window. It effectively doubles the natural light reaching the darker side of the room.', category: 'lighting' },
        { icon: '🌿', title: '15-Minute Fresh Air', desc: 'Even on cold Irish days, opening windows for 15 minutes improves indoor air quality dramatically. The SEAI recommends this daily.', category: 'air_quality' },
        { icon: '🛡️', title: 'Furniture Anchoring', desc: 'Tall bookshelves and dressers should be anchored to walls with anti-tip straps — critical for homes with young children.', category: 'safety' },
        { icon: '🛋️', title: 'Cozy Reading Corner', desc: 'Rearrange a chair near natural light with a small side table. Add a throw blanket you already have for a dedicated relaxation spot.', category: 'comfort' },
        { icon: '♿', title: 'Accessible Heights', desc: 'Move frequently used items — cups, keys, medications — to waist-height shelves. This reduces bending and reaching for everyone.', category: 'accessibility' },
        { icon: '🎯', title: 'Activity Zones', desc: 'Designate areas of a room for specific activities: a play corner, a reading nook, a crafts table. Clear boundaries reduce chaos.', category: 'activity' },
        { icon: '☀️', title: 'Track the Sun', desc: 'Notice which rooms get morning vs afternoon sun. Use the sunny room for your main activities to boost mood naturally.', category: 'lighting' },
        { icon: '🌿', title: 'Spider Plant Air Filter', desc: 'Spider plants and peace lilies are excellent natural air purifiers. Place one in every room — they thrive in Irish indoor conditions.', category: 'air_quality' },
        { icon: '🛡️', title: 'Stair Safety Check', desc: 'Ensure stair lighting is adequate and there are no loose items on steps. Consider contrast tape on top and bottom steps for visibility.', category: 'safety' },
        { icon: '🛋️', title: 'Clutter-Free Surfaces', desc: 'Clear flat surfaces of clutter. Keep only 1-3 intentional items per surface. It creates visual calm and reduces stress.', category: 'comfort' },
        { icon: '♿', title: 'Grip-Friendly Handles', desc: 'Replace small knobs with lever-style handles on frequently used doors and cabinets — easier for arthritic hands and children.', category: 'accessibility' },
        { icon: '🎯', title: 'Rotate Toys Weekly', desc: 'Store half of children\'s toys out of sight. Rotate weekly. Fewer visible toys = longer attention spans and easier tidying.', category: 'activity' },
    ];

    let currentFilter = 'all';

    async function loadTips(filter = currentFilter) {
        const list = document.getElementById('tips-list');
        list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary)"><span class="pulse-dot"></span> Generating personalised tips...</div>';
        
        let displayTips = [...allTips];
        try {
            const dynamic = await AuraAPI.getRecommendations();
            if (dynamic && dynamic.length > 0) {
                // Map API format to frontend format
                const mappedDynamic = dynamic.map(d => ({
                    icon: '✨',
                    title: d.title || 'Special Tip',
                    desc: d.description || 'Aura has a suggestion for you.',
                    category: d.category || 'comfort'
                }));
                // Prepend personalised tips
                displayTips = [...mappedDynamic, ...allTips];
            }
        } catch(e) {
            console.log("[Aura] Defaulting to static tips fallback.");
        }

        const filtered = filter === 'all' ? displayTips : displayTips.filter(t => t.category === filter);

        list.innerHTML = '';
        filtered.forEach(tip => {
            const card = document.createElement('div');
            card.className = 'tip-list-card';
            card.setAttribute('data-category', tip.category);
            card.innerHTML = `
                <div class="tip-list-card-top">
                    <div class="tip-list-icon">${tip.icon}</div>
                    <div class="tip-list-content">
                        <h3>${tip.title}</h3>
                        <p>${tip.desc}</p>
                    </div>
                </div>
                <div class="tip-list-footer">
                    <span class="tip-category-badge">${tip.category.replace('_', ' ')}</span>
                    <span class="tip-learn-more">Learn more →</span>
                </div>
            `;
            card.addEventListener('click', () => {
                openChat();
                setTimeout(() => {
                    AuraChat.sendMessage(`Tell me more about: ${tip.title}`);
                }, 400);
            });
            list.appendChild(card);
        });
    }

    // ═══════════════════════════════════════════════
    // LIFESTYLE — Dynamic "Right Now" insights
    // ═══════════════════════════════════════════════

    async function loadLifestyle() {
        const section = document.getElementById('lifestyle-section');
        const carousel = document.getElementById('lifestyle-carousel');
        if (!section || !carousel) return;

        try {
            const data = await AuraAPI.getRecommendations();
            if (data && data.length > 0) {
                carousel.innerHTML = '';
                data.forEach(item => {
                    let icon = '✨';
                    if (item.category === 'lighting') icon = '☀️';
                    if (item.category === 'air_quality') icon = '🌿';
                    if (item.category === 'comfort') icon = '🛋️';
                    if (item.category === 'routine') icon = '🔄';

                    const card = document.createElement('div');
                    card.className = 'tip-card glass-card';
                    card.innerHTML = `
                        <div class="tip-icon">${icon}</div>
                        <div style="font-size: 0.75rem; color: var(--accent); margin-bottom: 2px;">${item.category.toUpperCase()}</div>
                        <h3>${item.title}</h3>
                        <p>${item.description}</p>
                    `;
                    carousel.appendChild(card);
                });
                section.style.display = 'block';
            }
        } catch(err) {
            console.error("Lifestyle load error:", err);
        }
    }

    // Filter chips
    document.getElementById('filter-chips').addEventListener('click', (e) => {
        const chip = e.target.closest('.filter-chip');
        if (!chip) return;

        document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentFilter = chip.dataset.filter;
        loadTips(currentFilter);
    });

    // Initial load
    loadTips();


    // ═══════════════════════════════════════════════
    // PROFILE — Load & Save (v2 — Household Cards + Accessibility)
    // ═══════════════════════════════════════════════

    let selectedSpaceType = '';
    let householdMembers = []; // Array of {name, age, notes}

    function renderHouseholdCards() {
        const container = document.getElementById('household-members');
        container.innerHTML = '';
        householdMembers.forEach((person, idx) => {
            const card = document.createElement('div');
            card.className = 'person-card';
            const initial = (person.name || '?')[0].toUpperCase();
            const agePart = person.age ? ` (${person.age})` : '';
            const notesPart = person.notes ? ` · ${person.notes}` : '';
            card.innerHTML = `
                <div class="person-avatar">${initial}</div>
                <div class="person-info">
                    <div class="person-name">${person.name}${agePart}</div>
                    <div class="person-meta">${notesPart || 'No notes'}</div>
                </div>
                <button class="person-remove" data-idx="${idx}" aria-label="Remove">✕</button>
            `;
            container.appendChild(card);
        });

        // Attach remove handlers
        container.querySelectorAll('.person-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                householdMembers.splice(parseInt(btn.dataset.idx), 1);
                renderHouseholdCards();
            });
        });
    }

    // Add Person form toggle
    document.getElementById('btn-add-person').addEventListener('click', () => {
        document.getElementById('add-person-form').classList.add('visible');
        document.getElementById('person-name').focus();
    });

    document.getElementById('btn-cancel-person').addEventListener('click', () => {
        document.getElementById('add-person-form').classList.remove('visible');
    });

    document.getElementById('btn-confirm-person').addEventListener('click', () => {
        const name = document.getElementById('person-name').value.trim();
        const age = document.getElementById('person-age').value.trim();
        const notes = document.getElementById('person-notes').value.trim();
        if (!name) return;

        householdMembers.push({ name, age, notes });
        renderHouseholdCards();

        // Clear form
        document.getElementById('person-name').value = '';
        document.getElementById('person-age').value = '';
        document.getElementById('person-notes').value = '';
        document.getElementById('add-person-form').classList.remove('visible');
    });

    // Accessibility "Other" toggle
    const otherCheck = document.getElementById('a11y-other-check');
    if (otherCheck) {
        otherCheck.addEventListener('change', () => {
            document.getElementById('a11y-other-text').style.display = otherCheck.checked ? 'block' : 'none';
        });
    }

    async function loadProfile() {
        try {
            const profile = await AuraAPI.getProfile();
            if (!profile) return;
            
            // Fetch evaluation accuracy
            try {
                const evalResponse = await AuraAPI.getEvaluation('default');
                if (evalResponse && evalResponse.overall_score !== undefined) {
                    const pct = Math.round(evalResponse.overall_score * 100);
                    document.getElementById('accuracy-score').textContent = `${pct}%`;
                    document.getElementById('accuracy-badge-container').style.display = 'block';
                }
            } catch (e) {
                console.log('No evaluation available yet.');
            }

            // Household Members (array of dicts)
            if (profile.household_members && Array.isArray(profile.household_members)) {
                householdMembers = profile.household_members;
                renderHouseholdCards();
            }

            if (profile.interests) {
                document.getElementById('input-interests').value =
                    Array.isArray(profile.interests) ? profile.interests.join(', ') : profile.interests;
            }
            if (profile.space_type) {
                selectedSpaceType = profile.space_type;
                document.querySelectorAll('.space-type-btn').forEach(b => {
                    b.classList.toggle('selected', b.dataset.type === selectedSpaceType);
                });
            }

            // Accessibility checkboxes
            if (profile.accessibility_needs && Array.isArray(profile.accessibility_needs)) {
                profile.accessibility_needs.forEach(need => {
                    const checkbox = document.querySelector(`#accessibility-grid input[value="${need}"]`);
                    if (checkbox) checkbox.checked = true;
                    if (need === 'Other') {
                        document.getElementById('a11y-other-text').style.display = 'block';
                    }
                });
                // If there's an "other_text" field
                if (profile.accessibility_other) {
                    document.getElementById('a11y-other-text').value = profile.accessibility_other;
                }
            }
        } catch {
            // No profile yet
        }
    }

    // Space type selection
    document.getElementById('space-type-grid').addEventListener('click', (e) => {
        const btn = e.target.closest('.space-type-btn');
        if (!btn) return;

        document.querySelectorAll('.space-type-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        selectedSpaceType = btn.dataset.type;
    });

    // Save profile
    document.getElementById('btn-save-profile').addEventListener('click', async () => {
        const btn = document.getElementById('btn-save-profile');
        
        // Collect accessibility needs
        const accessibilityNeeds = [];
        document.querySelectorAll('#accessibility-grid input[type="checkbox"]:checked').forEach(cb => {
            accessibilityNeeds.push(cb.value);
        });

        const data = {
            household_members: householdMembers,
            interests: document.getElementById('input-interests').value
                .split(',').map(s => s.trim()).filter(Boolean),
            space_type: selectedSpaceType,
            accessibility_needs: accessibilityNeeds,
        };

        try {
            await AuraAPI.updateProfile('default', data);
            btn.textContent = '✓ Saved!';
            btn.classList.add('saved');
            
            // Reload tips and lifestyle dynamically since profile changed
            loadTips();
            loadLifestyle();
            loadWeather();  // Also refreshes outdoor places with new profile
            
            setTimeout(() => {
                btn.textContent = 'Save Profile';
                btn.classList.remove('saved');
            }, 2000);
        } catch {
            btn.textContent = 'Error — try again';
            setTimeout(() => {
                btn.textContent = 'Save Profile';
            }, 2000);
        }
    });


    // ═══════════════════════════════════════════════
    // SEASONAL BANNER (Oct-Mar)
    // ═══════════════════════════════════════════════

    (function initSeasonalBanner() {
        const month = new Date().getMonth() + 1; // 1-12
        if (month >= 10 || month <= 3) {
            const banner = document.getElementById('seasonal-banner');
            if (banner) banner.style.display = 'flex';
        }
    })();


    // ═══════════════════════════════════════════════
    // HOME — Mood Insight Persistence
    // ═══════════════════════════════════════════════

    (function restoreMoodInsight() {
        const savedInsight = localStorage.getItem('aura_mood_insight');
        if (savedInsight) {
            const card = document.getElementById('home-mood-insight');
            const text = document.getElementById('mood-insight-text');
            if (card && text) {
                text.textContent = savedInsight;
                card.style.display = 'block';
            }
        }
    })();


    // ═══════════════════════════════════════════════
    // CHAT BOTTOM SHEET
    // ═══════════════════════════════════════════════

    const chatSheet = document.getElementById('chat-sheet');

    function openChat() {
        chatSheet.classList.add('open');
    }

    function closeChat() {
        chatSheet.classList.remove('open');
    }

    // Expose openChat globally for the mood selector
    window.openChat = openChat;

    document.getElementById('fab-chat').addEventListener('click', openChat);
    document.getElementById('btn-close-chat').addEventListener('click', closeChat);
    document.getElementById('chat-overlay').addEventListener('click', closeChat);

    // Chat send
    const chatInput = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-chat-send');

    btnSend.addEventListener('click', () => {
        const text = chatInput.value.trim();
        if (!text) return;
        AuraChat.sendMessage(text);
        chatInput.value = '';
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            btnSend.click();
        }
    });

    // Voice input
    const btnMic = document.getElementById('btn-chat-mic');
    if (btnMic) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            
            recognition.onstart = () => {
                btnMic.style.color = 'var(--error)'; // Turn red while listening
                chatInput.placeholder = 'Listening...';
            };
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                chatInput.value = transcript;
                btnSend.click(); // Auto send after speaking
            };
            
            recognition.onend = () => {
                btnMic.style.color = 'currentColor';
                chatInput.placeholder = 'Ask Aura anything…';
            };
            
            btnMic.addEventListener('click', () => {
                recognition.start();
            });
        } else {
            btnMic.style.display = 'none'; // Hide if browser doesn't support it
        }
    }


    // ═══════════════════════════════════════════════
    // SERVICE WORKER
    // ═══════════════════════════════════════════════

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(() => console.log('[Aura] SW registered'))
            .catch(err => console.log('[Aura] SW failed:', err));
    }

});
