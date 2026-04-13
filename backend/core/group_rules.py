"""
Group Rules Engine — Profile-specific spatial recommendation rules.
Each function returns a list of contextual rules that get injected
into the LLM system prompt based on the user's profile.

Supports 15+ user archetypes — from toddler parents to night-shift workers.
"""


def detect_groups(profile: dict) -> list[str]:
    """Auto-detect which groups apply to a user based on their profile data.
    A user can belong to multiple groups simultaneously."""
    groups = []
    if not profile:
        return ["general_adult"]

    members = profile.get("household_members", [])
    interests = [i.lower() for i in profile.get("interests", [])]
    concerns = (profile.get("concerns", "") or "").lower()
    accessibility = profile.get("accessibility_needs", [])
    space_type = (profile.get("space_type", "") or "").lower()
    age = profile.get("age")

    # --- Parse household members for children / elderly ---
    child_ages = []
    has_elderly = False
    member_count = 0

    if isinstance(members, list):
        for m in members:
            member_count += 1
            if isinstance(m, dict):
                m_age_str = str(m.get("age", ""))
                m_notes = (m.get("notes", "") or "").lower()
                try:
                    m_age = float(m_age_str)
                    if m_age < 18:
                        child_ages.append(m_age)
                    if m_age >= 65:
                        has_elderly = True
                except (ValueError, TypeError):
                    pass
                if any(k in m_notes for k in ["toddler", "baby", "infant", "child", "kid"]):
                    child_ages.append(2.0)  # default estimate

    # --- Assign groups ---
    if child_ages:
        groups.append("child")
        if any(a < 2 for a in child_ages):
            groups.append("child_baby")
        if any(2 <= a < 5 for a in child_ages):
            groups.append("child_toddler")
        if any(5 <= a < 12 for a in child_ages):
            groups.append("child_school")
        if any(12 <= a < 18 for a in child_ages):
            groups.append("child_teen")
        # Parent detection
        if member_count > len(child_ages):
            groups.append("parent")

    if has_elderly or (age and age >= 65):
        groups.append("elderly")

    if accessibility:
        groups.append("disability")
        for need in accessibility:
            need_lower = need.lower()
            if any(k in need_lower for k in ["motor", "mobility", "wheelchair", "walking"]):
                groups.append("disability_motor")
            if any(k in need_lower for k in ["visual", "blind", "sight", "vision"]):
                groups.append("disability_visual")
            if any(k in need_lower for k in ["hearing", "deaf", "audio"]):
                groups.append("disability_hearing")

    # Interest/concern-based groups
    if any(k in " ".join(interests + [concerns]) for k in ["remote", "work from home", "wfh", "office", "desk", "productivity"]):
        groups.append("remote_worker")

    if any(k in " ".join(interests + [concerns]) for k in ["study", "student", "exam", "university", "college", "school"]):
        groups.append("student")

    if any(k in " ".join(interests + [concerns]) for k in ["yoga", "meditation", "mindful", "wellness", "breathing"]):
        groups.append("wellness")

    if any(k in " ".join(interests + [concerns]) for k in ["fitness", "exercise", "gym", "workout", "sport"]):
        groups.append("fitness")

    if any(k in " ".join(interests + [concerns]) for k in ["art", "paint", "craft", "creative", "design", "music"]):
        groups.append("creative")

    if any(k in " ".join(interests + [concerns]) for k in ["pregnant", "pregnancy", "expecting", "baby on the way"]):
        groups.append("pregnant")

    if any(k in " ".join(interests + [concerns]) for k in ["pet", "dog", "cat", "animal"]):
        groups.append("pet_owner")

    if any(k in " ".join(interests + [concerns]) for k in ["night shift", "night work", "shift work", "nocturnal"]):
        groups.append("night_worker")

    if any(k in " ".join(interests + [concerns]) for k in ["couple", "partner", "spouse", "married"]):
        groups.append("couple")

    if member_count == 1 or (member_count == 0 and not child_ages):
        groups.append("solo_living")

    # If nothing specific detected, add general  
    if not groups:
        groups.append("general_adult")

    return list(set(groups))


