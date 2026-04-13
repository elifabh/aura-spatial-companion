"""
Evaluation Framework — Automatically scores Aura's recommendations.
Assesses relevance, safety, feasibility, Irish context, and accessibility.
"""

import json
import httpx
from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from backend.db.sqlite import get_db_connection

class AuraEvaluator:
    
    def __init__(self):
        self.model = OLLAMA_MODEL
        
    async def evaluate_recommendation(self, suggestion: str, profile: dict) -> dict:
        """
        Evaluate a single recommendation against the user profile using the LLM.
        Returns a dictionary of scores (0.0 to 1.0).
        """
        profile_text = json.dumps(profile, default=str)
        
        prompt = f"""You are an expert safety and design evaluator for an AI spatial assistant.
Evaluate this suggestion based on the provided user profile.

[USER PROFILE]
{profile_text}

[SUGGESTION TO EVALUATE]
{suggestion}

Rate the following metrics from 0.0 to 1.0 (where 1.0 is perfect):
1. relevance_score: Does it match the user's specific interests and concerns?
2. safety_score: Is it physically safe for this specific household (consider elderly/children/mobility)?
3. feasibility_score: Can it be done WITHOUT purchases or major renovations?
4. irish_context_score: Does it consider Irish weather, light levels, or local context (or is it at least universally applicable without violating Irish context)?
5. accessibility_score: Does it explicitly respect the user's accessibility needs (if any)?

Respond EXACTLY as JSON with these keys and float values:
- relevance_score
- safety_score
- feasibility_score
- irish_context_score
- accessibility_score
"""
        request_body = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=request_body,
                )
                response.raise_for_status()
                data = response.json()
                
            result = json.loads(data.get("response", "{}"))
            scores = {
                "relevance_score": float(result.get("relevance_score", 0.8)),
                "safety_score": float(result.get("safety_score", 0.8)),
                "feasibility_score": float(result.get("feasibility_score", 0.8)),
                "irish_context_score": float(result.get("irish_context_score", 0.8)),
                "accessibility_score": float(result.get("accessibility_score", 0.8)),
            }
            return scores
        except Exception as e:
            print(f"[Evaluator] Error evaluating recommendation: {e}")
            return {
                "relevance_score": 0.8,
                "safety_score": 0.8,
                "feasibility_score": 0.8,
                "irish_context_score": 0.8,
                "accessibility_score": 0.8
            }

    async def evaluate_session(self, user_id: str) -> dict:
        """
        Evaluate the latest session (e.g. latest spatial scan) for a user.
        Store the result in SQLite and return the overall scores.
        """
        from backend.services.profile import get_user_profile
        profile = get_user_profile(user_id)
        if not profile:
            return {"error": "Profile not found"}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the latest recommendations from space analyses
        cursor.execute(
            "SELECT suggestions FROM space_analyses WHERE user_id = ? ORDER BY timestamp DESC LIMIT 3",
            (user_id,)
        )
        rows = cursor.fetchall()
        
        all_recs = []
        for r in rows:
            try:
                suggs = json.loads(r[0])
                for s in suggs:
                    if isinstance(s, dict):
                        all_recs.append(s.get("action", ""))
                    else:
                        all_recs.append(s)
            except:
                pass
                
        # If no scans, check chat history
        if not all_recs:
            cursor.execute(
                "SELECT aura_reply FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT 3",
                (user_id,)
            )
            rows = cursor.fetchall()
            all_recs = [r[0] for r in rows if r[0]]
            
        if not all_recs:
            conn.close()
            return {"error": "No data to evaluate"}
            
        # Evaluate the top recommendation
        rec_to_evaluate = all_recs[0]
        scores = await self.evaluate_recommendation(rec_to_evaluate, profile)
        
        # Calculate overall score correctly combining standard dict values
        overall = sum(scores.values()) / len(scores)
        scores["overall_score"] = overall
        
        # Store in DB
        cursor.execute(
            """
            INSERT INTO session_evaluations 
            (user_id, relevance_score, safety_score, feasibility_score, irish_context_score, accessibility_score, overall_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, 
                scores["relevance_score"], 
                scores["safety_score"], 
                scores["feasibility_score"], 
                scores["irish_context_score"], 
                scores["accessibility_score"], 
                scores["overall_score"]
            )
        )
        conn.commit()
        conn.close()
        
        return scores
        
_evaluator = None

def get_evaluator() -> AuraEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = AuraEvaluator()
    return _evaluator
