"""
Mood Activities Engine — Comprehensive spatial wellness recommendations.
12 categories of environmental actions mapped to each mood state.
Profile-adaptive: adjusts suggestions based on user's specific situation.
"""

import random

# ═══════════════════════════════════════════════════════
# ACTIVITY DATABASE — 12 Categories
# ═══════════════════════════════════════════════════════

ACTIVITIES = {
    "ventilation": {
        "icon": "🌬️",
        "label": "Fresh Air",
        "suggestions": [
            "Open the window for 10 minutes — fresh air boosts both energy and clarity.",
            "Try cross-ventilation: open two windows on opposite sides for a quick air refresh.",
            "Step to the window, take 3 deep breaths of fresh air. Even 30 seconds helps.",
            "Air out the bathroom after a shower — trapped moisture causes stuffiness everywhere.",
            "If it's raining, crack the window open just 2cm — you still get fresh air without getting wet.",
        ],
    },
    "lighting": {
        "icon": "💡",
        "label": "Light Adjustment",
        "suggestions": {
            "stressed": "Switch to warm, dim lighting — soft yellow tones calm the nervous system.",
            "tired": "Turn on the brightest light you have. Bright white light tells your brain it's time to be awake.",
            "anxious": "Soft, warm lighting. Avoid overhead fluorescents. A side lamp is your friend right now.",
            "calm": "Light a candle if you have one. The gentle flicker creates a meditative atmosphere.",
            "energetic": "Open ALL the curtains! Let every bit of natural light flood in.",
            "creative": "Natural light from the side is ideal for creative work. Avoid direct overhead light.",
            "sad": "Open the curtains all the way — even grey daylight is 10x brighter than indoor light.",
            "angry": "Step to the window. Natural light has a physiological calming effect.",
            "happy": "Enjoy the light you have. If it's sunny, sit in the warm spot for a few minutes!",
            "focused": "Cool white task lighting on your work area. Dim everything else — spotlight effect.",
        },
    },
    "temperature": {
        "icon": "🌡️",
        "label": "Temperature",
        "suggestions": [
            "If the room feels stuffy, open a window briefly — even 2 minutes makes a difference.",
            "Cold? Wrap a blanket around your shoulders. Warming your core calms the whole body.",
            "Hot and restless? Splash cold water on your wrists — it cools you down fast.",
            "The ideal room temperature for focus is 18-21°C. Adjust if you can.",
            "Cold feet? Put on socks. Warm feet = better sleep and relaxation.",
        ],
    },
    "sound": {
        "icon": "🎵",
        "label": "Sound & Music",
        "suggestions": {
            "stressed": "Try nature sounds — rain, ocean waves, or forest ambience. These slow your heart rate.",
            "tired": "Put on something upbeat. Energising music can physically wake you up.",
            "anxious": "Lo-fi beats or ambient music. Predictable, gentle rhythms soothe anxiety.",
            "calm": "Classical piano or acoustic guitar. Or simply enjoy the silence.",
            "energetic": "Your favourite playlist! Dance in your room — seriously, it works.",
            "creative": "Instrumental music without lyrics. Words compete with your creative thoughts.",
            "sad": "Gentle, warm music. Not sad music — music that feels like a hug.",
            "angry": "Something with a strong beat to channel the energy, then gradually slow it down.",
            "happy": "Sing along to your favourite song. Let the joy flow!",
            "focused": "White noise or brown noise. Or try 'study beats' — consistent tempo, no lyrics.",
        },
    },
    "aromatherapy": {
        "icon": "🌸",
        "label": "Scent & Aroma",
        "suggestions": {
            "stressed": "Lavender or chamomile — even smelling a herbal tea bag helps.",
            "tired": "Peppermint or citrus (orange, lemon). Fresh, sharp scents wake you up.",
            "anxious": "Lavender, vanilla, or chamomile. Warm, familiar scents ground you.",
            "calm": "Sandalwood, vanilla, or cinnamon. Deep, warm scents deepen relaxation.",
            "energetic": "Eucalyptus or rosemary. Invigorating and clarifying.",
            "creative": "Lemon or grapefruit. Citrus scents stimulate creative thinking.",
            "sad": "Vanilla or orange. Comforting, warm scents lift the spirits.",
            "angry": "Peppermint or eucalyptus. Cool scents have a calming physiological effect.",
            "happy": "Whatever you love most! Rose, jasmine, or fresh coffee.",
            "focused": "Rosemary or peppermint. Both improve concentration and memory.",
        },
    },
    "position": {
        "icon": "🧘",
        "label": "Body Position",
        "suggestions": {
            "stressed": "Sit down, lean back, put your feet up. Let gravity take the tension away.",
            "tired": "Stand up and stretch. Reach for the ceiling, then touch your toes. Reset your body.",
            "anxious": "Sit on the floor, back against the wall. Feel the solid surface grounding you.",
            "calm": "Lie down on the floor for 2 minutes. Just breathe and stare at the ceiling.",
            "energetic": "Stand by the window. Look out at the world. Take in the view with a deep breath.",
            "creative": "Change your usual position — sit somewhere different. New perspective = new ideas.",
            "sad": "Wrap yourself in a blanket. Sit in your favourite corner. You deserve comfort right now.",
            "angry": "Stand up. Walk to another room. Physical movement channels frustration.",
            "happy": "Find the sunniest spot in your home and just be there for a moment.",
            "focused": "Sit upright, both feet on the floor, desk at elbow height. Your spine drives your focus.",
        },
    },
    "declutter": {
        "icon": "🧹",
        "label": "Tidy & Organise",
        "suggestions": [
            "Clear 3 items off your desk or table. It takes 30 seconds and feels amazing.",
            "Make your bed (if you haven't). It sets a 'complete' tone for the whole day.",
            "Put one thing back where it belongs. Just one. A tiny bit of order grows into calm.",
            "Clear the kitchen counter. A clean surface where you prepare food lifts your mood.",
            "Sort one drawer. The satisfaction of finding things easily — tiny joy, big impact.",
        ],
    },
    "nature": {
        "icon": "🌿",
        "label": "Nature Connection",
        "suggestions": [
            "Water your plant. Touch the soil. Connecting with something living grounds you.",
            "Look out the window for 30 seconds. Watch the sky, the trees, the light changing.",
            "If you have a plant, move it to where you can see it from your seat. Green calms the mind.",
            "Open the window and listen. Birds, wind, rain — nature's soundtrack is free therapy.",
            "Touch something natural: wood, stone, cotton. Synthetic-free texture resets sensory overload.",
        ],
    },
    "hydration": {
        "icon": "💧",
        "label": "Drink & Nourish",
        "suggestions": [
            "Drink a glass of water right now. Dehydration makes stress, tiredness, and anxiety worse.",
            "Make yourself a warm cup of tea. The ritual itself is calming — kettle, cup, waiting, warmth.",
            "If you haven't eaten in 3+ hours, grab a small snack. Low blood sugar tanks your mood.",
            "Keep your water bottle visible on your desk. You drink 40% more when you can see it.",
            "Hot chocolate, warm milk, or herbal tea — warm drinks activate comfort signals in the brain.",
        ],
    },
    "grounding": {
        "icon": "🧠",
        "label": "Grounding Technique",
        "suggestions": {
            "stressed": "5-4-3-2-1: Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.",
            "anxious": "Press your feet firmly into the floor. Feel the ground. You are here. You are safe.",
            "angry": "Run cold water over your hands for 30 seconds. The shock resets your nervous system.",
            "sad": "Hold something warm — a mug, a hot water bottle. Warmth signals safety to your brain.",
            "tired": "Splash cold water on your face. The 'dive reflex' instantly improves alertness.",
            "calm": "Close your eyes. Take 3 breaths: in for 4 counts, hold for 4, out for 6.",
            "energetic": "Feel your feet on the ground. Channel that energy with intention.",
            "creative": "Touch different textures around you — smooth, rough, soft. Sensory input sparks ideas.",
            "happy": "Pause and notice the feeling. Where do you feel happiness in your body? Savour it.",
            "focused": "Put both hands flat on the desk. Feel the surface. Bring your attention to NOW.",
        },
    },
    "cozy": {
        "icon": "🛋️",
        "label": "Comfort & Cozy",
        "suggestions": [
            "Grab a blanket or throw. Drape it over your lap or shoulders. Instant comfort upgrade.",
            "Arrange your cushions. Stack them behind your back. A supported spine = a calmer mind.",
            "If you have fairy lights or a small lamp, turn them on. Ambient light makes spaces feel safe.",
            "Create your cozy corner: blanket + cushion + warm drink + soft light. Your recharge station.",
            "Put on the softest clothes you own. Comfort from the inside out.",
        ],
    },
    "movement": {
        "icon": "🏃",
        "label": "Move & Stretch",
        "suggestions": [
            "Stand up and stretch. Arms up, reach for the ceiling, hold for 10 seconds. Breathe.",
            "Walk to a different room and back. Physical movement changes mental state.",
            "Roll your shoulders 5 times forward, 5 times back. Release the tension you're holding.",
            "Stand at the window for 2 minutes. Just stand. Look outside. Breathe.",
            "Do 10 gentle squats. Not intense — just enough to get blood flowing to your brain.",
            "Neck stretches: tilt your head to each shoulder, hold for 10 seconds. Tension melts away.",
        ],
    },
}


