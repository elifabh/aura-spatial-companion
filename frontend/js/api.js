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

        /** Upload an image for spatial analysis. */
        async analyseImage(imageBlob, userId = 'default') {
            const formData = new FormData();
            formData.append('image', imageBlob, 'capture.jpg');
            formData.append('user_id', userId);

            const response = await fetch(`${BASE_URL}/camera/analyse`, {
                method: 'POST',
                body: formData,
            });

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

        /** Health check. */
        async healthCheck() {
            return request('/health');
        },
    };
})();
