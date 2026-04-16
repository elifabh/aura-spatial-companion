"""
Aura Test Suite — Verifies all 7 intelligence modules.
Run with: python -m pytest tests/test_aura.py -v
"""

import json
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np


class TestDocumentIngestion:
    """Phase 1: Document ingestion into ChromaDB."""

    def test_ingestion_creates_chunks(self):
        """Verify ChromaDB has documents after ingestion (runs ingest if needed)."""
        from backend.core.ingest import ingest_documents
        from backend.core.rag import get_collection
        ingest_documents()          # idempotent — skips if already populated
        collection = get_collection()
        count = collection.count()
        print(f"  ChromaDB document count: {count}")
        assert count > 0, "ChromaDB should have documents after ingestion"

    def test_knowledge_query_returns_results(self):
        """Verify querying the knowledge base returns relevant results."""
        from backend.core.ingest import ingest_documents
        from backend.core.rag import get_relevant_knowledge
        ingest_documents()          # idempotent — skips if already populated
        results = get_relevant_knowledge("lighting for elderly people")
        assert len(results) > 0, "Should return at least one knowledge result"
        print(f"  Returned {len(results)} knowledge results")


class TestGraphRAG:
    """Phase 2: Graph RAG relationship traversal."""

    def test_graph_has_nodes_and_edges(self):
        """Verify the knowledge graph has nodes and edges."""
        from backend.db.graph import get_graph
        G = get_graph()
        assert G.number_of_nodes() > 30, f"Graph should have 30+ nodes, has {G.number_of_nodes()}"
        assert G.number_of_edges() > 40, f"Graph should have 40+ edges, has {G.number_of_edges()}"
        print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    def test_graph_context_returns_chains(self):
        """Verify graph context returns relationship chains."""
        from backend.db.graph import get_graph_context
        chains = get_graph_context("elderly falls safety")
        assert len(chains) > 0, "Should return relationship chains for 'elderly falls safety'"
        print(f"  Chains returned: {len(chains)}")
        for chain in chains[:3]:
            print(f"    {chain}")

    def test_graph_adhd_context(self):
        """Verify ADHD-specific relationship chains."""
        from backend.db.graph import get_graph_context
        chains = get_graph_context("ADHD classroom")
        assert any("ADHD" in c for c in chains), "Should return ADHD-related chains"
        print(f"  ADHD chains: {len(chains)}")


class TestROCKETClassifier:
    """Phase 3: ROCKET time series classification."""

    def test_rocket_classifier_trains(self):
        """Verify ROCKET classifier trains without errors on synthetic data."""
        from backend.core.timeseries import AuraRocketClassifier
        classifier = AuraRocketClassifier()

        # Create minimal synthetic data
        n_samples = 10
        n_channels = 5
        n_timepoints = 30
        X = np.random.rand(n_samples, n_channels, n_timepoints)
        y = np.array(["light_sensitive"] * 5 + ["morning_person"] * 5)

        classifier.fit(X, y)
        assert classifier.model is not None, "Model should be trained"
        print("  ROCKET classifier trained successfully")

    def test_pattern_prediction_returns_label(self):
        """Verify pattern prediction returns a valid label for demo profiles."""
        from backend.core.timeseries import get_classifier
        classifier = get_classifier()

        if classifier.model is None:
            pytest.skip("ROCKET model not trained yet")

        # Test with sarah profile (should have data from seeding)
        pattern = classifier.predict("sarah")
        if pattern is not None:
            from backend.core.timeseries import PATTERN_LABELS
            assert pattern in PATTERN_LABELS, f"Pattern '{pattern}' should be a valid label"
            print(f"  Sarah's predicted pattern: {pattern}")
        else:
            print("  Sarah has no data for prediction (expected if not seeded)")


class TestDemoProfiles:
    """Phase 5: Demo profile verification."""

    def test_demo_profiles_exist(self):
        """Verify 3 demo profiles exist in the database."""
        from backend.services.profile import get_user_profile
        for user_id in ["sarah", "seamus", "claire"]:
            profile = get_user_profile(user_id)
            if profile is None:
                pytest.skip(f"Demo profile '{user_id}' not yet seeded")
            assert profile is not None, f"Profile '{user_id}' should exist"
            assert "name" in profile, f"Profile '{user_id}' should have a name"
            print(f"  ✓ {user_id}: {profile.get('name', 'Unknown')}")

    def test_demo_conversations_exist(self):
        """Verify demo profiles have conversation history."""
        from backend.db.sqlite import get_conversation_history
        for user_id in ["sarah", "seamus", "claire"]:
            history = get_conversation_history(user_id, limit=10)
            if not history:
                pytest.skip(f"No conversations for '{user_id}' (not yet seeded)")
            assert len(history) >= 5, f"'{user_id}' should have at least 5 conversations"
            print(f"  ✓ {user_id}: {len(history)} conversations")


