/**
 * Aura Orientation Module — Compass + Direction Detection
 * Uses DeviceOrientation API to get phone's compass heading.
 * Graceful fallback: if not available, everything still works.
 */

const AuraOrientation = (() => {
    let currentHeading = null;
    let isSupported = false;
    let isActive = false;

    /**
     * Get compass direction label from heading degrees
     */
    function getDirectionLabel(heading) {
        if (heading === null) return null;
        const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        const index = Math.round(heading / 45) % 8;
        return dirs[index];
    }

    /**
     * Request permission (required on iOS 13+)
     */
    async function requestPermission() {
        if (typeof DeviceOrientationEvent !== 'undefined' &&
            typeof DeviceOrientationEvent.requestPermission === 'function') {
            try {
                const permission = await DeviceOrientationEvent.requestPermission();
                return permission === 'granted';
            } catch {
                return false;
            }
        }
        // Android and other browsers don't need permission
        return true;
    }

    /**
     * Handle orientation event
     */
    function onOrientation(event) {
        // alpha = compass heading (0-360, where 0 = North)
        // webkitCompassHeading is more reliable on iOS
        let heading = event.webkitCompassHeading || event.alpha;

        if (heading !== null && heading !== undefined) {
            // On non-iOS, alpha is the rotation, not compass heading
            // We need to invert it for compass-like behavior
            if (!event.webkitCompassHeading && event.alpha !== null) {
                heading = (360 - event.alpha) % 360;
            }

            currentHeading = Math.round(heading);
            isSupported = true;

            // Update compass badge if visible
            updateBadge();
        }
    }

    /**
     * Update the compass badge UI on the scan screen
     */
    function updateBadge() {
        const badge = document.getElementById('compass-badge');
        if (!badge || currentHeading === null) return;

        const direction = getDirectionLabel(currentHeading);
        const arrow = badge.querySelector('.compass-arrow');
        const dirLabel = badge.querySelector('.compass-direction');
        const degLabel = badge.querySelector('.compass-degrees');

        if (arrow) arrow.style.transform = `rotate(${currentHeading}deg)`;
        if (dirLabel) dirLabel.textContent = direction;
        if (degLabel) degLabel.textContent = `${currentHeading}°`;

        badge.style.display = 'flex';
    }

    /**
     * Start listening to orientation events
     */
    async function start() {
        if (isActive) return;

        const granted = await requestPermission();
        if (!granted) {
            console.log('[Compass] Permission denied');
            return;
        }

        window.addEventListener('deviceorientation', onOrientation, true);
        isActive = true;
        console.log('[Compass] Listening for orientation events');
    }

    /**
     * Stop listening
     */
    function stop() {
        window.removeEventListener('deviceorientation', onOrientation, true);
        isActive = false;
    }

    /**
     * Get current heading (or null if unavailable)
     */
    function getHeading() {
        return currentHeading;
    }

    /**
     * Get direction label (or null)
     */
    function getDirection() {
        return getDirectionLabel(currentHeading);
    }

    /**
     * Check if compass is supported and active
     */
    function available() {
        return isSupported && isActive;
    }

    return {
        start,
        stop,
        getHeading,
        getDirection,
        available,
        requestPermission,
    };
})();