# ═══════════════════════════════════════════════════════
# MOOD → CATEGORY PRIORITY MAPPING
# ═══════════════════════════════════════════════════════

MOOD_PRIORITIES = {
    "stressed":  ["ventilation", "position", "aromatherapy", "sound", "grounding", "cozy"],
    "tired":     ["lighting", "hydration", "movement", "temperature", "nature", "sound"],
    "anxious":   ["grounding", "position", "sound", "ventilation", "cozy", "aromatherapy"],
    "calm":      ["aromatherapy", "nature", "cozy", "declutter", "sound", "position"],
    "energetic": ["movement", "lighting", "ventilation", "declutter", "nature", "sound"],
    "creative":  ["lighting", "declutter", "sound", "nature", "position", "aromatherapy"],
    "sad":       ["cozy", "sound", "nature", "hydration", "position", "lighting"],
    "angry":     ["ventilation", "movement", "grounding", "sound", "position", "nature"],
    "happy":     ["nature", "movement", "sound", "ventilation", "lighting", "cozy"],
    "focused":   ["declutter", "lighting", "sound", "temperature", "hydration", "position"],
}


def get_mood_activities(mood: str, count: int = 3, profile: dict = None) -> list[dict]:
    """Get a list of spatial activity recommendations for the given mood.
    Returns dicts with keys: icon, category, suggestion.
    Adapts seamlessly to user profile (mobility, children, age)."""

    mood = mood.lower()
    priorities = MOOD_PRIORITIES.get(mood, MOOD_PRIORITIES["calm"])
    activities = []
    
    # 1. Determine constraints from profile
    constraints = []
    if profile:
        from backend.core.group_rules import detect_groups
        groups = detect_groups(profile)
        if "disability_motor" in groups or "elderly" in groups:
            constraints.append("no_high_reach")
            constraints.append("no_floor_sitting")
            constraints.append("low_intensity_movement")
        if "disability_visual" in groups:
            constraints.append("no_rearrange")
        if "child" in groups:
            constraints.append("child_safe")

    for category in priorities:
        if len(activities) >= count:
            break
            
        cat_data = ACTIVITIES.get(category, {})
        raw_suggestions = cat_data.get("suggestions", [])

        # Get the right suggestion pool (dict or list)
        if isinstance(raw_suggestions, dict):
            suggestion_pool = raw_suggestions.get(mood) or raw_suggestions.get("calm", "Take a moment for yourself.")
            suggestion_pool = [suggestion_pool] if isinstance(suggestion_pool, str) else suggestion_pool
        elif isinstance(raw_suggestions, list):
            suggestion_pool = raw_suggestions
        else:
            suggestion_pool = ["Take a moment for yourself."]

        # 2. Filter suggestion pool against constraints
        valid_suggestions = []
        for s in suggestion_pool:
            s_lower = s.lower()
            is_valid = True
            
            if "no_high_reach" in constraints and any(w in s_lower for w in ["reach for the ceiling", "tall"]):
                is_valid = False
            if "no_floor_sitting" in constraints and any(w in s_lower for w in ["sit on the floor", "lie down", "squat"]):
                is_valid = False
            if "low_intensity_movement" in constraints and any(w in s_lower for w in ["squats", "dance", "jump"]):
                is_valid = False
            if "no_rearrange" in constraints and any(w in s_lower for w in ["move", "rearrange", "clear"]):
                is_valid = False
                
            if is_valid:
                valid_suggestions.append(s)

        if not valid_suggestions:
            continue # Skipped this category because of constraints

        suggestion = random.choice(valid_suggestions)

        # 3. Enhance phrasing gently based on specific profile needs
        if "child_safe" in constraints and "music" in suggestion:
            suggestion += " (Headphones work well if little ones are asleep!)"

        activities.append({
            "icon": cat_data.get("icon", "✨"),
            "category": cat_data.get("label", category),
            "suggestion": suggestion,
        })

    return activities