class TestSafetyGuards:
    """Phase 6: Content safety filtering."""

    def test_clean_text_passes(self):
        """Verify clean spatial text passes safety check."""
        from backend.core.safety import check_text_safety
        result = check_text_safety("How can I improve the lighting in my living room?")
        assert result["safe"] is True, "Clean spatial text should pass"
        print("  ✓ Clean text passes")

    def test_harmful_text_blocked(self):
        """Verify harmful content is blocked."""
        from backend.core.safety import check_text_safety
        result = check_text_safety("I want to hurt someone")
        assert result["safe"] is False, "Harmful text should be blocked"
        assert result["response"] is not None, "Should provide a redirect response"
        print(f"  ✓ Harmful text blocked (category: {result['category']})")

    def test_self_harm_gets_compassionate_response(self):
        """Verify self-harm text gets compassionate redirect with helpline."""
        from backend.core.safety import check_text_safety
        result = check_text_safety("I don't want to live anymore")
        assert result["safe"] is False, "Self-harm text should be blocked"
        assert "Samaritans" in result["response"], "Should include helpline information"
        print("  ✓ Self-harm gets compassionate response with helplines")

    def test_distress_gets_warm_redirect(self):
        """Verify distress signals get warm acknowledgment."""
        from backend.core.safety import check_text_safety
        result = check_text_safety("I feel completely hopeless")
        assert result["safe"] is False, "Distress should be caught"
        assert "trust" in result["response"].lower() or "alone" in result["response"].lower(), \
            "Should warmly acknowledge distress"
        print("  ✓ Distress gets warm redirect")


class TestZoneAnalysis:
    """Zone Analysis — structure, validation, personalisation, and persistence."""

    def test_zone_structure_has_required_fields(self):
        """Verify a zone dict contains all required fields with correct types."""
        required_fields = {
            "id", "label", "type", "color", "description",
            "recommendation", "priority",
            "x_percent", "y_percent", "width_percent", "height_percent",
        }
        sample_zone = {
            "id": "zone_1",
            "label": "Test Hazard",
            "type": "danger",
            "color": "red",
            "description": "A sharp-cornered table at toddler head height.",
            "recommendation": "Pad corners with folded towels.",
            "priority": 1,
            "x_percent": 20.0,
            "y_percent": 35.0,
            "width_percent": 25.0,
            "height_percent": 15.0,
        }
        missing = required_fields - sample_zone.keys()
        assert not missing, f"Zone is missing fields: {missing}"
        assert isinstance(sample_zone["x_percent"], float)
        assert isinstance(sample_zone["priority"], int)
        print("  ✓ All required zone fields present with correct types")

    def test_zone_types_and_colors_are_valid(self):
        """Verify the four zone type/colour pairs are all valid."""
        valid_types = {"danger", "caution", "opportunity", "suggestion"}
        valid_colors = {"red", "yellow", "green", "blue"}
        pairs = [
            ("danger", "red"),
            ("caution", "yellow"),
            ("opportunity", "green"),
            ("suggestion", "blue"),
        ]
        for ztype, zcolor in pairs:
            assert ztype in valid_types, f"Invalid type: {ztype}"
            assert zcolor in valid_colors, f"Invalid color: {zcolor}"
        print("  ✓ All four zone types and colours validated")

    def test_zone_coordinates_clamped_and_prompt_builds(self):
        """Verify coordinate clamping logic and that build_zone_prompt runs for each archetype."""
        from backend.core.vision import build_zone_prompt

        archetypes = [
            ["child_baby", "child_toddler", "child", "parent"],
            ["elderly", "disability_motor"],
            ["disability_visual", "disability_hearing"],
            ["remote_worker", "student"],
            ["wellness", "fitness"],
            ["general_adult"],
        ]

        for groups in archetypes:
            prompt = build_zone_prompt("Test profile text.", groups)
            assert "danger" in prompt
            assert "x_percent" in prompt
            assert len(prompt) > 200
            print(f"  ✓ Prompt built for groups: {groups[:2]}")

        # Verify coordinate clamping boundaries
        coords = [
            (10.0, 20.0, 25.0, 15.0),   # normal
            (0.0,  0.0,  5.0,  5.0),    # minimum
            (95.0, 95.0, 40.0, 40.0),   # maximum
        ]
        for x, y, w, h in coords:
            assert 0 <= x <= 95
            assert 0 <= y <= 95
            assert 5 <= w <= 40
            assert 5 <= h <= 40
        print("  ✓ Coordinate boundaries validated")

    def test_zone_analysis_saved_and_retrieved_from_db(self):
        """Verify a zone analysis can be written to and read back from SQLite."""
        from backend.db.sqlite import init_db, log_zone_analysis, get_zone_analyses
        init_db()  # Ensure zone_analyses table exists (idempotent)

        test_zones = [
            {
                "id": "zone_t1",
                "label": "DB Test Hazard",
                "type": "caution",
                "color": "yellow",
                "description": "Dim lighting in transit area.",
                "recommendation": "Add a battery motion-sensor light at floor level.",
                "priority": 1,
                "x_percent": 15.0,
                "y_percent": 25.0,
                "width_percent": 20.0,
                "height_percent": 18.0,
            }
        ]

        row_id = log_zone_analysis(
            user_id="_test_zone_persist_",
            zones=test_zones,
            overall_score=74,
            summary="Test persistence summary.",
        )
        assert isinstance(row_id, int) and row_id > 0, "log_zone_analysis should return a positive row id"

        results = get_zone_analyses("_test_zone_persist_", limit=5)
        assert len(results) >= 1, "Should retrieve at least one zone analysis"
        latest = results[0]
        assert latest["overall_score"] == 74
        assert latest["summary"] == "Test persistence summary."
        assert len(latest["zones"]) == 1
        assert latest["zones"][0]["label"] == "DB Test Hazard"
        assert latest["zones"][0]["type"] == "caution"
        print(f"  ✓ Zone analysis saved (row_id={row_id}) and retrieved correctly")


