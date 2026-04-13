"""
Demo Data Seeder — Creates 5 realistic demo profiles with synthetic time series data,
conversation histories, and trains the ROCKET classifier.
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta

from backend.db.sqlite import get_db_connection, log_conversation, log_mood
from backend.services.profile import update_user_profile


def seed_demo_profiles():
    """Create the 5 demo user profiles with full data."""

    profiles = {
        "sarah": {
            "name": "Sarah",
            "age": 34,
            "location": "Cork, Ireland",
            "space_type": "house",
            "household_members": [
                {"name": "Sarah", "age": "34", "notes": ""},
                {"name": "Cian", "age": "1.5", "notes": "toddler"}
            ],
            "accessibility_needs": [],
            "interests": ["reading", "crafts", "child development"],
            "concerns": "safe play space, child development",
        },
        "seamus": {
            "name": "Seamus",
            "age": 71,
            "location": "Galway, Ireland",
            "space_type": "house",
            "household_members": [
                {"name": "Seamus", "age": "71", "notes": "lives alone"}
            ],
            "accessibility_needs": ["Motor difficulties"],
            "interests": ["gardening", "reading", "radio"],
            "concerns": "mobility, independence",
        },
        "claire": {
            "name": "Claire",
            "age": 42,
            "location": "Dublin, Ireland",
            "space_type": "shared",
            "household_members": [],
            "accessibility_needs": [],
            "interests": ["education", "child engagement", "classroom design"],
            "concerns": "learning environment, child engagement",
        },
        "niamh": {
            "name": "Niamh",
            "age": 28,
            "location": "Limerick, Ireland",
            "space_type": "apartment",
            "household_members": [{"name": "Niamh", "age": "28", "notes": ""}],
            "accessibility_needs": [],
            "interests": ["yoga", "productivity", "minimalism"],
            "concerns": "morning routines, small spaces",
        },
        "liam": {
            "name": "Liam",
            "age": 55,
            "location": "Belfast, Northern Ireland",
            "space_type": "house",
            "household_members": [{"name": "Liam", "age": "55", "notes": ""}],
            "accessibility_needs": ["Visual impairment"],
            "interests": ["music", "cooking", "structure"],
            "concerns": "organising, clear pathways",
        },
    }

    for user_id, profile_data in profiles.items():
        update_user_profile(user_id, profile_data)
        print(f"[Seed] Created profile: {user_id}")

    return profiles


def seed_conversations():
    """Pre-load 5 conversation messages per demo profile."""
    # (Just keeping Sarah, Seamus, Claire for brevity, returning early for Niamh/Liam)
    conversations = {
         "sarah": [
            ("Cian keeps falling near the coffee table, help",
             "I understand your worry! For Cian's safety, I'd suggest moving the coffee table to the wall temporarily, or padding the corners with soft bumpers you may already have (like cut pool noodles). Create a clear play zone in the centre of the room."),
            ("Is the living room light okay for a toddler?",
             "At 18 months, Cian benefits from lots of natural light for development. Your south-facing window is great — keep curtains open during the day. Avoid harsh overhead lights in the evening; a warm lamp at child height creates a calming atmosphere."),
            ("How can I create a reading corner for myself too?",
             "Lovely idea! Use the corner near the window — a comfy chair, a small shelf, and a reading lamp. Position it where you can see Cian's play area. This way you get your quiet time while staying present."),
            ("It's been raining all week, Cian is restless indoors",
             "Rainy Cork days! Create an indoor obstacle course with cushions and tunnels from blankets. Rotate toys (put half away, swap next week — they feel new again). A sensory bin with rice or pasta keeps toddlers engaged for ages."),
            ("Aura noticed it's cloudy today — suggested indoor activity zone",
             "Yes! On overcast days, I proactively check light levels. Today's cloud cover means less natural light, so I'd turn on warm task lighting and set up an activity station near the brightest window. Cian's mood will benefit from the extra light."),
        ],
        "seamus": [
            ("I find it hard to get up from my armchair lately",
             "That's a common challenge. First, check your armchair height — your knees should be at 90°. You can raise it with furniture risers (or sturdy books temporarily). Also, place a stable side table next to it so you have something to push up from. Would you like me to suggest some simple exercises too?"),
            ("The bathroom tiles are slippery, worried about falling",
             "Very wise to address this. Non-slip bath mats are the quickest fix — you may already have rubber mats that could work. Also consider leaving a towel on the floor by the shower as a temporary measure. Grab rails by the toilet and shower are life-changing and often available free through the HSE."),
            ("Is there anything I can do about the dark hallway?",
             "Absolutely! Even without rewiring: place a battery-operated motion-sensor light (very affordable) at each end. Paint the walls a lighter colour if possible — even one accent wall helps. Keep the hallway completely clear of obstacles. A small mirror opposite any light source will bounce light further."),
            ("My daughter wants me to move but I want to stay independent",
             "Your independence matters enormously. Small adjustments can make home much safer: clear pathways, night lights, grab rails, and keeping daily items between waist and shoulder height. These changes often make the difference between needing to move and thriving at home. I'm here to help with each one."),
            ("Aura suggested moving the lamp — it really helped",
             "I'm so glad! Repositioning that lamp to illuminate the path between your chair and the kitchen was a simple change with big impact. Good lighting reduces fall risk by up to 50%. Let's look at the bedroom next — is the path to the bathroom well-lit at night?"),
        ],
        "claire": [
             ("My junior infants lose focus after 20 minutes",
             "Very normal for 4-5 year olds! Their attention span is roughly their age in minutes. Try breaking activities into 15-minute blocks with a physical movement break between each. A simple 'stand up, stretch, sit down' routine helps reset focus. Also, check if the lighting or temperature changes around that time."),
            ("The classroom gets very stuffy in the afternoon",
             "Stuffy air = drowsy students. Open windows for 5 minutes every hour (even in Irish weather, the fresh air burst helps). Position desks away from radiators. If you have a CO₂ monitor, ideal is under 1000ppm. Consider a small fan to circulate air without creating a draft on the children."),
            ("How should I arrange desks for group activities?",
             "For junior infants, clusters of 4-6 desks work best for group activities. Leave clear pathways between clusters (minimum 90cm for wheelchairs). Create a 'carpet area' for whole-class activities. The teacher's desk should face the room, near the door. Rotate seating monthly so children build different social connections."),
            ("One child has ADHD, how do I help without disrupting others?",
             "Beautiful question. Seat them near you but not isolated — second row, slightly off-centre works well. Create a 'calm corner' with headphones and fidget tools that ANY child can use (normalises it). Use visual timers for tasks. Reduce wall clutter near their desk. These changes actually help ALL children focus better, not just the one with ADHD."),
            ("Morning light is too harsh on the whiteboard",
             "The glare is likely from east-facing windows hitting the board directly. Options: angle the board slightly (even 10° helps), use a matte screen if available, or install a simple roller blind. Morning work could temporarily use the non-glare side of the room. After 10:30am, the sun angle changes and the issue often resolves itself."),
        ],
        "niamh": [
            ("I love mornings but my room feels dull", "Morning light is key to starting your day, maybe reposition your bed near the window?"),
            ("Can I add greenery?", "Yes, low-maintenance plants like snake plants thrive in low light.")
        ],
        "liam": [
            ("I keep tripping in the hallway", "Make sure there are no loose rugs, Liam. Consistency in furniture placement helps when vision is impaired."),
            ("Does lighting matter much?", "Yes, bright and consistent lighting without glare is essential.")
        ]
    }

    for user_id, convos in conversations.items():
        for user_msg, aura_reply in convos:
            log_conversation(user_id, user_msg, aura_reply)
        print(f"[Seed] Loaded {len(convos)} conversations for {user_id}")


def seed_synthetic_timeseries():
    """Generate 100 days of realistic mood + space score data for 5 profiles (500 points total)."""

    conn = get_db_connection()
    cursor = conn.cursor()
    base_date = datetime.now() - timedelta(days=100)

    # 1. Sarah: light_sensitive
    for day in range(100):
        dt = base_date + timedelta(days=day)
        is_cloudy = random.random() < 0.6  # High chance of clouds
        mood = random.choice(["stressed", "tired", "anxious"]) if is_cloudy else random.choice(["energetic", "calm", "creative"])
        hour = random.choice([7, 8, 9, 20, 21])
        ts = dt.replace(hour=hour, minute=random.randint(0, 59))
        weather = {"temperature": random.uniform(5, 15), "weather_code": 3 if is_cloudy else 1, "humidity": random.randint(60, 95)}
        sun = {"sun_altitude": random.uniform(10, 40) if not is_cloudy else random.uniform(5, 15), "is_daylight": hour < 20}

        cursor.execute("INSERT INTO mood_logs (user_id, mood, weather_data, sun_data, timestamp) VALUES (?, ?, ?, ?, ?)",
                       ("sarah", mood, json.dumps(weather), json.dumps(sun), ts.isoformat()))
        score = int(60 + (18 * day / 100) + random.randint(-3, 3))
        cursor.execute("INSERT INTO space_analyses (user_id, description, scores, timestamp) VALUES (?, ?, ?, ?)",
                       ("sarah", "Scan", json.dumps({"overall": score, "light": score}), ts.isoformat()))

    # 2. Seamus: seasonal_affected
    for day in range(100):
        dt = base_date + timedelta(days=day)
        is_winter = dt.month in [11, 12, 1, 2]
        mood = random.choice(["tired", "stressed"]) if is_winter else random.choice(["calm", "energetic"])
        hour = random.choice([9, 10, 15, 16])
        ts = dt.replace(hour=hour, minute=random.randint(0, 59))
        weather = {"temperature": random.uniform(2, 10) if is_winter else random.uniform(10, 16), "weather_code": 3 if is_winter else 1}
        sun = {"sun_altitude": random.uniform(5, 20) if is_winter else random.uniform(20, 45)}
        cursor.execute("INSERT INTO mood_logs (user_id, mood, weather_data, sun_data, timestamp) VALUES (?, ?, ?, ?, ?)",
                       ("seamus", mood, json.dumps(weather), json.dumps(sun), ts.isoformat()))
        score = int(45 + (20 * day / 100) + random.randint(-4, 4))
        cursor.execute("INSERT INTO space_analyses (user_id, description, scores, timestamp) VALUES (?, ?, ?, ?)",
                       ("seamus", "Scan", json.dumps({"overall": score}), ts.isoformat()))

    # 3. Claire: space_improver
    for day in range(100):
        dt = base_date + timedelta(days=day)
        mood = random.choice(["focused", "calm", "energetic", "creative"])
        hour = random.choice([7, 8, 16, 17])
        ts = dt.replace(hour=hour, minute=random.randint(0, 59))
        weather = {"temperature": random.uniform(8, 16), "weather_code": 1}
        sun = {"sun_altitude": random.uniform(15, 45)}
        cursor.execute("INSERT INTO mood_logs (user_id, mood, weather_data, sun_data, timestamp) VALUES (?, ?, ?, ?, ?)",
                       ("claire", mood, json.dumps(weather), json.dumps(sun), ts.isoformat()))
        score = int(40 + (45 * day / 100) + random.randint(-2, 2))  # Big steady improvement
        cursor.execute("INSERT INTO space_analyses (user_id, description, scores, timestamp) VALUES (?, ?, ?, ?)",
                       ("claire", "Scan", json.dumps({"overall": score}), ts.isoformat()))

    # 4. Niamh: morning_person
    for day in range(100):
        dt = base_date + timedelta(days=day)
        hour = random.choice([6, 7, 8, 20, 21, 22])
        is_morning = hour < 12
        mood = random.choice(["energetic", "creative", "focused"]) if is_morning else random.choice(["tired", "calm"])
        ts = dt.replace(hour=hour, minute=random.randint(0, 59))
        weather = {"temperature": 10, "weather_code": 1}
        sun = {"sun_altitude": 25}
        cursor.execute("INSERT INTO mood_logs (user_id, mood, weather_data, sun_data, timestamp) VALUES (?, ?, ?, ?, ?)",
                       ("niamh", mood, json.dumps(weather), json.dumps(sun), ts.isoformat()))
        score = int(70 + random.randint(-5, 5))
        cursor.execute("INSERT INTO space_analyses (user_id, description, scores, timestamp) VALUES (?, ?, ?, ?)",
                       ("niamh", "Scan", json.dumps({"overall": score}), ts.isoformat()))

    # 5. Liam: routine_seeker
    for day in range(100):
        dt = base_date + timedelta(days=day)
        hour = random.choice([8, 13, 19])  # Very consistent hours
        mood = random.choice(["calm", "focused"])
        ts = dt.replace(hour=hour, minute=random.randint(0, 59))
        weather = {"temperature": 12, "weather_code": 1}
        sun = {"sun_altitude": 30}
        cursor.execute("INSERT INTO mood_logs (user_id, mood, weather_data, sun_data, timestamp) VALUES (?, ?, ?, ?, ?)",
                       ("liam", mood, json.dumps(weather), json.dumps(sun), ts.isoformat()))
        score = int(80 + random.randint(-2, 2))  # Consistent high score
        cursor.execute("INSERT INTO space_analyses (user_id, description, scores, timestamp) VALUES (?, ?, ?, ?)",
                       ("liam", "Scan", json.dumps({"overall": score}), ts.isoformat()))

    conn.commit()
    conn.close()
    print("[Seed] Done! Generated 500 data points of synthetic time series data (100 per profile)")


def train_rocket_on_demo_data():
    """Train the ROCKET classifier on the synthetic demo data."""
    from backend.core.timeseries import AuraRocketClassifier

    classifier = AuraRocketClassifier()

    X_list = []
    y_list = []

    user_labels = {
        "sarah": "light_sensitive",
        "seamus": "seasonal_affected",
        "claire": "space_improver",
        "niamh": "morning_person",
        "liam": "routine_seeker"
    }

    for user_id, label in user_labels.items():
        features = classifier.build_features(user_id)
        if features is not None:
            X_list.append(features[0])  # Shape (5, T)
            y_list.append(label)

    if len(X_list) < 2:
        print("[Seed] Not enough data to train ROCKET.")
        return

    # Pad all to same length (max T)
    max_len = max(x.shape[1] for x in X_list)
    X_padded = []
    for x in X_list:
        if x.shape[1] < max_len:
            pad = np.zeros((x.shape[0], max_len - x.shape[1]))
            x = np.hstack([x, pad])
        X_padded.append(x)

    X = np.array(X_padded)  # (n_samples, 5, max_T)
    y = np.array(y_list)

    # Duplicate data to give ROCKET more training samples
    X_aug = np.tile(X, (5, 1, 1))  # 25 samples
    y_aug = np.tile(y, 5)

    # Add small noise for variation
    noise = np.random.normal(0, 0.1, X_aug.shape)
    X_aug = X_aug + noise

    classifier.fit(X_aug, y_aug)
    print("[Seed] Done! ROCKET classifier trained on demo data.")


def seed_all():
    """Run all seeding steps."""
    print("[Seed] Starting demo data seeding...")
    seed_demo_profiles()
    seed_conversations()
    seed_synthetic_timeseries()
    train_rocket_on_demo_data()
    print("[Seed] Done! All demo data seeded successfully!")

if __name__ == "__main__":
    from backend.db.sqlite import init_db
    init_db()
    seed_all()