# ═══════════════════════════════════════════════════════
# MOOD → CONVERSATION STYLE (injected into system prompt)
# ═══════════════════════════════════════════════════════

MOOD_STYLES = {
    "stressed": {
        "tone": "calm, gentle, and reassuring",
        "approach": "Slow down. Use short, soothing sentences. Acknowledge their stress first before offering any advice. Suggest ONE thing, not a list.",
        "opening": "I can see things feel heavy right now. Let's take it one step at a time.",
    },
    "tired": {
        "tone": "warm, understanding, and energising",
        "approach": "Be empathetic about their tiredness. Don't overload them. Suggest quick, easy wins. Bright and light suggestions.",
        "opening": "I hear you — tiredness makes everything harder. Let me help with something easy.",
    },
    "anxious": {
        "tone": "safe, steady, and grounding",
        "approach": "Use predictable, structured language. Avoid overwhelming choices. Provide concrete, simple steps. Reassure them.",
        "opening": "You're okay. Let's focus on something small and manageable right now.",
    },
    "calm": {
        "tone": "warm, thoughtful, and reflective",
        "approach": "Match their calm energy. You can go deeper into topics. Suggest meditative or creative activities.",
        "opening": "What a lovely mood to be in. Let's make the most of this peaceful moment.",
    },
    "energetic": {
        "tone": "enthusiastic, positive, and action-oriented",
        "approach": "Match their energy! Suggest active things. Be direct and dynamic. More exclamation marks are okay.",
        "opening": "Love that energy! Let's channel it into something great for your space!",
    },
    "creative": {
        "tone": "inspiring, open, and imaginative",
        "approach": "Encourage their creativity. Suggest space transformations they can do right now. Be visual in descriptions.",
        "opening": "Ooh, creative mode! Your space has so much potential — let's play with it.",
    },
    "sad": {
        "tone": "deeply empathetic, gentle, and comforting",
        "approach": "Never minimise their feelings. Don't say 'cheer up'. Offer comfort first, advice second. Physical comfort suggestions (blankets, warmth, soft things).",
        "opening": "I'm here. We all have days like this. Let me help make your space feel like a warm hug.",
    },
    "angry": {
        "tone": "calm, non-judgmental, and redirecting",
        "approach": "Acknowledge the anger without feeding it. Suggest physical release (movement, fresh air). Then gradually calm the environment.",
        "opening": "I feel you. Let's use that energy — sometimes the best thing is a change of scene.",
    },
    "happy": {
        "tone": "joyful, celebratory, and light",
        "approach": "Share their joy! Suggest enhancing the good mood with environment optimisation. Keep it light and fun.",
        "opening": "That's wonderful! Happy days deserve a happy space. Let me add to the good vibes!",
    },
    "focused": {
        "tone": "efficient, clear, and supportive",
        "approach": "Be concise. Support their focus — don't break it with long responses. Practical, quick tips only.",
        "opening": "Focus mode — I'll keep this short and useful.",
    },
}