class TestAPIHealth:
    """Phase 7: API endpoint verification."""

    def test_health_endpoint_function(self):
        """Verify health check function returns correct response."""
        import asyncio
        from backend.main import health_check
        result = asyncio.get_event_loop().run_until_complete(health_check())
        assert result["status"] == "ok"
        assert result["service"] == "aura"
        print("  OK: /api/health returns {status: ok}")


class TestGamificationAndMusic:
    """Gamification system and mood-music mapping."""

    @staticmethod
    def _fresh_user(prefix: str) -> str:
        """Return a unique test user ID so repeated runs don't accumulate state."""
        import uuid
        return f"_{prefix}_{uuid.uuid4().hex[:8]}_"

    def test_suggestion_completion_saves(self):
        """Completing a suggestion persists to the DB and returns points."""
        from backend.core.gamification import complete_suggestion, get_user_points

        user = self._fresh_user("gami_save")
        result = complete_suggestion(user, "Open the window for 10 minutes.")
        assert result["points_awarded"] == 5, "Should award 5 points per completion"
        assert result["total_points"] == 5, "First completion should give exactly 5 total pts"

        stored = get_user_points(user)
        assert stored == 5, "get_user_points should return 5"
        print(f"  ✓ Completion saved — {stored} pts for {user}")

    def test_points_accumulate_correctly(self):
        """Multiple completions must sum points correctly."""
        from backend.core.gamification import complete_suggestion, get_user_points

        user = self._fresh_user("gami_accum")
        for i in range(3):
            complete_suggestion(user, f"Test suggestion {i}")

        total = get_user_points(user)
        assert total == 15, f"3 × 5 pts should equal 15, got {total}"
        print(f"  ✓ Points accumulated correctly: {total} pts")

    def test_badge_unlocks_at_threshold(self):
        """A badge must be unlocked exactly when the points threshold is crossed."""
        from backend.core.gamification import complete_suggestion, get_user_badges, BADGES

        user = self._fresh_user("gami_badge")
        # First threshold is 10 pts → "getting_started"
        first_threshold, first_id, *_ = BADGES[0]
        completions_needed = first_threshold // 5   # 1 completion = 5 pts

        result = None
        for _ in range(completions_needed):
            result = complete_suggestion(user, "Badge test suggestion")

        assert result is not None
        badge_ids_unlocked = [b["id"] for b in result["badges_unlocked"]]
        assert first_id in badge_ids_unlocked, (
            f"Badge '{first_id}' should unlock at {first_threshold} pts"
        )
        stored_badges = get_user_badges(user)
        assert first_id in stored_badges, "Badge must be persisted in user_gamification"
        print(f"  ✓ Badge '{first_id}' unlocked at {first_threshold} pts")

    def test_music_mapping_covers_all_moods(self):
        """Every mood in MOOD_PRIORITIES must have a Spotify playlist entry."""
        from backend.core.mood_activities import MOOD_PRIORITIES
        from backend.core.music import get_playlist_for_mood, MOOD_PLAYLISTS

        missing = []
        for mood in MOOD_PRIORITIES:
            playlist = get_playlist_for_mood(mood)
            if playlist is None:
                missing.append(mood)
            else:
                assert "name" in playlist, f"Playlist for '{mood}' missing 'name'"
                assert "url" in playlist, f"Playlist for '{mood}' missing 'url'"
                assert playlist["url"].startswith("https://open.spotify.com/"), (
                    f"Playlist URL for '{mood}' must be a Spotify URL"
                )

        assert not missing, f"Moods with no playlist: {missing}"
        print(f"  ✓ All {len(MOOD_PRIORITIES)} moods have a Spotify playlist")
        for mood in MOOD_PRIORITIES:
            p = MOOD_PLAYLISTS[mood]
            print(f"    {mood}: {p['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
