import time
import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    MitigationBatch, Mitigation, OrchestratorResponse
)
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
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, EndSessionContent, TextContent, chat_protocol_spec
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
CALIBRATION_PROMPT = """You are an AI Calibration Agent responsible for fine-tuning security mitigations based on historical patterns and reasoning.

Your role:
1. Review the recommended mitigation from a specialist agent (Auth, Search, or General)
2. Analyze similar past mitigations from the RAG database (ChromaDB)
3. Decide whether to AMPLIFY, DOWNGRADE, or KEEP the mitigation based on patterns in past decisions
4. Provide clear reasoning for your decision

Available mitigation levels (in order of severity):
- delay: Small request delay (100-500ms) - Severity: low
- captcha: CAPTCHA challenge required - Severity: medium
- temp_block: Temporary block (15-60 min) - Severity: high
- ban: Permanent ban - Severity: critical

Decision guidelines - TEMPORAL PATTERNS ARE CRITICAL:
- AMPLIFY: 
  * Multiple similar incidents clustered in time (within minutes/hours) = REPEAT OFFENDER pattern
  * 3+ similar cases within a short timeframe = clear escalation needed
  * Frequency of incidents is increasing over time
  * Past incidents had higher severity levels
- DOWNGRADE: 
  * Only 1-2 isolated incidents in history with large time gaps (hours/days apart)
  * Sparse pattern suggests one-off mistakes, not malicious intent
  * Long time gap since last similar incident (suggests reformed behavior)
  * Past incidents consistently handled with lower severity
- KEEP_ORIGINAL: 
  * Similar cases used the same severity level consistently
  * Mixed temporal patterns (some clustered, some sparse)
  * No clear pattern exists

Prioritize temporal clustering:
- Repeat offenses within similar timestamps (< 5 minutes apart) = HIGH PRIORITY for AMPLIFY
- Large gaps between incidents (> 5 minutes) with only 1-2 cases = safe to DOWNGRADE
- Consider recency: recent clusters are more concerning than old isolated incidents

Output format - Return ONLY valid JSON:
{
  "decision": "AMPLIFY|DOWNGRADE|KEEP_ORIGINAL",
  "calibrated_severity": "low|medium|high|critical",
  "calibrated_mitigation": "delay|captcha|temp_block|ban",
  "reasoning": "Brief explanation emphasizing temporal patterns and repeat offense analysis",
  "confidence": "low|medium|high"
}
"""


@agent.on_event("startup")
async def startup(ctx: Context):
    chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:9000")
    if not GROQ_API_KEY:
        ctx.logger.warning("[CALIBRATION] ⚠️  GROQ_API_KEY not found - calibration will fail!")
    ctx.logger.info("[CALIBRATION] Calibration Agent online with pattern-based RAG learning")