def get_mood_conversation_style(mood: str, profile: dict = None) -> str:
    """Generate the mood-specific conversation style block for the system prompt."""
    mood = mood.lower()
    style = MOOD_STYLES.get(mood, MOOD_STYLES["calm"])

    prompt = f"""[CURRENT MOOD: {mood.upper()}]
Your conversation tone must be: {style['tone']}.
Approach: {style['approach']}
Suggested opening: "{style['opening']}"
"""

    # Profile-adaptive language
    if profile:
        from backend.core.group_rules import detect_groups
        groups = detect_groups(profile)

        if "parent" in groups:
            prompt += """
[PARENT EMPATHY] This person is a parent. If their child is sleeping or occupied, acknowledge this:
"If the little one is settled, this is YOUR moment. Make it count 💛"
Always show you understand the constant juggling of parenthood.\n"""

        if "elderly" in groups:
            prompt += """
[ELDERLY EMPATHY] Be patient, clear, and respectful of independence.
Never assume inability. Phrase suggestions as choices: "You might find it helpful to..." not "You need to..."\n"""

        if "disability" in groups:
            prompt += """
[DISABILITY AWARENESS] Naturally adapt ALL suggestions to their specific needs.
Never draw attention to limitations. Focus on abilities and independence.\n"""

        if "solo_living" in groups:
            prompt += """
[SOLO LIVING] This person lives alone. They might appreciate feeling less alone through warm conversation.
"I'm here whenever you need a chat about your space."\n"""

        if "student" in groups:
            prompt += """
[STUDENT MODE] Keep it relatable and practical. Study breaks are important:
"Take a real break — step away from the desk. Your brain needs the reset."\n"""

        if "remote_worker" in groups:
            prompt += """
[REMOTE WORKER] Understand the work-day-at-home fatigue:
"Your desk isn't your whole world. Step away, even for 3 minutes, to a different room."\n"""

    return prompt
