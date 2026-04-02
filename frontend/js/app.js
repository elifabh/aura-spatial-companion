/**
 * Aura App — Main application controller.
 * Wires up all modules and handles user interactions.
 */

document.addEventListener('DOMContentLoaded', () => {

    // ── Elements ──────────────────────────────────
    const messageInput = document.getElementById('message-input');
    const btnSend      = document.getElementById('btn-send');
    const btnCamera    = document.getElementById('btn-camera');
    const btnProfile   = document.getElementById('btn-profile');

    const cameraModal  = document.getElementById('camera-modal');
    const profileModal = document.getElementById('profile-modal');

    const btnCloseCamera  = document.getElementById('btn-close-camera');
    const btnCloseProfile = document.getElementById('btn-close-profile');
    const btnCapture      = document.getElementById('btn-capture');
    const profileForm     = document.getElementById('profile-form');


    // ── Chat Input ────────────────────────────────
    btnSend.addEventListener('click', () => {
        AuraChat.sendMessage(messageInput.value);
        messageInput.value = '';
    });

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            btnSend.click();
        }
    });


    // ── Quick Actions (chips) ─────────────────────
    document.addEventListener('click', async (e) => {
        const chip = e.target.closest('.chip');
        if (!chip) return;

        const action = chip.dataset.action;

        switch (action) {
            case 'scan':
                cameraModal.classList.remove('hidden');
                AuraCamera.start();
                break;

            case 'tips':
                AuraChat.sendMessage("Give me a quick tip to improve my living space today.");
                break;

            case 'weather':
                AuraChat.showTyping();
                try {
                    const weather = await AuraAPI.getWeather();
                    AuraChat.hideTyping();
                    const desc = weather.weather_description || 'No data';
                    const temp = weather.temperature != null ? `${weather.temperature}°C` : 'N/A';
                    AuraChat.addAuraMessage(
                        `**Current weather:** ${desc}, ${temp}\n\n` +
                        "Based on today's weather, I can suggest how to best use natural light and ventilation in your space. Just ask!"
                    );
                } catch {
                    AuraChat.hideTyping();
                    AuraChat.addAuraMessage("I couldn't fetch the weather right now. Is the backend running?");
                }
                break;
        }
    });


    // ── Camera Modal ──────────────────────────────
    btnCamera.addEventListener('click', () => {
        cameraModal.classList.remove('hidden');
        AuraCamera.start();
    });

    btnCloseCamera.addEventListener('click', () => {
        cameraModal.classList.add('hidden');
        AuraCamera.stop();
    });

    cameraModal.querySelector('.modal-overlay').addEventListener('click', () => {
        cameraModal.classList.add('hidden');
        AuraCamera.stop();
    });

    btnCapture.addEventListener('click', () => {
        AuraCamera.captureAndAnalyse();
    });


    // ── Profile Modal ─────────────────────────────
    btnProfile.addEventListener('click', async () => {
        profileModal.classList.remove('hidden');

        // Try to load existing profile
        try {
            const profile = await AuraAPI.getProfile();
            if (profile) {
                document.getElementById('household').value =
                    (profile.household_members || []).join(', ');
                document.getElementById('mobility').value =
                    profile.mobility_notes || '';
                document.getElementById('interests').value =
                    (profile.interests || []).join(', ');
                document.getElementById('space-type').value =
                    profile.space_type || '';
            }
        } catch {
            // No profile yet — that's fine
        }
    });

    btnCloseProfile.addEventListener('click', () => {
        profileModal.classList.add('hidden');
    });

    profileModal.querySelector('.modal-overlay').addEventListener('click', () => {
        profileModal.classList.add('hidden');
    });

    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const data = {
            household_members: document.getElementById('household').value
                .split(',').map(s => s.trim()).filter(Boolean),
            mobility_notes: document.getElementById('mobility').value,
            interests: document.getElementById('interests').value
                .split(',').map(s => s.trim()).filter(Boolean),
            space_type: document.getElementById('space-type').value,
        };

        try {
            await AuraAPI.updateProfile('default', data);
            profileModal.classList.add('hidden');
            AuraChat.addAuraMessage(
                "Profile updated! I'll use this to give you more relevant suggestions. ✦"
            );
        } catch {
            AuraChat.addAuraMessage(
                "I couldn't save your profile right now. Please try again."
            );
        }
    });


    // ── Register Service Worker ───────────────────
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(() => console.log('[Aura] Service worker registered'))
            .catch(err => console.log('[Aura] SW registration failed:', err));
    }

});
