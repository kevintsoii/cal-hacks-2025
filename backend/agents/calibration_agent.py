import time
from models import (
    MitigationBatch, Mitigation, OrchestratorResponse
)
import os
import json
import asyncio
import httpx  # For making async API calls to Groq
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
import sys

# Add parent directory to path to import rag module
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from uagents import Agent, Context
from typing import List, Dict, Optional

# Import ChromaDB RAG implementation
from rag.simple_rag import SimpleRAG

load_dotenv()

# SETUP
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

agent = Agent(
    name="Calibration Agent",
    seed="Calibration Agent Seed 23324324",
    port=8005,
    mailbox=True,
    publish_agent_details=True
)

# Create a persistent async client for Groq API calls
http_client = httpx.AsyncClient()

# Initialize ChromaDB RAG - connects to separate ChromaDB service via HTTP
rag = SimpleRAG()

# CALIBRATION AGENT PROMPT
CALIBRATION_PROMPT = """You are an AI Calibration Agent responsible for fine-tuning security mitigations based on historical effectiveness data.

Your role:
1. Review the recommended mitigation from a specialist agent (Auth, Search, or General)
2. Analyze similar past mitigations from the RAG database (ChromaDB)
3. Decide whether to AMPLIFY, DOWNGRADE, or KEEP the mitigation based on historical effectiveness
4. Provide clear reasoning for your decision

Available mitigation levels (in order of severity):
- delay: Small request delay (100-500ms) - Severity: low
- captcha: CAPTCHA challenge required - Severity: medium
- temp_block: Temporary block (15-60 min) - Severity: high
- ban: Permanent ban - Severity: critical

Decision guidelines:
- AMPLIFY: If similar past mitigations were ineffective (<50% effectiveness) → increase severity
- DOWNGRADE: If similar past mitigations were overly effective (>80% effectiveness, all successful) → decrease severity to reduce friction
- KEEP_ORIGINAL: If historical data shows moderate effectiveness (50-80%) or no data available

Consider:
- Average effectiveness of similar cases
- Number of similar cases (higher = more confidence)
- Severity of the threat
- User experience vs security trade-offs

Output format - Return ONLY valid JSON:
{
  "decision": "AMPLIFY|DOWNGRADE|KEEP_ORIGINAL",
  "calibrated_severity": "low|medium|high|critical",
  "calibrated_mitigation": "delay|captcha|temp_block|ban",
  "reasoning": "Brief explanation of your decision based on the historical data",
  "confidence": "low|medium|high"
}
"""


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("[CALIBRATION] Calibration Agent online with AI-powered RAG")
    ctx.logger.info(f"[CALIBRATION] Using Groq LLM for intelligent mitigation calibration")
    chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8006")
    ctx.logger.info(f"[CALIBRATION] Connected to ChromaDB service at: {chromadb_url}")
    ctx.logger.info(f"[CALIBRATION] Vector embeddings enabled for semantic search")
    ctx.logger.info(f"[CALIBRATION] Agent address: {agent.address}")
    if not GROQ_API_KEY:
        ctx.logger.warning("[CALIBRATION] ⚠️  GROQ_API_KEY not found - calibration will fail!")


