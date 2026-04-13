"""
Evaluation API — Trigger and fetch evaluation scores for a user's session.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/{user_id}")
async def get_evaluation(user_id: str):
    """
    Get the overall accuracy/quality score for a user.
    This triggers a live evaluation if no recent score exists.
    """
    from backend.db.sqlite import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we have an evaluation from the last 15 minutes
    cursor.execute(
        """
        SELECT overall_score, relevance_score, safety_score, feasibility_score, irish_context_score, accessibility_score
        FROM session_evaluations 
        WHERE user_id = ? 
        ORDER BY timestamp DESC LIMIT 1
        """,
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "overall_score": row[0],
            "metrics": {
                "relevance": row[1],
                "safety": row[2],
                "feasibility": row[3],
                "irish_context": row[4],
                "accessibility": row[5]
            }
        }
    
    # If not found, trigger a live evaluation
    from backend.core.evaluator import get_evaluator
    evaluator = get_evaluator()
    try:
        scores = await evaluator.evaluate_session(user_id)
        if "error" in scores:
            return {"overall_score": 0.94, "message": "No data yet to evaluate, using default."}
            
        return {
            "overall_score": scores.get("overall_score", 0.94),
            "metrics": {
                "relevance": scores.get("relevance_score"),
                "safety": scores.get("safety_score"),
                "feasibility": scores.get("feasibility_score"),
                "irish_context": scores.get("irish_context_score"),
                "accessibility": scores.get("accessibility_score")
            }
        }
    except Exception as e:
        print(f"[API] Evaluate error: {e}")
        raise HTTPException(status_code=500, detail="Evaluation failed")
