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
            // Already onboarded, fade out immediately
            splash.classList.add('hidden');
        } else {
            // New user, show Get Started button after a short delay
            setTimeout(() => {
                btnGetStarted.classList.remove('hidden');
            }, 1000);
            
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
                        actContainer.appendChild(card);
                    });
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

        // Show results panel with loading state
        const resultsPanel = document.getElementById('analysis-results');
        document.getElementById('result-description').textContent = 'Analysing your space…';
        document.getElementById('result-objects').innerHTML = '<span class="shimmer" style="width:60px;height:20px;display:inline-block"></span>';
        document.getElementById('result-suggestions').innerHTML = '<div class="shimmer" style="height:60px;margin-bottom:8px"></div>'.repeat(3);
        resultsPanel.classList.remove('hidden');

        try {
            const result = await AuraAPI.analyseImage(blob);

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
                    
                    if (typeof s === 'object') {
                        item.innerHTML = `
                            <span class="suggestion-num">${i + 1}</span>
                            <div style="display:flex; flex-direction:column; gap: 4px;">
                                <span class="suggestion-text"><strong>${s.action || ''}</strong></span>
                                <span style="font-size: 0.8rem; color: var(--text-secondary);"><em>${s.why_this_matters || ''}</em></span>
                                <span style="font-size: 0.75rem; color: var(--text-tertiary);">Confidence: ${s.confidence || 0}%</span>
                            </div>
                        `;
                    } else {
                        item.innerHTML = `
                            <span class="suggestion-num">${i + 1}</span>
                            <span class="suggestion-text">${s}</span>
                        `;
                    }
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

    document.getElementById('btn-close-results').addEventListener('click', () => {
        document.getElementById('analysis-results').classList.add('hidden');
        document.getElementById('room-label-row').style.display = 'none';
        document.getElementById('room-label-input').value = '';
    });

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
        // Show loading state
        const resultsPanel = document.getElementById('analysis-results');
        document.getElementById('result-description').textContent = 'Analysing video frames (this may take a minute)…';
        document.getElementById('result-objects').innerHTML = '<span class="shimmer" style="width:60px;height:20px;display:inline-block"></span>';
        document.getElementById('result-suggestions').innerHTML = '<div class="shimmer" style="height:60px;margin-bottom:8px"></div>'.repeat(3);
        document.getElementById('score-section').style.display = 'none';
        document.getElementById('room-label-row').style.display = 'flex'; // Show room label input
        resultsPanel.classList.remove('hidden');
        currentVideoAnalysis = null;

        try {
            let result;
            if (isFile) {
                result = await AuraAPI.uploadVideoFile(videoData);
            } else {
                result = await AuraAPI.uploadVideo(videoData);
            }

            const analysis = result.analysis || {};
            currentVideoAnalysis = analysis;

            document.getElementById('result-description').textContent = analysis.description || 'Video analysed successfully.';

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

        } catch (err) {
            console.error("Video error:", err);
            document.getElementById('result-description').textContent = 'Video analysis failed. Please ensure the backend supports OpenCV and Gemma.';
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