# ═══════════════════════════════════════════════════════
# RULE SETS — each returns a string to inject into system prompt
# ═══════════════════════════════════════════════════════

def get_child_rules(child_ages: list[float] = None) -> str:
    rules = "[CHILD SAFETY ACTIVE]\n"

    if child_ages and any(a < 2 for a in child_ages):
        rules += """- Baby (0-2): ALL floor-level hazards are CRITICAL. Check for: small objects (choking), uncovered outlets, sharp furniture corners, dangling cords, unsecured heavy items.
- Recommend: soft corner protectors on tables, outlet covers, securing bookshelves to walls, removing small decorative items from reach.
- Floor should be soft and clean — suggest a play mat or blanket over hard floors.
- Crib/sleep area must be away from windows, cords, and direct sunlight.\n"""

    if child_ages and any(2 <= a < 5 for a in child_ages):
        rules += """- Toddler (2-5): Active climbers — ensure tall furniture is anchored. Remove climbable furniture near windows.
- Create a designated activity zone with clear boundaries (use rugs or tape to mark).
- Keep cleaning products, medications, and sharp items in unreachable/locked storage.
- Soft corners on coffee tables and low furniture. Stair gates if applicable.
- Rotation system for toys: keep half stored, swap weekly — reduces chaos and renews interest.\n"""

    if child_ages and any(5 <= a < 12 for a in child_ages):
        rules += """- School-age (5-12): Focus on study area ergonomics — proper desk height, good lighting, screen distance.
- Create a homework zone with minimal distractions, near natural light if possible.
- Eye health: 20-20-20 rule (every 20 min, look 20 feet away for 20 seconds).
- Still need safety basics but can start with organisation and responsibility zones.\n"""

    if child_ages and any(12 <= a < 18 for a in child_ages):
        rules += """- Teen (12-18): Privacy and personal space are essential for development.
- Help create their own organised zone — a desk, personal shelf, and lighting they control.
- Good sleep hygiene: no screens in bedroom 1 hour before sleep, blackout options.
- Study area with proper ergonomics and noise management.\n"""

    return rules


def get_elderly_rules() -> str:
    return """[ELDERLY SAFETY — HIGH PRIORITY]
- Fall prevention is THE #1 concern. Ensure: clear pathways (min 90cm), no loose rugs, no trailing cables.
- Lighting must be bright and consistent — especially hallways, stairs, bathroom. Motion-sensor lights at night.
- Frequently used items between waist and shoulder height — no reaching up or bending down.
- Grab rails in bathroom (toilet, shower). Non-slip mats in wet areas.
- Furniture should be stable, appropriate height for easy sitting/standing. Armrests help.
- Emergency access: phone within reach, clear path to exits, nothing blocking doors.
- Temperature: elderly are more sensitive to cold — ensure heating is accessible and even.
- Contrast colours on stairs (light vs dark) help with visibility.\n"""


def get_disability_rules(types: list[str] = None) -> str:
    rules = "[ACCESSIBILITY OVERRIDE — MANDATORY]\n"

    if not types:
        types = ["general"]

    if "disability_motor" in types or "general" in types:
        rules += """- Motor/Mobility: All pathways min 90cm clear. Furniture at wheelchair-accessible heights.
- Lever-style handles instead of knobs. Light switches at accessible height.
- Non-slip surfaces everywhere. Remove unnecessary obstacles.
- Consider reach zones: everything essential within arm's reach from seated position.\n"""

    if "disability_visual" in types:
        rules += """- Visual: High-contrast colours for edges, switches, and obstacles.
- Consistent furniture placement — NEVER suggest rearranging without explicit agreement.
- Texture differentiation on floors for zone identification (rugs mark different areas).
- Bright, even lighting without glare. Avoid reflective surfaces near light sources.
- Label systems: tactile or high-contrast labels on storage.\n"""

    if "disability_hearing" in types:
        rules += """- Hearing: Visual alert systems instead of sound-based ones (flashing lights for doorbells).
- Good sightlines throughout the home for visual communication.
- Reduce background noise: soft furnishings absorb echo.
- Ensure vibration-based alerts are possible (smart devices on hard surfaces).\n"""

    return rules


