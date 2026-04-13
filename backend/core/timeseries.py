"""
Time Series Classification — ROCKET (Random Convolutional Kernel Transform)
Uses the Aeon library to classify user wellness patterns from mood/environment data.
"""

import pickle
import numpy as np
from pathlib import Path
from datetime import datetime

from backend.config import DATA_DIR
from backend.db.sqlite import get_db_connection

MODEL_PATH = Path(DATA_DIR) / "rocket_model.pkl"

PATTERN_LABELS = [
    "light_sensitive",    # Feels worse on cloudy days
    "morning_person",     # More positive in AM
    "seasonal_affected",  # Oct-Mar mood drops
    "space_improver",     # Space score increasing over time
    "routine_seeker",     # Consistent daily patterns
]

MOOD_ENCODING = {
    "energetic": 5, "creative": 4, "calm": 3,
    "cozy": 3, "focused": 4,
    "tired": 1, "stressed": 1, "anxious": 1,
}


class AuraRocketClassifier:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                print("[ROCKET] Model loaded from disk.")
            except Exception as e:
                print(f"[ROCKET] Could not load model: {e}")

    def _save_model(self):
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.model, f)
        print("[ROCKET] Model saved to disk.")

    def build_features(self, user_id: str) -> np.ndarray | None:
        """
        Build multivariate time series from a user's mood/environment logs.
        Shape: (1, n_channels, n_timepoints) for aeon format.
        Channels: [mood_encoded, weather_code, sun_alt, hour, space_score]
        """
        import json
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get mood logs
        cursor.execute(
            "SELECT mood, weather_data, sun_data, timestamp FROM mood_logs WHERE user_id = ? ORDER BY timestamp",
            (user_id,)
        )
        mood_rows = cursor.fetchall()

        # Get space scores
        cursor.execute(
            "SELECT scores, timestamp FROM space_analyses WHERE user_id = ? ORDER BY timestamp",
            (user_id,)
        )
        score_rows = cursor.fetchall()
        conn.close()

        if len(mood_rows) < 7:
            return None

        # Build channels
        moods = []
        weather_codes = []
        sun_alts = []
        hours = []

        for mood_text, weather_json, sun_json, ts in mood_rows:
            moods.append(MOOD_ENCODING.get(mood_text, 2))

            try:
                wd = json.loads(weather_json) if weather_json else {}
                weather_codes.append(float(wd.get("weather_code", 0)))
            except Exception:
                weather_codes.append(0.0)

            try:
                sd = json.loads(sun_json) if sun_json else {}
                sun_alts.append(float(sd.get("sun_altitude", 30)))
            except Exception:
                sun_alts.append(30.0)

            try:
                dt = datetime.fromisoformat(ts)
                hours.append(float(dt.hour))
            except Exception:
                hours.append(12.0)

        # Space scores (pad or truncate to match mood length)
        space_scores = []
        for score_json, _ in score_rows:
            try:
                sc = json.loads(score_json) if score_json else {}
                space_scores.append(float(sc.get("overall", 50)))
            except Exception:
                space_scores.append(50.0)

        # Pad space_scores to match mood length
        while len(space_scores) < len(moods):
            space_scores.append(space_scores[-1] if space_scores else 50.0)
        space_scores = space_scores[:len(moods)]

        # Stack into (1, 5, T) array
        X = np.array([moods, weather_codes, sun_alts, hours, space_scores], dtype=np.float64)
        return X.reshape(1, 5, -1)

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train the ROCKET classifier on labelled time series data."""
        from aeon.classification.convolution_based import RocketClassifier
        self.model = RocketClassifier(n_kernels=500)
        self.model.fit(X, y)
        self._save_model()
        print(f"[ROCKET] Trained on {len(y)} samples.")

    def predict(self, user_id: str) -> str | None:
        """Predict the wellness pattern for a user."""
        if self.model is None:
            return None

        X = self.build_features(user_id)
        if X is None:
            return None

        try:
            prediction = self.model.predict(X)
            return prediction[0]
        except Exception as e:
            print(f"[ROCKET] Prediction error: {e}")
            return None

    def get_pattern_label(self, pattern: str) -> dict:
        """Get a human-readable description of a pattern."""
        descriptions = {
            "light_sensitive": {
                "label": "Light Sensitive",
                "emoji": "☁️",
                "description": "You tend to feel more tired or stressed on cloudy days. Maximising natural light in your space could really help.",
            },
            "morning_person": {
                "label": "Morning Person",
                "emoji": "🌅",
                "description": "You're most energetic and positive in the morning. Consider doing important tasks and space improvements early in the day.",
            },
            "seasonal_affected": {
                "label": "Seasonally Affected",
                "emoji": "🌧️",
                "description": "Your mood tends to drop during the darker months (Oct-Mar). Light therapy, mirrors, and warm lighting can make a big difference.",
            },
            "space_improver": {
                "label": "Space Improver",
                "emoji": "📈",
                "description": "Your space score has been steadily improving! Your changes are making a real difference to your environment.",
            },
            "routine_seeker": {
                "label": "Routine Seeker",
                "emoji": "🔄",
                "description": "You thrive on consistency. Keeping your space organised and predictable supports your wellbeing.",
            },
        }
        return descriptions.get(pattern, {
            "label": pattern.replace("_", " ").title(),
            "emoji": "✨",
            "description": "A unique pattern we're still learning about.",
        })


# Singleton
_classifier: AuraRocketClassifier | None = None

def get_classifier() -> AuraRocketClassifier:
    global _classifier
    if _classifier is None:
        _classifier = AuraRocketClassifier()
    return _classifier