@agent.on_message(model=MitigationBatch)
async def handle_mitigation_batch(ctx: Context, sender: str, batch: MitigationBatch):
    """
    Handle incoming mitigation recommendations from specialist agents.
    
    Workflow:
    1. Query ChromaDB for similar past mitigations using vector similarity (RAG)
    2. Analyze patterns in similar mitigations using Groq LLM
    3. Amplify or downgrade the mitigation based on historical patterns
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
        
        # STEP 1: Query ChromaDB for similar past mitigations AND custom rules (in parallel)
        ctx.logger.info(f"\n[CALIBRATION] 🔍 STEP 1: Querying ChromaDB for similar cases and custom rules...")
        similar_cases, custom_rules = await asyncio.gather(
            query_chromadb(ctx, mitigation.reason, mitigation.entity),
            query_custom_rules(ctx, mitigation.reason)
        )
        
        if similar_cases:
            ctx.logger.info(f"[CALIBRATION]   ✓ Found {len(similar_cases)} similar past cases")
            for j, case in enumerate(similar_cases[:3], 1):
                ctx.logger.info(f"[CALIBRATION]     {j}. {case['mitigation']} (severity: {case['severity']}) - {case['reason'][:60]}...")
        else:
            ctx.logger.info(f"[CALIBRATION]   ℹ️  No similar cases found (first-time scenario)")
        
        if custom_rules:
            ctx.logger.info(f"[CALIBRATION]   ✓ Found {len(custom_rules)} relevant custom rules")
            for j, rule in enumerate(custom_rules[:3], 1):
                ctx.logger.info(f"[CALIBRATION]     {j}. [{rule.get('category', 'general')}] {rule.get('refined_text', '')[:60]}...")
        else:
            ctx.logger.info(f"[CALIBRATION]   ℹ️  No custom rules found")
        
        # STEP 2: Analyze and calibrate
        ctx.logger.info(f"\n[CALIBRATION] ⚖️  STEP 2: Analyzing and calibrating mitigation...")
        calibrated_mitigation, calibration_reasoning = await calibrate_with_rag(
            ctx, mitigation, similar_cases, custom_rules
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
        # Use threat reason directly for semantic matching (entity is noise for pattern matching)
        query_text = reason
        
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
                "calibration_decision": metadata.get("calibration_decision"),
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


async def query_custom_rules(ctx: Context, reason: str) -> List[Dict]:
    """
    Query ChromaDB for relevant custom security rules using vector similarity search.
    Uses semantic embeddings to find applicable rules.
    """
    try:
        # Query custom rules collection
        rules = await rag.query_rules(reason, k=3)
        
        if not rules:
            ctx.logger.info(f"[CALIBRATION]   No custom rules found in ChromaDB")
            return []
        
        ctx.logger.info(f"[CALIBRATION]   Found {len(rules)} relevant custom rules")
        return rules
        
    except Exception as e:
        ctx.logger.error(f"[CALIBRATION] Error querying custom rules: {e}")
        import traceback
        ctx.logger.error(f"[CALIBRATION] Traceback: {traceback.format_exc()}")
        return []


async def calibrate_with_rag(ctx: Context, mitigation: Mitigation, similar_cases: List[Dict], custom_rules: List[Dict]) -> tuple[Mitigation, Dict]:
    """
    Use RAG + LLM (Groq) to amplify or downgrade mitigation based on historical patterns and custom rules.
    
    Returns: (calibrated_mitigation, reasoning_dict)
    """
    original_severity = mitigation.severity
    original_mitigation_type = mitigation.mitigation
    
    # Prepare context for LLM based on top similar cases
    if not similar_cases:
        historical_context = "No historical data available for similar cases."
        total_cases = 0
    else:
        total_cases = len(similar_cases)
        
        
        # Format historical cases for LLM - one line per case
        historical_context = f"Retrieved {total_cases} similar past mitigations (analyze timestamps for recency/clustering):\n"
        
        for i, case in enumerate(similar_cases[:5], 1):
            historical_context += (
                f"{i}. [{case.get('timestamp', 'unknown')}] "
                f"{case.get('entity_type', '?')}:{case.get('entity', '?')} → "
                f"{case.get('mitigation', '?')} (severity:{case.get('severity', '?')}) | "
                f"{case.get('source_agent', '?')} | "
                f"reason: {case.get('reason', 'N/A')[:100]} | "
                f"similarity:{case.get('similarity_score', 0):.2f}\n"
            )
        
        ctx.logger.info(f"[CALIBRATION]   RAG Context: {total_cases} similar cases retrieved")
    
    # Prepare custom rules context
    if not custom_rules:
        rules_context = "No custom security rules defined."
        total_rules = 0
    else:
        total_rules = len(custom_rules)
        
        # Format custom rules for LLM
        rules_context = f"Retrieved {total_rules} relevant custom security rules:\n"
        
        for i, rule in enumerate(custom_rules[:5], 1):
            rules_context += (
                f"{i}. [{rule.get('category', 'general')}] (severity:{rule.get('severity', 'medium')}) "
                f"{rule.get('refined_text', rule.get('original_text', 'N/A'))} | "
                f"similarity:{rule.get('similarity_score', 0):.2f}\n"
            )
        
        ctx.logger.info(f"[CALIBRATION]   Custom Rules: {total_rules} relevant rules retrieved")
    
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

CUSTOM SECURITY RULES (RAG):
{rules_context}

Based on these historical patterns, custom security rules, and past decisions for similar threats, decide whether to AMPLIFY, DOWNGRADE, or KEEP_ORIGINAL for this mitigation.
Consider both the historical incident patterns and any applicable custom rules in your decision.
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
            "rules_analyzed": total_rules,
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
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
    - mitigation:ip:{ip_address} -> mitigation type ("delay", "captcha", "temp_block", "ban")
    - mitigation:user:{username} -> mitigation type ("delay", "captcha", "temp_block", "ban")
    """
    try:
        from db.redis import redis_client
        
        # Use the mitigation type directly (middleware expects: "delay", "captcha", "temp_block", "ban")
        mitigation_type = mitigation.mitigation
        
        # Apply to Redis based on entity type
        if mitigation.entity_type == "ip":
            key = f"mitigation:ip:{mitigation.entity}"
            await redis_client.set_value(key, mitigation_type, expiry=60)  # 1 minute TTL (demo)
            ctx.logger.info(f"[CALIBRATION]   Set Redis: {key} = {mitigation_type} (severity: {mitigation.severity}, TTL: 1min)")
            
        elif mitigation.entity_type == "user":
            key = f"mitigation:user:{mitigation.entity}"
            await redis_client.set_value(key, mitigation_type, expiry=60)  # 1 minute TTL (demo)
            ctx.logger.info(f"[CALIBRATION]   Set Redis: {key} = {mitigation_type} (severity: {mitigation.severity}, TTL: 1min)")
        
        # Also store mitigation details for debugging
        details_key = f"{key}:details"
        details = {
            "mitigation": mitigation.mitigation,
            "severity": mitigation.severity,
            "reason": mitigation.reason,
            "timestamp": datetime.now().isoformat(),
            "source_agent": mitigation.source_agent
        }
        await redis_client.set_value(details_key, json.dumps(details), expiry=60)
        
    except Exception as e:
        ctx.logger.error(f"[CALIBRATION] Error applying to Redis: {e}")
        ctx.logger.error(f"[CALIBRATION] Mitigation will not be enforced by middleware!")


