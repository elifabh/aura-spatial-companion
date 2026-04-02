/**
 * Aura Camera Module
 * Handles camera access, capture, and image upload.
 */

const AuraCamera = (() => {
    let stream = null;
    const video = () => document.getElementById('camera-feed');
    const canvas = () => document.getElementById('camera-canvas');

    async function start() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                },
            });
            video().srcObject = stream;
        } catch (error) {
            console.error('[Aura Camera] Access denied:', error);
            AuraChat.addAuraMessage(
                "I couldn't access your camera. Please check your browser permissions and try again."
            );
        }
    }

    function stop() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
    }

    function capture() {
        const v = video();
        const c = canvas();
        c.width = v.videoWidth;
        c.height = v.videoHeight;
        c.getContext('2d').drawImage(v, 0, 0);

        return new Promise(resolve => {
            c.toBlob(blob => resolve(blob), 'image/jpeg', 0.85);
        });
    }

    async function captureAndAnalyse() {
        const blob = await capture();
        if (!blob) return;

        // Close camera modal
        document.getElementById('camera-modal').classList.add('hidden');
        stop();

        // Show loading
        AuraChat.addAuraMessage('Analysing your space… 🔍');
        AuraChat.showTyping();

        try {
            const result = await AuraAPI.analyseImage(blob);
            AuraChat.hideTyping();

            let response = '';
            if (result.description) {
                response += `**What I see:** ${result.description}\n\n`;
            }
            if (result.objects_detected && result.objects_detected.length) {
                response += `**Objects spotted:** ${result.objects_detected.join(', ')}\n\n`;
            }
            if (result.suggestions && result.suggestions.length) {
                response += '**My suggestions:**\n';
                result.suggestions.forEach(s => {
                    response += `• ${s}\n`;
                });
            }

            AuraChat.addAuraMessage(response || "I've noted your space. Tell me more about what you'd like to improve!");
        } catch (error) {
            AuraChat.hideTyping();
            AuraChat.addAuraMessage(
                "I had trouble analysing that image. Make sure the backend is running and try again."
            );
        }
    }

    return { start, stop, capture, captureAndAnalyse };
})();
