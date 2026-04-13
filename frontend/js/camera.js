/**
 * Aura Camera Module
 * Full-screen camera with rear-facing capture, analysis,
 * live video recording (MediaRecorder), and file upload.
 */

const AuraCamera = (() => {
    let stream = null;
    let mediaRecorder = null;
    let recordedChunks = [];
    let isRecording = false;

    const video = () => document.getElementById('camera-feed');
    const canvas = () => document.getElementById('camera-canvas');

    async function start() {
        if (stream) return;
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                },
            });
            const v = video();
            if (v) v.srcObject = stream;
        } catch (error) {
            console.error('[Aura Camera] Access denied:', error);
        }
    }

    function stop() {
        if (isRecording) stopRecording();
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            const v = video();
            if (v) v.srcObject = null;
        }
    }

    async function capture() {
        const v = video();
        const c = canvas();
        if (!v || !c) return null;

        c.width = v.videoWidth || 1280;
        c.height = v.videoHeight || 720;
        c.getContext('2d').drawImage(v, 0, 0);

        return new Promise(resolve => {
            c.toBlob(blob => resolve(blob), 'image/jpeg', 0.85);
        });
    }

    // ── Video Recording ─────────────────────────────────

    function startRecording() {
        if (!stream || isRecording) return;

        recordedChunks = [];
        const mimeType = (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported('video/webm;codecs=vp9'))
            ? 'video/webm;codecs=vp9'
            : 'video/webm';

        try {
            mediaRecorder = new MediaRecorder(stream, { mimeType });
            mediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) recordedChunks.push(e.data);
            };
            mediaRecorder.start(1000);
            isRecording = true;
            console.log('[Aura Camera] Recording started');

            const btn = document.getElementById('btn-record-video');
            if (btn) {
                btn.classList.add('recording');
                const lbl = btn.querySelector('.record-label');
                if (lbl) lbl.textContent = 'Stop ■';
            }
        } catch (e) {
            console.error('[Aura Camera] MediaRecorder error:', e);
        }
    }

    function stopRecording() {
        return new Promise((resolve) => {
            if (!mediaRecorder || !isRecording) { resolve(null); return; }
            mediaRecorder.onstop = () => {
                const blob = new Blob(recordedChunks, { type: 'video/webm' });
                recordedChunks = [];
                isRecording = false;
                console.log('[Aura Camera] Recording stopped, size:', blob.size);
                resolve(blob);

                const btn = document.getElementById('btn-record-video');
                if (btn) {
                    btn.classList.remove('recording');
                    const lbl = btn.querySelector('.record-label');
                    if (lbl) lbl.textContent = '● Record';
                }
            };
            mediaRecorder.stop();
        });
    }

    function isCurrentlyRecording() {
        return isRecording;
    }

    return { start, stop, capture, startRecording, stopRecording, isCurrentlyRecording };
})();