@agent.on_message(model=MitigationBatch)
async def handle_mitigation_batch(ctx: Context, sender: str, batch: MitigationBatch):
    """
    Handle incoming mitigation recommendations from specialist agents.
    
    Workflow:
    1. Query ChromaDB for similar past mitigations using vector similarity (RAG)
    2. Analyze effectiveness of similar mitigations using Groq LLM
    3. Amplify or downgrade the mitigation based on historical data
    4. Save the calibrated mitigation to ChromaDB with vector embeddings
    5. Apply the final mitigation to Redis
    """
    ctx.logger.info(f"[CALIBRATION] ✓ Received {len(batch.mitigations)} mitigations from {batch.source_agent} agent")
    
    # Process each mitigation
    for i, mitigation in enumerate(batch.mitigations, 1):
        ctx.logger.info(f"\n[CALIBRATION] {'='*70}")
        ctx.logger.info(f"[CALIBRATION] Processing Mitigation {i}/{len(batch.mitigations)}")
        ctx.logger.info(f"[CALIBRATION] {'='*70}")
        ctx.logger.info(
            f"[CALIBRATION]   Original: {mitigation.entity_type} {mitigation.entity} "
            f"-> {mitigation.mitigation} (severity: {mitigation.severity})"
        )
        ctx.logger.info(f"[CALIBRATION]   Reason: {mitigation.reason}")
        
        # STEP 1: Query ChromaDB for similar past mitigations
        ctx.logger.info(f"\n[CALIBRATION] 🔍 STEP 1: Querying ChromaDB for similar cases...")
        similar_cases = await query_chromadb(ctx, mitigation.reason, mitigation.entity)
        
        if similar_cases:
            ctx.logger.info(f"[CALIBRATION]   ✓ Found {len(similar_cases)} similar past cases")
            for j, case in enumerate(similar_cases[:3], 1):
                ctx.logger.info(f"[CALIBRATION]     {j}. {case['mitigation']} → Result: {case['result']} (Effectiveness: {case['effectiveness']}%)")
        else:
            ctx.logger.info(f"[CALIBRATION]   ℹ️  No similar cases found (first-time scenario)")
        
        # STEP 2: Analyze and calibrate
        ctx.logger.info(f"\n[CALIBRATION] ⚖️  STEP 2: Analyzing and calibrating mitigation...")
        calibrated_mitigation, calibration_reasoning = await calibrate_with_rag(
            ctx, mitigation, similar_cases
        )
        
        ctx.logger.info(f"[CALIBRATION]   Decision: {calibration_reasoning['decision']}")
        ctx.logger.info(f"[CALIBRATION]   Reasoning: {calibration_reasoning['reasoning']}")
        ctx.logger.info(
            f"[CALIBRATION]   Calibrated: {calibrated_mitigation.entity_type} {calibrated_mitigation.entity} "
            f"-> {calibrated_mitigation.mitigation} (severity: {calibrated_mitigation.severity})"
        )
        
        # STEP 3: Save to ChromaDB
        ctx.logger.info(f"\n[CALIBRATION] 💾 STEP 3: Saving to ChromaDB for future reference...")
        await save_to_chromadb(ctx, calibrated_mitigation, calibration_reasoning)
        ctx.logger.info(f"[CALIBRATION]   ✓ Saved to ChromaDB")
        
        # STEP 4: Apply to Redis
        ctx.logger.info(f"\n[CALIBRATION] 🔧 STEP 4: Applying mitigation to Redis...")
        await apply_to_redis(ctx, calibrated_mitigation)
        ctx.logger.info(f"[CALIBRATION]   ✓ Applied to Redis")
        
        ctx.logger.info(f"[CALIBRATION] {'='*70}\n")
    
    ctx.logger.info(f"[CALIBRATION] ✅ All {len(batch.mitigations)} mitigations processed and applied")
    
    # Send acknowledgment back
    await ctx.send(sender, OrchestratorResponse(success=True))


async def query_chromadb(ctx: Context, reason: str, entity: str) -> List[Dict]:
    """
    Query ChromaDB for similar past mitigations using vector similarity search (RAG).
    Uses semantic embeddings to find similar threat patterns.
    """
    try:
        # Build semantic query combining reason and entity context
        query_text = f"{reason} affecting {entity}"
        
        # Use RAG to find semantically similar past incidents
        similar_items = await rag.query_items(query_text, k=5)
        
        if not similar_items:
            ctx.logger.info(f"[CALIBRATION]   No similar cases found in ChromaDB")
            return []
        
        # Transform RAG results to calibration format
        similar_cases = []
        for item in similar_items:
            metadata = item.get("metadata", {})
            similar_cases.append({
                "id": item.get("id"),
                "entity_type": metadata.get("entity_type"),
                "entity": metadata.get("entity"),
                "severity": metadata.get("severity"),
                "mitigation": metadata.get("mitigation"),
                "reason": item.get("text"),  # The reasoning text (embedded)
                "source_agent": metadata.get("source_agent"),
                "effectiveness": metadata.get("effectiveness"),
                "result": metadata.get("result", "pending"),
                "similarity_score": item.get("score", 0.0),
                "timestamp": metadata.get("timestamp")
            })
        
        ctx.logger.info(f"[CALIBRATION]   Found {len(similar_cases)} semantically similar cases")
        return similar_cases
        
    except Exception as e:
        ctx.logger.error(f"[CALIBRATION] Error querying ChromaDB: {e}")
        import traceback
        ctx.logger.error(f"[CALIBRATION] Traceback: {traceback.format_exc()}")
        return []