def get_parent_rules() -> str:
    return """[PARENT AWARENESS]
- You are speaking to a parent who balances their own needs with their child's safety.
- Acknowledge the challenge: "I know it's hard to have your own space when little ones need constant attention."
- Suggest dual-purpose areas: a reading corner where they can also watch the play zone.
- Self-care reminders: "If they're napping, this is YOUR 10 minutes — make it count 💛"
- Never make them feel guilty about wanting personal space.\n"""


def get_remote_worker_rules() -> str:
    return """[REMOTE WORK SPACE]
- Ergonomic desk setup: monitor at eye level, elbows at 90°, feet flat on floor.
- Separate work zone from living zone — even a visual divider (plant, shelf) helps the brain switch off.
- Natural light from the side (not behind screen, not in your eyes).
- 20-20-20 rule for eye strain: every 20 min, look 20 feet away for 20 sec.
- Background noise management: suggest quiet corners, or white noise.
- Cable management for clean visual space.
- "Leave your desk" reminders: move to a different room for breaks.\n"""


def get_student_rules() -> str:
    return """[STUDY ENVIRONMENT]
- Study desk near natural light, facing a wall (not window — reduces distraction).
- Minimal clutter on study surface — only current materials.
- Good task lighting: warm white for reading, cool white for alertness.
- Break reminders: Pomodoro technique (25 min study, 5 min break).
- A separate relaxation zone (bed/couch is NOT the study area).
- Noise: suggest quiet space or background white noise.
- Motivational corner: a small visible board with goals and progress.\n"""


def get_couple_rules() -> str:
    return """[SHARED LIVING]
- Balance shared and personal spaces — each person needs a corner that feels "theirs."
- Sleep environment: consider different temperature/light preferences (dual solutions).
- Shared activity areas: a cozy corner for evenings together.
- Storage: fair division of space, visible and organised.
- Communication tools: a shared calendar/board for household tasks.\n"""


def get_pregnant_rules() -> str:
    return """[PREGNANCY SAFETY]
- Avoid chemical odurs: suggest natural cleaning alternatives, good ventilation.
- Clear pathways — balance changes as pregnancy progresses.
- Comfortable seating with back support. Easy-to-adjust positions.
- Good lighting on stairs and hallways (night-time bathroom trips increase).
- Rest area accessible from main living space.
- Temperature sensitivity: easy access to ventilation and warmth control.
- Nesting zone: a calm, prepared area for the baby's arrival.\n"""


def get_pet_owner_rules() -> str:
    return """[PET-FRIENDLY SPACE]
- Remove toxic houseplants (lilies, pothos, philodendron) from pet reach.
- Secure cables and small objects that could be chewed.
- Designated pet zone with bed/mat — helps establish boundaries.
- Easy-to-clean floor surfaces near pet areas.
- Pet gates if certain rooms are off-limits.
- Storage for pet supplies that's easily accessible but tidy.\n"""


def get_fitness_rules() -> str:
    return """[HOME FITNESS SPACE]
- Clear floor area (min 2m x 2m) for exercises. Remove obstacles before workouts.
- Good ventilation for exercise: open window or fan during workouts.
- Mirror placement for form-checking if available.
- Mat storage: accessible but out of the way. Wall hooks work well.
- Stretching area near natural light — morning stretches by the window boost energy.
- Post-workout: ventilate the space to clear humidity.\n"""


def get_night_worker_rules() -> str:
    return """[NIGHT/SHIFT WORKER]
- Blackout solutions for daytime sleep: thick curtains, eye mask, door draught excluder for light leaks.
- Consistent sleep environment regardless of outside light.
- Bright light exposure during "morning" (whenever your day starts) to reset circadian rhythm.
- Separate "awake" and "sleep" lighting: cool white for activity, warm dim for wind-down.
- Meal preparation area that's functional without waking others (quiet zones).
- Minimize disruption: soft-close doors, rugs on hard floors in shared areas.\n"""


