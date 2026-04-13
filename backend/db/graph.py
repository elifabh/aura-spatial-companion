"""
Graph RAG — Lightweight knowledge graph using NetworkX.
Stores domain concepts and their relationships for richer context retrieval.
"""

import json
import networkx as nx
from pathlib import Path
from backend.config import DATA_DIR


GRAPH_PATH = Path(DATA_DIR) / "knowledge_graph.json"


def build_knowledge_graph() -> nx.DiGraph:
    """Build the Aura domain knowledge graph with expert relationships."""
    G = nx.DiGraph()

    # ── Nodes (concepts) ───────────────────────────────
    concepts = [
        # Conditions & Demographics
        ("ADHD", {"type": "condition", "domain": "neurodiversity"}),
        ("autism", {"type": "condition", "domain": "neurodiversity"}),
        ("elderly", {"type": "demographic", "domain": "age"}),
        ("children", {"type": "demographic", "domain": "age"}),
        ("toddler", {"type": "demographic", "domain": "age"}),
        ("wheelchair_user", {"type": "condition", "domain": "mobility"}),
        ("visual_impairment", {"type": "condition", "domain": "sensory"}),
        ("hearing_impairment", {"type": "condition", "domain": "sensory"}),
        ("motor_difficulties", {"type": "condition", "domain": "mobility"}),

        # Environmental Factors
        ("natural_light", {"type": "factor", "domain": "environment"}),
        ("artificial_light", {"type": "factor", "domain": "environment"}),
        ("ventilation", {"type": "factor", "domain": "environment"}),
        ("air_quality", {"type": "factor", "domain": "environment"}),
        ("noise", {"type": "factor", "domain": "environment"}),
        ("temperature", {"type": "factor", "domain": "environment"}),
        ("humidity", {"type": "factor", "domain": "environment"}),
        ("Irish_winter", {"type": "season", "domain": "climate"}),
        ("Irish_summer", {"type": "season", "domain": "climate"}),
        ("cloudy_weather", {"type": "weather", "domain": "climate"}),
        ("rain", {"type": "weather", "domain": "climate"}),

        # Risks & Outcomes
        ("SAD", {"type": "condition", "domain": "mental_health"}),
        ("falls", {"type": "risk", "domain": "safety"}),
        ("stress", {"type": "outcome", "domain": "mental_health"}),
        ("fatigue", {"type": "outcome", "domain": "mental_health"}),
        ("sensory_overload", {"type": "risk", "domain": "neurodiversity"}),
        ("poor_sleep", {"type": "risk", "domain": "health"}),

        # Spatial Solutions
        ("low_distraction_space", {"type": "solution", "domain": "design"}),
        ("clear_pathways", {"type": "solution", "domain": "design"}),
        ("wide_doorways", {"type": "solution", "domain": "design"}),
        ("secured_furniture", {"type": "solution", "domain": "safety"}),
        ("grab_rails", {"type": "solution", "domain": "safety"}),
        ("non_slip_flooring", {"type": "solution", "domain": "safety"}),
        ("mirror_placement", {"type": "solution", "domain": "lighting"}),
        ("light_paint", {"type": "solution", "domain": "lighting"}),
        ("task_lighting", {"type": "solution", "domain": "lighting"}),
        ("quiet_zone", {"type": "solution", "domain": "design"}),
        ("sensory_corner", {"type": "solution", "domain": "design"}),
        ("activity_zones", {"type": "solution", "domain": "design"}),
        ("floor_bed", {"type": "solution", "domain": "montessori"}),
        ("low_shelves", {"type": "solution", "domain": "montessori"}),
        ("safety_gates", {"type": "solution", "domain": "safety"}),
        ("window_cord_safety", {"type": "solution", "domain": "safety"}),
        ("ventilation_routine", {"type": "solution", "domain": "air"}),
        ("houseplants", {"type": "solution", "domain": "air"}),

        # Standards & Guidelines
        ("WELL_standard", {"type": "standard", "domain": "building"}),
        ("CIBSE_guidelines", {"type": "standard", "domain": "building"}),
        ("universal_design", {"type": "standard", "domain": "accessibility"}),
        ("WHO_housing", {"type": "standard", "domain": "health"}),
        ("montessori_principles", {"type": "standard", "domain": "education"}),
    ]

    for node_id, attrs in concepts:
        G.add_node(node_id, **attrs)

    # ── Edges (relationships) ──────────────────────────
    relationships = [
        # ADHD
        ("ADHD", "needs", "low_distraction_space"),
        ("ADHD", "needs", "quiet_zone"),
        ("ADHD", "sensitive_to", "noise"),
        ("ADHD", "sensitive_to", "sensory_overload"),
        ("ADHD", "benefits_from", "activity_zones"),

        # Autism
        ("autism", "needs", "sensory_corner"),
        ("autism", "needs", "quiet_zone"),
        ("autism", "sensitive_to", "noise"),
        ("autism", "sensitive_to", "artificial_light"),
        ("autism", "risk_of", "sensory_overload"),

        # Elderly
        ("elderly", "risk_of", "falls"),
        ("falls", "prevented_by", "clear_pathways"),
        ("falls", "prevented_by", "grab_rails"),
        ("falls", "prevented_by", "non_slip_flooring"),
        ("elderly", "needs", "task_lighting"),
        ("elderly", "needs", "wide_doorways"),

        # Children & Toddlers
        ("children", "needs", "secured_furniture"),
        ("children", "needs", "safety_gates"),
        ("children", "needs", "window_cord_safety"),
        ("toddler", "benefits_from", "floor_bed"),
        ("toddler", "benefits_from", "low_shelves"),
        ("toddler", "benefits_from", "activity_zones"),
        ("children", "benefits_from", "activity_zones"),

        # Wheelchair
        ("wheelchair_user", "needs", "wide_doorways"),
        ("wheelchair_user", "needs", "clear_pathways"),
        ("wheelchair_user", "needs", "low_shelves"),

        # Visual impairment
        ("visual_impairment", "needs", "task_lighting"),
        ("visual_impairment", "needs", "light_paint"),
        ("visual_impairment", "sensitive_to", "poor_sleep"),

        # Motor difficulties
        ("motor_difficulties", "needs", "grab_rails"),
        ("motor_difficulties", "needs", "non_slip_flooring"),
        ("motor_difficulties", "risk_of", "falls"),

        # Irish Climate
        ("Irish_winter", "causes", "cloudy_weather"),
        ("cloudy_weather", "reduces", "natural_light"),
        ("natural_light", "deficiency_leads_to", "SAD"),
        ("SAD", "mitigated_by", "mirror_placement"),
        ("SAD", "mitigated_by", "light_paint"),
        ("SAD", "mitigated_by", "task_lighting"),
        ("Irish_winter", "increases", "humidity"),
        ("humidity", "mitigated_by", "ventilation_routine"),
        ("rain", "common_in", "Irish_winter"),

        # Air Quality
        ("ventilation", "improved_by", "ventilation_routine"),
        ("air_quality", "improved_by", "houseplants"),
        ("air_quality", "improved_by", "ventilation_routine"),

        # Stress & Fatigue
        ("cloudy_weather", "correlates_with", "fatigue"),
        ("noise", "causes", "stress"),
        ("sensory_overload", "causes", "stress"),
        ("stress", "mitigated_by", "quiet_zone"),
        ("fatigue", "mitigated_by", "natural_light"),
        ("poor_sleep", "caused_by", "artificial_light"),

        # Standards references
        ("WELL_standard", "covers", "natural_light"),
        ("WELL_standard", "covers", "air_quality"),
        ("WELL_standard", "covers", "noise"),
        ("CIBSE_guidelines", "covers", "ventilation"),
        ("CIBSE_guidelines", "covers", "temperature"),
        ("universal_design", "covers", "wide_doorways"),
        ("universal_design", "covers", "clear_pathways"),
        ("WHO_housing", "covers", "falls"),
        ("WHO_housing", "covers", "humidity"),
        ("montessori_principles", "covers", "low_shelves"),
        ("montessori_principles", "covers", "floor_bed"),
        ("montessori_principles", "covers", "activity_zones"),
    ]

    for src, rel, dst in relationships:
        G.add_edge(src, dst, relationship=rel)

    return G