async def calibrate_with_rag(ctx: Context, mitigation: Mitigation, similar_cases: List[Dict]) -> tuple[Mitigation, Dict]:
    """
    Use RAG + LLM (Groq) to amplify or downgrade mitigation based on historical effectiveness.
    
    Returns: (calibrated_mitigation, reasoning_dict)
    """
    original_severity = mitigation.severity
    original_mitigation_type = mitigation.mitigation
    
    # Filter out cases with None effectiveness (pending results)
    cases_with_results = [case for case in similar_cases if case.get("effectiveness") is not None]
    
    # Prepare context for LLM
    if not cases_with_results:
        historical_context = "No historical data available for similar cases."
        avg_effectiveness = None
        total_cases = 0
    else:
        total_cases = len(cases_with_results)
        avg_effectiveness = sum(case.get("effectiveness", 0) for case in cases_with_results) / total_cases
        effective_count = sum(1 for case in cases_with_results if case.get("effectiveness", 0) >= 70)
        
        # Format historical cases for LLM
        historical_context = f"Historical Analysis of {total_cases} similar cases:\n"
        historical_context += f"- Average effectiveness: {avg_effectiveness:.1f}%\n"
        historical_context += f"- Highly effective (≥70%): {effective_count}/{total_cases}\n\n"
        historical_context += "Past mitigation details:\n"
        
        for i, case in enumerate(cases_with_results[:5], 1):
            historical_context += f"{i}. Mitigation: {case.get('mitigation', 'unknown')} (Severity: {case.get('severity', 'unknown')})\n"
            historical_context += f"   Result: {case.get('result', 'unknown')}\n"
            historical_context += f"   Effectiveness: {case.get('effectiveness', 0)}%\n"
            historical_context += f"   Reason: {case.get('reason', 'N/A')[:100]}\n\n"
        
        ctx.logger.info(f"[CALIBRATION]   RAG Context: {total_cases} cases, avg {avg_effectiveness:.1f}% effectiveness")
    
    # Build user prompt with mitigation details and historical context
    user_prompt = f"""CURRENT MITIGATION TO CALIBRATE:
Entity Type: {mitigation.entity_type}
Entity: {mitigation.entity}
Original Severity: {original_severity}
Original Mitigation: {original_mitigation_type}
Threat Reason: {mitigation.reason}
Source Agent: {mitigation.source_agent}

HISTORICAL DATA (RAG):
{historical_context}

Based on this historical effectiveness data, decide whether to AMPLIFY, DOWNGRADE, or KEEP_ORIGINAL for this mitigation.
Return your decision in the specified JSON format."""

    try:
        # Call Groq API
        ctx.logger.info(f"[CALIBRATION] Calling Groq for AI-powered calibration decision...")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GROQ_API_KEY}'
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": CALIBRATION_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,  # Lower temperature for more consistent decisions
            "response_format": {"type": "json_object"}
        }
        
        response = await http_client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            ctx.logger.error(f"[CALIBRATION] Groq API error {response.status_code}: {response.text}")
            # Fallback: keep original
            return mitigation, {
                "decision": "KEEP_ORIGINAL",
                "reasoning": "API error - keeping original mitigation",
                "confidence": "low",
                "error": f"Groq API returned {response.status_code}"
            }
        
        result = response.json()
        llm_output = result['choices'][0]['message']['content']
        
        # Parse LLM decision
        try:
            decision_data = json.loads(llm_output)
        except json.JSONDecodeError as e:
            ctx.logger.error(f"[CALIBRATION] Failed to parse LLM response: {e}")
            ctx.logger.error(f"[CALIBRATION] Response was: {llm_output[:200]}")
            # Fallback
            return mitigation, {
                "decision": "KEEP_ORIGINAL",
                "reasoning": "Failed to parse LLM response - keeping original",
                "confidence": "low"
            }
        
        # Extract calibrated values
        decision = decision_data.get("decision", "KEEP_ORIGINAL")
        new_severity = decision_data.get("calibrated_severity", original_severity)
        new_mitigation_type = decision_data.get("calibrated_mitigation", original_mitigation_type)
        reasoning = decision_data.get("reasoning", "No reasoning provided")
        confidence = decision_data.get("confidence", "medium")
        
        ctx.logger.info(f"[CALIBRATION] 🤖 LLM Decision: {decision}")
        ctx.logger.info(f"[CALIBRATION] 💭 Reasoning: {reasoning}")
        
        # Create calibrated mitigation
        calibrated = Mitigation(
            entity_type=mitigation.entity_type,
            entity=mitigation.entity,
            severity=new_severity,
            mitigation=new_mitigation_type,
            reason=mitigation.reason,
            source_agent=mitigation.source_agent
        )
        
        calibration_reasoning = {
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "cases_analyzed": total_cases,
            "avg_effectiveness": round(avg_effectiveness, 1) if avg_effectiveness else None,
            "original_severity": original_severity,
            "calibrated_severity": new_severity,
            "original_mitigation": original_mitigation_type,
            "calibrated_mitigation": new_mitigation_type,
            "llm_used": True
        }
        
        return calibrated, calibration_reasoning
        
    except httpx.RequestError as e:
        ctx.logger.error(f"[CALIBRATION] HTTP error calling Groq: {e}")
        # Fallback to original
        return mitigation, {
            "decision": "KEEP_ORIGINAL",
            "reasoning": f"Network error - keeping original mitigation: {str(e)}",
            "confidence": "low",
            "error": str(e)
        }
    except Exception as e:
        ctx.logger.error(f"[CALIBRATION] Unexpected error: {e}")
        return mitigation, {
            "decision": "KEEP_ORIGINAL",
            "reasoning": f"Unexpected error - keeping original mitigation: {str(e)}",
            "confidence": "low",
            "error": str(e)
        }


