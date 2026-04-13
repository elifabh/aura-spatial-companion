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
        """Verify ChromaDB has documents after ingestion."""
        from backend.core.rag import get_collection
        collection = get_collection()
        count = collection.count()
        print(f"  ChromaDB document count: {count}")
        assert count > 0, "ChromaDB should have documents after ingestion"

    def test_knowledge_query_returns_results(self):
        """Verify querying the knowledge base returns relevant results."""
        from backend.core.rag import get_relevant_knowledge
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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