# ── Singleton graph instance ──────────────────────────
_graph: nx.DiGraph | None = None


def get_graph() -> nx.DiGraph:
    global _graph
    if _graph is None:
        _graph = build_knowledge_graph()
    return _graph


def get_graph_context(query: str, max_hops: int = 2) -> list[str]:
    """
    Find relevant nodes from the query and traverse relationships
    to build context chains.

    Returns a list of human-readable relationship strings like:
    "elderly → risk_of → falls → prevented_by → grab_rails"
    """
    G = get_graph()
    query_lower = query.lower()

    # Find matching nodes
    matched_nodes = []
    for node in G.nodes():
        node_lower = node.lower().replace("_", " ")
        if node_lower in query_lower or any(word in query_lower for word in node_lower.split()):
            matched_nodes.append(node)

    # Also check node attributes for broader matching
    keywords = query_lower.split()
    for node, attrs in G.nodes(data=True):
        domain = attrs.get("domain", "").lower()
        ntype = attrs.get("type", "").lower()
        if any(kw in domain or kw in ntype for kw in keywords):
            if node not in matched_nodes:
                matched_nodes.append(node)

    if not matched_nodes:
        return []

    # Traverse relationships (BFS up to max_hops)
    chains = []
    visited = set()

    for start_node in matched_nodes[:5]:  # Limit starting nodes
        # Forward traversal
        for target in G.successors(start_node):
            edge_data = G.edges[start_node, target]
            rel = edge_data.get("relationship", "related_to")
            chain = f"{start_node} → {rel} → {target}"

            # Second hop
            for target2 in G.successors(target):
                edge_data2 = G.edges[target, target2]
                rel2 = edge_data2.get("relationship", "related_to")
                chain2 = f"{chain} → {rel2} → {target2}"
                if chain2 not in visited:
                    chains.append(chain2)
                    visited.add(chain2)

            if chain not in visited:
                chains.append(chain)
                visited.add(chain)

        # Backward traversal (what leads to this node?)
        for source in G.predecessors(start_node):
            edge_data = G.edges[source, start_node]
            rel = edge_data.get("relationship", "related_to")
            chain = f"{source} → {rel} → {start_node}"
            if chain not in visited:
                chains.append(chain)
                visited.add(chain)

    return chains[:15]  # Limit context size


def save_graph():
    """Serialize graph to JSON for persistence."""
    G = get_graph()
    data = nx.node_link_data(G)
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    with open(GRAPH_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[Graph] Saved knowledge graph ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