async def save_to_chromadb(ctx: Context, mitigation: Mitigation, calibration_reasoning: Dict):
    """
    Save the calibrated mitigation to ChromaDB with semantic reasoning.
    This creates vector embeddings for future RAG queries.
    """
    try:
        # Map severity to numeric (1-5) for ChromaDB
        severity_map = {"low": 2, "medium": 3, "high": 4, "critical": 5}
        severity_numeric = severity_map.get(mitigation.severity, 3)
        
        # Build comprehensive reasoning text that will be embedded (vectorized)
        # This is what ChromaDB will use for semantic similarity matching
        reasoning_text = f"""
Threat: {mitigation.reason}
Mitigation Applied: {mitigation.mitigation} (severity: {mitigation.severity})
Entity Type: {mitigation.entity_type}
Source Agent: {mitigation.source_agent}
Calibration Decision: {calibration_reasoning["decision"]}
Reasoning: {calibration_reasoning["reasoning"]}
Confidence: {calibration_reasoning["confidence"]}
        """.strip()
        
        # Store structured data in metadata (not embedded, but stored alongside)
        metadata = {
            "entity_type": mitigation.entity_type,
            "entity": mitigation.entity,
            "severity": mitigation.severity,
            "mitigation": mitigation.mitigation,
            "source_agent": mitigation.source_agent,
            "calibration_decision": calibration_reasoning["decision"],
            "calibration_confidence": calibration_reasoning["confidence"],
            "result": "pending",  # Will be "resolved", "escalated", "false_positive", etc.
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # Don't include effectiveness if None - will be added later when we have feedback
        if calibration_reasoning.get("effectiveness") is not None:
            metadata["effectiveness"] = calibration_reasoning["effectiveness"]
        
        # Save to ChromaDB with vector embeddings
        # The reasoning_text gets embedded for semantic search
        item_id = await rag.add_item(
            reasoning=reasoning_text,
            user=mitigation.entity if mitigation.entity_type == "user" else "system",
            ip=mitigation.entity if mitigation.entity_type == "ip" else "0.0.0.0",
            severity=severity_numeric,
            metadata=metadata
        )
        
        ctx.logger.info(f"[CALIBRATION]   Saved to ChromaDB with ID: {item_id[:8]}...")
        ctx.logger.info(f"[CALIBRATION]   Vector embedding created for semantic search")
        
    except Exception as e:
        ctx.logger.error(f"[CALIBRATION] Error saving to ChromaDB: {e}")
        import traceback
        ctx.logger.error(f"[CALIBRATION] Traceback: {traceback.format_exc()}")


async def apply_to_redis(ctx: Context, mitigation: Mitigation):
    """
    Apply the final mitigation to Redis so middleware can enforce it.
    
    Redis keys:
    - mitigation:ip:{ip_address} -> severity level (1-4)
    - mitigation:user:{username} -> severity level (1-4)
    """
    try:
        from db.redis import redis_client
        
        # Map severity to numeric level
        severity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        severity_level = severity_map.get(mitigation.severity, 2)
        
        # Apply to Redis based on entity type
        if mitigation.entity_type == "ip":
            key = f"mitigation:ip:{mitigation.entity}"
            await redis_client.set_value(key, str(severity_level), expiry=3600)  # 1 hour TTL
            ctx.logger.info(f"[CALIBRATION]   Set Redis: {key} = {severity_level} (TTL: 1h)")
            
        elif mitigation.entity_type == "user":
            key = f"mitigation:user:{mitigation.entity}"
            await redis_client.set_value(key, str(severity_level), expiry=3600)  # 1 hour TTL
            ctx.logger.info(f"[CALIBRATION]   Set Redis: {key} = {severity_level} (TTL: 1h)")
        
        # Also store mitigation details for debugging
        details_key = f"{key}:details"
        details = {
            "mitigation": mitigation.mitigation,
            "reason": mitigation.reason,
            "timestamp": datetime.now().isoformat(),
            "source_agent": mitigation.source_agent
        }
        await redis_client.set_value(details_key, json.dumps(details), expiry=3600)
        
    except Exception as e:
        ctx.logger.error(f"[CALIBRATION] Error applying to Redis: {e}")
        ctx.logger.error(f"[CALIBRATION] Mitigation will not be enforced by middleware!")


if __name__ == "__main__":
    agent.run()