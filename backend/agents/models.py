from uagents import Model
from typing import List, Optional

# 1. DATA MODELS


class APIRequestLog(Model):
    """A single API request log entry."""
    ip_address: Optional[str] = None
    path: str
    method: str
    user_id: Optional[str] = None
    json_body: Optional[str] = None


class RequestBatch(Model):
    """The batch of requests sent FROM FastAPI TO the Orchestrator."""
    requests: List[APIRequestLog]


class OrchestratorResponse(Model):
    success: bool


class SpecialistRequest(Model):
    """A list of strings sent to specialist agents."""
    logs: List[str]


class Mitigation(Model):
    """A single mitigation recommendation."""
    entity_type: str  # "ip" or "user"
    entity: str  # IP address or username
    severity: str  # "low", "medium", "high", "critical"
    mitigation: str  # "delay", "captcha", "temp_block", "ban"
    reason: str  # Explanation
    source_agent: Optional[str] = None  # Which agent detected it (auth/search/general)


class MitigationBatch(Model):
    """Batch of mitigations sent to Calibration Agent."""
    mitigations: List[Mitigation]
    source_agent: str  # "auth", "search", or "general"






def clean_llm_output(llm_output_str: str) -> str:
    """
    Clean the LLM output string to remove markdown code blocks and extra whitespace.
    
    Args:
        llm_output_str: Raw output string from the LLM
        
    Returns:
        Cleaned output string with markdown code blocks removed
    """
    # Remove opening markdown code blocks
    if llm_output_str.startswith("```json"):
        llm_output_str = llm_output_str[7:]  # Remove ```json
    elif llm_output_str.startswith("```"):
        llm_output_str = llm_output_str[3:]  # Remove ```
    
    # Remove closing markdown code blocks
    if llm_output_str.endswith("```"):
        llm_output_str = llm_output_str[:-3]  # Remove trailing ```
    
    return llm_output_str.strip()  # Remove any extra whitespace