def get_solo_rules() -> str:
    return """[SOLO LIVING]
- Safety: ensure someone can reach you — phone charged and nearby.
- Create distinct zones even in small spaces: sleeping, living, working (prevents monotony).
- Social corner: a welcoming seating area for when visitors come.
- Self-care space: a bathroom or corner that feels like a mini spa (candles, plants, texture).
- Mood management: varied lighting for different times of day (energising mornings, cozy evenings).
- Personalisation: make the space fully yours — it should reflect your personality.\n"""


def get_creative_rules() -> str:
    return """[CREATIVE SPACE]
- Inspiration wall: a board or wall area for pinning ideas, images, textures.
- Natural light quality matters: north-facing is best for consistent light (no harsh shadows).
- Materials storage: visible but organised — seeing your materials sparks creativity.
- Allow "creative mess" in the work zone, but keep the rest tidy for mental clarity.
- Good task lighting for detail work. Adjustable lamp preferred.
- Music/sound: a way to play background music without disturbing others.\n"""


def get_wellness_rules() -> str:
    return """[WELLNESS / MEDITATION]
- Quiet corner: a dedicated calm space with minimal visual clutter.
- Soft textures: cushion, mat, or blanket on the floor.
- Natural elements: a plant, a stone, or a water feature (even a small bowl of water).
- Aromatherapy-ready: space for essential oil diffuser or candles.
- Face east if possible for morning meditation (sunrise direction).
- Sound isolation: if noisy area, suggest soft furnishings to absorb sound.
- Warm lighting: avoid overhead — use floor lamp or candles.\n"""


def get_general_adult_rules() -> str:
    return """[GENERAL WELLNESS BASELINE]
- Everyone benefits from: natural light, fresh air, clear pathways, and organised spaces.
- Ventilation: open windows 15 min daily even in cold weather — dramatically improves air quality.
- Light: maximise natural light during the day, warm tones in the evening.
- Temperature: 18-21°C is ideal for most activities, 16-18°C for sleeping.
- Clutter: clear surfaces reduce stress. 1-3 items per surface is the sweet spot.
- Plants: even one indoor plant improves air quality and mood.
- Ergonomics: wherever you sit most, ensure good posture support.
- Hydration point: keep water visible and accessible (you drink more when you see it).\n"""


# ═══════════════════════════════════════════════════════
# MAIN FUNCTION — called by llm.py
# ═══════════════════════════════════════════════════════

def build_group_prompt(profile: dict) -> str:
    """Build the complete group-specific rules block for the system prompt."""
    if not profile:
        return get_general_adult_rules()

    groups = detect_groups(profile)
    rules_parts = []

    # Extract child ages for child-specific rules
    child_ages = []
    members = profile.get("household_members", [])
    if isinstance(members, list):
        for m in members:
            if isinstance(m, dict):
                try:
                    age = float(str(m.get("age", "")))
                    if age < 18:
                        child_ages.append(age)
                except (ValueError, TypeError):
                    pass

    # Build rules based on detected groups
    if "child" in groups:
        rules_parts.append(get_child_rules(child_ages))
    if "parent" in groups:
        rules_parts.append(get_parent_rules())
    if "elderly" in groups:
        rules_parts.append(get_elderly_rules())
    if "disability" in groups:
        rules_parts.append(get_disability_rules(groups))
    if "remote_worker" in groups:
        rules_parts.append(get_remote_worker_rules())
    if "student" in groups:
        rules_parts.append(get_student_rules())
    if "couple" in groups:
        rules_parts.append(get_couple_rules())
    if "pregnant" in groups:
        rules_parts.append(get_pregnant_rules())
    if "pet_owner" in groups:
        rules_parts.append(get_pet_owner_rules())
    if "fitness" in groups:
        rules_parts.append(get_fitness_rules())
    if "night_worker" in groups:
        rules_parts.append(get_night_worker_rules())
    if "solo_living" in groups:
        rules_parts.append(get_solo_rules())
    if "creative" in groups:
        rules_parts.append(get_creative_rules())
    if "wellness" in groups:
        rules_parts.append(get_wellness_rules())
    if "general_adult" in groups:
        rules_parts.append(get_general_adult_rules())

    # Always include general baseline if not already there
    if "general_adult" not in groups:
        rules_parts.append(get_general_adult_rules())

    return "\n".join(rules_parts)
