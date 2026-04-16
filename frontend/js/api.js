/**
 * Aura API Client
 * Handles all communication with the FastAPI backend.
 */

const AuraAPI = (() => {
    const BASE_URL = '/api';

    async function request(endpoint, options = {}) {
        try {
            const response = await fetch(`${BASE_URL}${endpoint}`, {
                headers: { 'Content-Type': 'application/json' },
                ...options,
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`[Aura API] ${endpoint}:`, error);
            throw error;
        }
    }

    return {
        /** Send a chat message and get Aura's reply. */
        async sendMessage(message, userId = 'default') {
            return request('/chat/send', {
                method: 'POST',
                body: JSON.stringify({ message, user_id: userId }),
            });
        },

        /** Get conversation history. */
        async getHistory(userId = 'default', limit = 20) {
            return request(`/chat/history/${userId}?limit=${limit}`);
        },

        /** Upload an image for spatial analysis (with optional compass heading). */
        async analyseImage(imageBlob, userId = 'default', compassHeading = null, lat = null, lon = null) {
            const formData = new FormData();
            formData.append('image', imageBlob, 'capture.jpg');
            formData.append('user_id', userId);

            let url = `${BASE_URL}/camera/analyse`;
            const params = new URLSearchParams();
            if (compassHeading !== null) params.append('compass_heading', compassHeading);
            if (lat !== null) params.append('lat', lat);
            if (lon !== null) params.append('lon', lon);
            if (params.toString()) url += '?' + params.toString();

            const response = await fetch(url, { method: 'POST', body: formData });
            if (!response.ok) throw new Error(`API error: ${response.status}`);
            return response.json();
        },

        /** Get current weather. */
        async getWeather(lat = 53.3498, lon = -6.2603) {
            return request(`/weather/current?lat=${lat}&lon=${lon}`);
        },

        /** Get sun position. */
        async getSunPosition(lat = 53.3498, lon = -6.2603) {
            return request(`/weather/sun?lat=${lat}&lon=${lon}`);
        },

        /** Get user profile. */
        async getProfile(userId = 'default') {
            return request(`/profile/${userId}`);
        },

        /** Update user profile. */
        async updateProfile(userId, data) {
            return request(`/profile/${userId}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },

        /** Generate recommendations. */
        async getRecommendations(userId = 'default', context = '') {
            return request('/recommendations/generate', {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, context }),
            });
        },

        /** Log a mood to the server and detect patterns. */
        async logMood(mood, weatherData, sunData, userId = 'default') {
            return request(`/profile/${userId}/mood`, {
                method: 'POST',
                body: JSON.stringify({
                    mood: mood,
                    weather_data: JSON.stringify(weatherData),
                    sun_data: JSON.stringify(sunData)
                }),
            });
        },

        /** Health check. */
        async healthCheck() {
            return request('/health');
        },

        /** Get Evaluation */
        async getEvaluation(userId = 'default') {
            return request(`/evaluate/${userId}`);
        },

        /** Upload a video blob for multi-frame room analysis. */
        async uploadVideo(videoBlob, roomLabel = null, userId = 'default') {
            const formData = new FormData();
            formData.append('video', videoBlob, 'recording.webm');
            formData.append('user_id', userId);
            if (roomLabel) formData.append('room_label', roomLabel);

            const res = await fetch(`${BASE_URL}/video/upload`, {
                method: 'POST',
                body: formData,
            });
            if (!res.ok) throw new Error(`Video upload failed: ${res.status}`);
            return res.json();
        },

        /** Upload a video file (from file input) for room analysis. */
        async uploadVideoFile(file, roomLabel = null, userId = 'default') {
            const formData = new FormData();
            formData.append('video', file, file.name);
            formData.append('user_id', userId);
            if (roomLabel) formData.append('room_label', roomLabel);

            const res = await fetch(`${BASE_URL}/video/upload`, {
                method: 'POST',
                body: formData,
            });
            if (!res.ok) throw new Error(`Video upload failed: ${res.status}`);
            return res.json();
        },

        /** Label a room manually (no video needed). */
        async labelRoom(roomLabel, description = '', analysis = null, userId = 'default') {
            return request('/video/label', {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, room_label: roomLabel, description, analysis }),
            });
        },

        /** Get all saved rooms for a user. */
        async getRooms(userId = 'default') {
            return request(`/video/rooms/${userId}`);
        },

        /** Get nearby parks/public spaces. */
        async getNearbyOutdoor(lat, lon, userId = 'default') {
            return request(`/outdoor/nearby?lat=${lat}&lon=${lon}&user_id=${userId}`);
        },

        /** Run zone analysis on an image blob — returns zones with coordinates and recommendations. */
        async analyseZones(imageBlob, userId = 'default') {
            const formData = new FormData();
            formData.append('image', imageBlob, 'capture.jpg');

            const url = `${BASE_URL}/camera/zone-analysis?user_id=${encodeURIComponent(userId)}`;
            const response = await fetch(url, { method: 'POST', body: formData });
            if (!response.ok) throw new Error(`Zone analysis error: ${response.status}`);
            return response.json();
        },

        /** Fetch pre-seeded demo zones for a profile without needing camera access. */
        async getDemoZones(userId) {
            return request(`/camera/demo-zones/${encodeURIComponent(userId)}`);
        },

        /** Mark a suggestion as completed — awards Aura Points and checks badges. */
        async completeSuggestion(suggestionText, userId = 'default') {
            return request('/gamification/complete', {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, suggestion_text: suggestionText }),
            });
        },
    };
})();