# Setup Chat Protocol support
chat_protocol = Protocol(spec=chat_protocol_spec)

@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    # send the acknowledgement for receiving the message
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )
 
    # collect up all the text chunks
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    try:
        # Try to parse the text as JSON to create a MitigationBatch
        parsed_data = json.loads(text)
        
        # Handle different input formats
        if isinstance(parsed_data, dict):
            # Check if it has a "mitigations" key (wrapped format)
            if "mitigations" in parsed_data:
                mitigation_batch = MitigationBatch(**parsed_data)
            else:
                # Treat the dict as a single mitigation and wrap it in a batch
                mitigation = Mitigation(**parsed_data)
                mitigation_batch = MitigationBatch(
                    mitigations=[mitigation],
                    source_agent=parsed_data.get("source_agent", "unknown")
                )
        elif isinstance(parsed_data, list):
            # Direct list of mitigations (unwrapped format)
            mitigation_batch = MitigationBatch(
                mitigations=[Mitigation(**m) for m in parsed_data],
                source_agent="unknown"
            )
        else:
            response = f'Could not parse mitigation batch. Received type: {type(parsed_data).__name__}'
            raise ValueError(response)
        
        # Process the mitigation batch
        await handle_mitigation_batch(ctx, sender, mitigation_batch)
        
        response = f'Mitigation batch received and processed successfully. {len(mitigation_batch.mitigations)} mitigation(s) calibrated and applied.'
    except json.JSONDecodeError as e:
        response = f'Could not parse JSON from the message: {str(e)}'
    except Exception as e:
        response = f'Could not process mitigation batch: {str(e)}'
        ctx.logger.error(f"[CALIBRATION] Error processing chat message: {e}")

    # send the response back to the user
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=response),
            EndSessionContent(type="end-session"),
        ]
    ))

@chat_protocol.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass

agent.include(chat_protocol, publish_manifest=True)


if __name__ == "__main__":
    agent.run()