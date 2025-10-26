"""
Custom Security Rules API Routes for Calibration Agent
Allows users to define security rules in plain English, which are refined by Groq AI
and stored in ChromaDB for the calibration agent to reference.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import httpx
import os
import json

router = APIRouter()

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ChromaDB service URL
CHROMADB_SERVICE_URL = os.getenv("CHROMADB_SERVICE_URL", "http://localhost:9000")


class RuleCreate(BaseModel):
    """Request model for creating a new rule"""
    user_input: str


class Rule(BaseModel):
    """Response model for a rule"""
    id: str
    original_text: str
    refined_text: str
    category: str
    severity: str
    timestamp: str


class RulesResponse(BaseModel):
    """Response model for list of rules"""
    rules: List[Rule]
    count: int


async def refine_rule_with_groq(user_input: str) -> dict:
    """
    Use Groq AI to refine and categorize a user's security rule.
    
    Returns:
        dict with keys: refined_text, category, severity
    """
    system_prompt = """You are a cybersecurity expert. The user will provide a security rule in plain English.
Your job is to:
1. Refine the rule to be more specific, clear, and actionable
2. Categorize it (auth, search, rate_limit, data_access, sql_injection, etc.)
3. Assign a severity level (low, medium, high, critical)

Respond in JSON format:
{
    "refined_text": "Clear, specific rule description with concrete thresholds and actions",
    "category": "category_name",
    "severity": "severity_level"
}

Examples:
User: "Block users who try too many passwords"
You: {"refined_text": "Block IP addresses that attempt more than 10 failed login attempts within 5 minutes with a temporary block for 30 minutes", "category": "auth", "severity": "high"}

User: "Stop scrapers"
You: {"refined_text": "Apply CAPTCHA to IP addresses making more than 100 requests per minute to search endpoints, and temporarily block after 3 CAPTCHA failures", "category": "rate_limit", "severity": "medium"}
"""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Groq API error: {response.text}")
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            refined_data = json.loads(content)
            
            return refined_data
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refining rule: {str(e)}")


@router.post("/api/calibration-rules", response_model=Rule)
async def create_rule(rule_input: RuleCreate):
    """
    Create a new custom security rule for the Calibration Agent.
    
    1. User provides rule in plain English
    2. Groq refines it and adds category/severity
    3. Store in ChromaDB with semantic embeddings
    4. Return the created rule
    """
    try:
        # Step 1: Refine with Groq
        refined_data = await refine_rule_with_groq(rule_input.user_input)
        
        # Step 2: Store in ChromaDB
        rule_id = f"rule_{datetime.now().timestamp()}"
        timestamp = datetime.now().isoformat()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Add to ChromaDB custom_rules collection
            response = await client.post(
                f"{CHROMADB_SERVICE_URL}/rules/add",
                json={
                    "rule_id": rule_id,
                    "original_text": rule_input.user_input,
                    "refined_text": refined_data["refined_text"],
                    "category": refined_data["category"],
                    "severity": refined_data["severity"],
                    "timestamp": timestamp
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"ChromaDB error: {response.text}")
        
        # Step 3: Return created rule
        return Rule(
            id=rule_id,
            original_text=rule_input.user_input,
            refined_text=refined_data["refined_text"],
            category=refined_data["category"],
            severity=refined_data["severity"],
            timestamp=timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating rule: {str(e)}")


@router.get("/api/calibration-rules", response_model=RulesResponse)
async def get_rules():
    """
    Retrieve all custom security rules from ChromaDB for the Calibration Agent.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{CHROMADB_SERVICE_URL}/rules/all")
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=503, 
                    detail="ChromaDB service is not available. Please ensure it's running on port 9000."
                )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"ChromaDB error: {response.text}")
            
            data = response.json()
            rules = []
            
            for item in data.get("rules", []):
                try:
                    rules.append(Rule(
                        id=item.get("id", ""),
                        original_text=item.get("original_text", ""),
                        refined_text=item.get("refined_text", ""),
                        category=item.get("category", "general"),
                        severity=item.get("severity", "medium"),
                        timestamp=item.get("timestamp", "")
                    ))
                except Exception as e:
                    # Log but don't fail the entire request if one rule is malformed
                    print(f"Error parsing rule {item.get('id', 'unknown')}: {e}")
                    continue
            
            # Sort by timestamp (newest first)
            rules.sort(key=lambda x: x.timestamp, reverse=True)
            
            return RulesResponse(rules=rules, count=len(rules))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")


@router.delete("/api/calibration-rules/{rule_id}")
async def delete_rule(rule_id: str):
    """
    Delete a custom security rule from ChromaDB.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"{CHROMADB_SERVICE_URL}/rules/{rule_id}")
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Rule not found")
            elif response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"ChromaDB error: {response.text}")
            
            return {"success": True, "message": f"Rule {rule_id} deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting rule: {str(e)}")

