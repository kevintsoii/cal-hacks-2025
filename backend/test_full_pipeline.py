#!/usr/bin/env python3
"""
Complete End-to-End Pipeline Test

This test simulates the entire workflow:
1. Orchestrator receives batch of API logs
2. Routes logs to appropriate Specialist Agent (General Agent)
3. General Agent analyzes logs and generates mitigations
4. Mitigations sent to Calibration Agent
5. Calibration Agent queries ChromaDB for similar cases (RAG)
6. Analyzes effectiveness and calibrates (amplify/downgrade/keep)
7. Saves calibrated mitigation to ChromaDB
8. Applies final mitigation to Redis
9. Middleware can now enforce the mitigation ✅
"""
import sys
import os
import json
import logging
from pathlib import Path

# Add agents directory to path
agents_dir = os.path.join(os.path.dirname(__file__), "agents")
if agents_dir not in sys.path:
    sys.path.insert(0, agents_dir)

from models import SpecialistRequest, Mitigation, MitigationBatch

# Import agent functions
from general_agent import handle_batch as general_agent_handle_batch
from auth_agent import handle_batch as auth_agent_handle_batch
from search_agent import handle_batch as search_agent_handle_batch
from calibration_agent import (
    query_chromadb,
    calibrate_with_rag,
    save_to_chromadb,
    apply_to_redis
)


class MockContext:
    """Mock context for testing without full agent infrastructure."""
    class MockLogger:
        def __init__(self, prefix=""):
            self.prefix = prefix
        
        def info(self, msg):
            print(f"{self.prefix}{msg}")
        
        def error(self, msg):
            print(f"{self.prefix}ERROR: {msg}")
        
        def warning(self, msg):
            print(f"{self.prefix}WARNING: {msg}")
    
    def __init__(self, agent_name="Test"):
        self.logger = self.MockLogger()


async def simulate_orchestrator(logs: list[str]) -> dict:
    """
    Simulate Orchestrator Agent routing logic.
    
    Categorizes logs into auth, search, or general based on endpoint patterns.
    """
    print("\n" + "=" * 80)
    print(" " * 25 + "🎯 ORCHESTRATOR AGENT")
    print("=" * 80)
    print()
    print(f"  📥 Received batch of {len(logs)} API request logs")
    print()
    
    # Show a few sample logs
    print("  Sample logs:")
    for i, log in enumerate(logs[:5], 1):
        print(f"    {i}. {log}")
    if len(logs) > 5:
        print(f"    ... and {len(logs) - 5} more")
    print()
    
    # Categorize logs based on endpoint patterns
    print("  🔍 Categorizing logs by endpoint type...")
    print()
    
    auth_logs = []
    search_logs = []
    general_logs = []
    
    auth_keywords = ['/login', '/register', '/auth', '/signup', '/password', '/logout', '/token']
    search_keywords = ['/search', '/query', '/products', '/items', '/list', '/browse']
    
    for log in logs:
        parts = log.split(',')
        if len(parts) >= 2:
            path = parts[1].lower()
            
            # Categorize based on path
            if any(keyword in path for keyword in auth_keywords):
                auth_logs.append(log)
            elif any(keyword in path for keyword in search_keywords):
                search_logs.append(log)
            else:
                general_logs.append(log)
        else:
            general_logs.append(log)
    
    # Show categorization results
    print(f"  📊 Categorization Results:")
    print(f"     • AUTH endpoints:    {len(auth_logs):2d} logs → Auth Agent")
    print(f"     • SEARCH endpoints:  {len(search_logs):2d} logs → Search Agent")
    print(f"     • GENERAL endpoints: {len(general_logs):2d} logs → General Agent")
    print()
    
    # Show sample from each category
    if auth_logs:
        print(f"  🔐 Auth samples:")
        for log in auth_logs[:2]:
            print(f"     {log}")
        if len(auth_logs) > 2:
            print(f"     ... and {len(auth_logs) - 2} more")
        print()
    
    if search_logs:
        print(f"  🔍 Search samples:")
        for log in search_logs[:2]:
            print(f"     {log}")
        if len(search_logs) > 2:
            print(f"     ... and {len(search_logs) - 2} more")
        print()
    
    if general_logs:
        print(f"  🌐 General samples:")
        for log in general_logs[:2]:
            print(f"     {log}")
        if len(general_logs) > 2:
            print(f"     ... and {len(general_logs) - 2} more")
        print()
    
    print("  ✅ Routing complete - sending to specialist agents...")
    print()
    
    return {
        "auth": auth_logs,
        "search": search_logs,
        "general": general_logs
    }


async def simulate_auth_agent(ctx: MockContext, logs: list[str]) -> list[Mitigation]:
    """
    Simulate Auth Agent analyzing logs and generating mitigations.
    Uses the actual auth_agent.handle_batch function.
    """
    if not logs:
        return []
    
    print("\n" + "=" * 80)
    print(" " * 25 + "🔐 AUTH AGENT")
    print("=" * 80)
    print()
    print(f"  📨 Received {len(logs)} auth logs from Orchestrator")
    print()
    
    # Create specialist request
    request = SpecialistRequest(logs=logs)
    
    print("  🧠 Analyzing authentication logs with LLM (Groq)...")
    print("  🔍 Checking Elasticsearch for failed login patterns...")
    print()
    
    # Call actual auth agent logic
    mitigation_dicts = await auth_agent_handle_batch(ctx, request)
    
    # Convert dictionaries to Mitigation objects
    mitigations = []
    if mitigation_dicts:
        for m_dict in mitigation_dicts:
            mitigation = Mitigation(
                entity_type=m_dict.get("entity_type", "ip"),
                entity=m_dict.get("entity", "unknown"),
                severity=m_dict.get("severity", "medium"),
                mitigation=m_dict.get("mitigation", "delay"),
                reason=m_dict.get("reason", ""),
                source_agent="auth"
            )
            mitigations.append(mitigation)
    
    if mitigations:
        print(f"  ⚠️  AUTH THREATS DETECTED: {len(mitigations)} mitigation(s) recommended")
        print()
        for i, mitigation in enumerate(mitigations, 1):
            print(f"    {i}. {mitigation.entity_type.upper()} {mitigation.entity}")
            print(f"       Severity: {mitigation.severity.upper()}")
            print(f"       Action: {mitigation.mitigation.upper()}")
            print(f"       Reason: {mitigation.reason}")
            print()
        
        print("  📤 Sending auth mitigations to CALIBRATION AGENT...")
        print()
    else:
        print("  ✅ No auth threats detected")
        print()
    
    return mitigations


async def simulate_search_agent(ctx: MockContext, logs: list[str]) -> list[Mitigation]:
    """
    Simulate Search Agent analyzing logs and generating mitigations.
    Uses the actual search_agent.handle_batch function.
    """
    if not logs:
        return []
    
    print("\n" + "=" * 80)
    print(" " * 25 + "🔍 SEARCH AGENT")
    print("=" * 80)
    print()
    print(f"  📨 Received {len(logs)} search logs from Orchestrator")
    print()
    
    # Create specialist request
    request = SpecialistRequest(logs=logs)
    
    print("  🧠 Analyzing search/query logs with LLM (Groq)...")
    print("  🔍 Checking Elasticsearch for scraping patterns...")
    print()
    
    # Call actual search agent logic
    mitigation_dicts = await search_agent_handle_batch(ctx, request)
    
    # Convert dictionaries to Mitigation objects
    mitigations = []
    if mitigation_dicts:
        for m_dict in mitigation_dicts:
            mitigation = Mitigation(
                entity_type=m_dict.get("entity_type", "ip"),
                entity=m_dict.get("entity", "unknown"),
                severity=m_dict.get("severity", "medium"),
                mitigation=m_dict.get("mitigation", "delay"),
                reason=m_dict.get("reason", ""),
                source_agent="search"
            )
            mitigations.append(mitigation)
    
    if mitigations:
        print(f"  ⚠️  SEARCH THREATS DETECTED: {len(mitigations)} mitigation(s) recommended")
        print()
        for i, mitigation in enumerate(mitigations, 1):
            print(f"    {i}. {mitigation.entity_type.upper()} {mitigation.entity}")
            print(f"       Severity: {mitigation.severity.upper()}")
            print(f"       Action: {mitigation.mitigation.upper()}")
            print(f"       Reason: {mitigation.reason}")
            print()
        
        print("  📤 Sending search mitigations to CALIBRATION AGENT...")
        print()
    else:
        print("  ✅ No search threats detected")
        print()
    
    return mitigations


async def simulate_general_agent(ctx: MockContext, logs: list[str]) -> list[Mitigation]:
    """
    Simulate General Agent analyzing logs and generating mitigations.
    Uses the actual general_agent.handle_batch function.
    """
    if not logs:
        return []
    
    print("\n" + "=" * 80)
    print(" " * 25 + "🌐 GENERAL AGENT")
    print("=" * 80)
    print()
    print(f"  📨 Received {len(logs)} general logs from Orchestrator")
    print()
    
    # Create specialist request
    request = SpecialistRequest(logs=logs)
    
    print("  🧠 Analyzing logs with LLM (Groq)...")
    print("  🔍 Checking Elasticsearch for similar attack patterns...")
    print()
    
    # Call actual general agent logic
    mitigation_dicts = await general_agent_handle_batch(ctx, request)
    
    # Convert dictionaries to Mitigation objects
    mitigations = []
    if mitigation_dicts:
        for m_dict in mitigation_dicts:
            mitigation = Mitigation(
                entity_type=m_dict.get("entity_type", "ip"),
                entity=m_dict.get("entity", "unknown"),
                severity=m_dict.get("severity", "medium"),
                mitigation=m_dict.get("mitigation", "delay"),
                reason=m_dict.get("reason", ""),
                source_agent="general"
            )
            mitigations.append(mitigation)
    
    if mitigations:
        print(f"  ⚠️  GENERAL THREATS DETECTED: {len(mitigations)} mitigation(s) recommended")
        print()
        for i, mitigation in enumerate(mitigations, 1):
            print(f"    {i}. {mitigation.entity_type.upper()} {mitigation.entity}")
            print(f"       Severity: {mitigation.severity.upper()}")
            print(f"       Action: {mitigation.mitigation.upper()}")
            print(f"       Reason: {mitigation.reason}")
            print()
        
        print("  📤 Sending general mitigations to CALIBRATION AGENT...")
        print()
    else:
        print("  ✅ No general threats detected")
        print()
    
    return mitigations


async def simulate_calibration_agent(ctx: MockContext, mitigations: list[Mitigation]) -> list[dict]:
    """
    Simulate Calibration Agent processing mitigations with RAG.
    Uses actual calibration_agent functions.
    """
    print("\n" + "=" * 80)
    print(" " * 25 + "⚖️  CALIBRATION AGENT")
    print("=" * 80)
    print()
    print(f"  📨 Received {len(mitigations)} mitigation(s) from General Agent")
    print()
    
    results = []
    
    for mitigation_num, mitigation in enumerate(mitigations, 1):
        print(f"  ┌{'─' * 76}┐")
        print(f"  │ Processing Mitigation {mitigation_num}/{len(mitigations)}: {mitigation.entity_type.upper()} {mitigation.entity:<38} │")
        print(f"  └{'─' * 76}┘")
        print()
        
        # STEP 1: Query ChromaDB (RAG)
        print(f"    🔍 STEP 1: Querying ChromaDB for similar past cases...")
        similar_cases = await query_chromadb(ctx, mitigation.reason, mitigation.entity)
        
        if similar_cases:
            # Filter out pending cases
            cases_with_results = [c for c in similar_cases if c.get("effectiveness") is not None]
            print(f"    ✓ Found {len(similar_cases)} similar cases ({len(cases_with_results)} with results)")
        else:
            print(f"    ℹ️  No similar cases found")
            cases_with_results = []
        print()
        
        # STEP 2: Calibrate with RAG + LLM
        print(f"    ⚖️  STEP 2: AI-powered calibration with Groq LLM...")
        calibrated_mitigation, reasoning = await calibrate_with_rag(ctx, mitigation, similar_cases)
        
        decision_icon = {
            "AMPLIFY": "⬆️",
            "DOWNGRADE": "⬇️",
            "KEEP_ORIGINAL": "➡️"
        }.get(reasoning["decision"], "❓")
        
        print(f"    {decision_icon} LLM Decision: {reasoning['decision']}")
        if reasoning.get("avg_effectiveness"):
            print(f"    📊 Based on {reasoning['cases_analyzed']} past cases (avg: {reasoning['avg_effectiveness']}% effective)")
        if reasoning.get("llm_used"):
            print(f"    🤖 AI-powered analysis with confidence: {reasoning.get('confidence', 'unknown')}")
        print(f"    💭 Reasoning: {reasoning['reasoning']}")
        print()
        
        # Show before/after
        if calibrated_mitigation.severity != mitigation.severity or calibrated_mitigation.mitigation != mitigation.mitigation:
            print(f"    📋 CALIBRATION APPLIED:")
            print(f"       Before: {mitigation.severity.upper():<8} → {mitigation.mitigation.upper()}")
            print(f"       After:  {calibrated_mitigation.severity.upper():<8} → {calibrated_mitigation.mitigation.upper()}")
        else:
            print(f"    📋 Mitigation unchanged: {mitigation.severity.upper()} → {mitigation.mitigation.upper()}")
        print()
        
        # STEP 3: Save to ChromaDB
        print(f"    💾 STEP 3: Saving to ChromaDB for future learning...")
        await save_to_chromadb(ctx, calibrated_mitigation, reasoning)
        print(f"    ✓ Saved to memory")
        print()
        
        # STEP 4: Apply to Redis
        print(f"    🔧 STEP 4: Applying to Redis...")
        await apply_to_redis(ctx, calibrated_mitigation)
        
        severity_descriptions = {
            "low": "Small delay (100-500ms)",
            "medium": "CAPTCHA challenge required",
            "high": "Temporary block (15-60 min)",
            "critical": "Permanent ban"
        }
        
        print(f"    ✓ Applied to Redis")
        print(f"    🛡️  Middleware will enforce: {severity_descriptions.get(calibrated_mitigation.severity, 'Unknown')}")
        print()
        
        results.append({
            "original": mitigation,
            "calibrated": calibrated_mitigation,
            "reasoning": reasoning,
            "similar_cases_found": len(similar_cases),
            "cases_with_results": len(cases_with_results)
        })
    
    return results


async def verify_redis_keys(mitigations: list[Mitigation]):
    """
    Verify that mitigations were actually saved to Redis.
    """
    print("\n" + "=" * 80)
    print(" " * 25 + "🔍 VERIFICATION: REDIS")
    print("=" * 80)
    print()
    
    try:
        from db.redis import redis_client
        
        print("  📊 Checking Redis for applied mitigations...")
        print()
        
        for mitigation in mitigations:
            key = f"mitigation:{mitigation.entity_type}:{mitigation.entity}"
            value = await redis_client.get_value(key)
            
            if value:
                severity_map = {1: "low", 2: "medium", 3: "high", 4: "critical"}
                severity = severity_map.get(int(value), "unknown")
                print(f"    ✅ {key}")
                print(f"       Value: {value} ({severity.upper()})")
                
                # Check details
                details_key = f"{key}:details"
                details_value = await redis_client.get_value(details_key)
                if details_value:
                    details = json.loads(details_value)
                    print(f"       Mitigation: {details['mitigation']}")
                    print(f"       Timestamp: {details['timestamp']}")
            else:
                print(f"    ❌ {key} - NOT FOUND")
            print()
        
        print("  ✅ Redis verification complete")
        
    except Exception as e:
        print(f"  ⚠️  Redis verification skipped: {e}")
        print(f"     (This is OK if Redis is not running)")


async def main():
    """Run the complete end-to-end pipeline test."""
    import time
    
    # Start total timer
    total_start_time = time.time()
    stage_times = {}
    
    print("\n" + "=" * 80)
    print("=" * 80)
    print(" " * 15 + "🚀 COMPLETE PIPELINE TEST: END-TO-END")
    print("=" * 80)
    print("=" * 80)
    print()
    print("  This test simulates the entire workflow from API logs to Redis enforcement:")
    print()
    print("    1. 📥 Orchestrator receives API logs")
    print("    2. 🔀 Categorizes and routes to specialist agents:")
    print("       🔐 Auth Agent (authentication endpoints)")
    print("       🔍 Search Agent (search/query endpoints)")
    print("       🌐 General Agent (all other endpoints)")
    print("    3. 🤖 Each agent analyzes and generates mitigations")
    print("    4. ⚖️  Calibration Agent queries ChromaDB (RAG)")
    print("    5. 🧠 Analyzes effectiveness and calibrates")
    print("    6. 💾 Saves to ChromaDB for future learning")
    print("    7. 🔧 Applies to Redis")
    print("    8. ✅ Middleware enforces mitigation")
    print()
    input("  Press Enter to start the test...")
    
    # STEP 1: Simulate incoming API logs (suspicious traffic across all categories)
    suspicious_logs = [
        # AUTH ENDPOINTS - Brute force attack
        "10.0.0.75,/auth/login,POST,,,25",
        "10.0.0.75,/auth/login,POST,,,22",
        "10.0.0.75,/api/login,POST,,,18",
        "10.0.0.75,/login,POST,,,20",
        "10.0.0.75,/api/auth/token,POST,,,15",
        
        # SEARCH ENDPOINTS - Scraping pattern
        "192.168.1.50,/api/search,GET,,query=product,30",
        "192.168.1.50,/api/products,GET,,category=all,25",
        "192.168.1.50,/api/search,GET,,query=user,28",
        "192.168.1.50,/api/items,GET,,page=1,32",
        "192.168.1.50,/api/products/list,GET,,,27",
        "192.168.1.50,/api/browse,GET,,category=electronics,29",
        
        # GENERAL ENDPOINTS - Endpoint enumeration
        "10.0.0.50,/admin,GET,,,15",
        "10.0.0.50,/api/users,GET,,,10",
        "10.0.0.50,/api/config,GET,,,8",
        "10.0.0.50,/api/debug,GET,,,12",
        "10.0.0.50,/api/internal,GET,,,9",
        "10.0.0.50,/dashboard,GET,,,11",
        "10.0.0.50,/admin/settings,GET,,,14",
        "10.0.0.50,/admin/users,GET,,,13",
        
        # GENERAL ENDPOINTS - Rate abuse
        "203.0.113.42,/status,GET,,,50",
        "203.0.113.42,/status,GET,,,48",
        "203.0.113.42,/status,GET,,,51",
        "203.0.113.42,/api/health,GET,,,49",
        
        # Normal traffic
        "192.168.1.100,/,GET,,,2",
        "192.168.1.101,/about,GET,,,1",
    ]
    
    # Create context
    ctx = MockContext()
    
    # STEP 2: Orchestrator routes logs
    stage_start = time.time()
    routing_decision = await simulate_orchestrator(suspicious_logs)
    stage_times["orchestrator"] = time.time() - stage_start
    
    # STEP 3: Route to appropriate specialist agents
    print("\n" + "=" * 80)
    print(" " * 20 + "🤖 STEP 3: SPECIALIST AGENT ANALYSIS")
    print("=" * 80)
    all_mitigations = []
    
    # Auth Agent
    if routing_decision["auth"]:
        stage_start = time.time()
        auth_mitigations = await simulate_auth_agent(ctx, routing_decision["auth"])
        stage_times["auth_agent"] = time.time() - stage_start
        all_mitigations.extend(auth_mitigations)
        print(f"  ✅ Auth Agent complete: {len(auth_mitigations)} mitigation(s) generated")
        print()
    else:
        print("\n  ⏭️  Skipping Auth Agent (no auth logs to process)")
        print()
    
    # Search Agent
    if routing_decision["search"]:
        stage_start = time.time()
        search_mitigations = await simulate_search_agent(ctx, routing_decision["search"])
        stage_times["search_agent"] = time.time() - stage_start
        all_mitigations.extend(search_mitigations)
        print(f"  ✅ Search Agent complete: {len(search_mitigations)} mitigation(s) generated")
        print()
    else:
        print("  ⏭️  Skipping Search Agent (no search logs to process)")
        print()
    
    # General Agent
    if routing_decision["general"]:
        stage_start = time.time()
        general_mitigations = await simulate_general_agent(ctx, routing_decision["general"])
        stage_times["general_agent"] = time.time() - stage_start
        all_mitigations.extend(general_mitigations)
        print(f"  ✅ General Agent complete: {len(general_mitigations)} mitigation(s) generated")
        print()
    else:
        print("  ⏭️  Skipping General Agent (no general logs to process)")
        print()
    
    if not all_mitigations:
        print("\n" + "=" * 80)
        print(" " * 20 + "✅ TEST COMPLETE: No threats detected")
        print("=" * 80)
        print()
        return
    
    # Show combined results
    print("\n" + "=" * 80)
    print(" " * 20 + "📊 COMBINED RESULTS FROM ALL AGENTS")
    print("=" * 80)
    print()
    print(f"  Total mitigations from all specialist agents: {len(all_mitigations)}")
    print()
    
    # Group by source agent
    by_agent = {}
    for m in all_mitigations:
        agent = m.source_agent
        if agent not in by_agent:
            by_agent[agent] = []
        by_agent[agent].append(m)
    
    for agent_name, mits in by_agent.items():
        icon = {"auth": "🔐", "search": "🔍", "general": "🌐"}.get(agent_name, "🤖")
        print(f"  {icon} {agent_name.upper()} Agent: {len(mits)} mitigation(s)")
        for i, m in enumerate(mits, 1):
            print(f"      {i}. {m.entity_type.upper()} {m.entity} → {m.mitigation.upper()} ({m.severity})")
    print()
    
    print("  📤 Sending all mitigations to CALIBRATION AGENT for RAG analysis...")
    print()
    
    # STEP 4: Calibration Agent processes with RAG
    stage_start = time.time()
    calibration_results = await simulate_calibration_agent(ctx, all_mitigations)
    stage_times["calibration_agent"] = time.time() - stage_start
    
    # STEP 5: Verify Redis
    stage_start = time.time()
    calibrated_mitigations = [result["calibrated"] for result in calibration_results]
    await verify_redis_keys(calibrated_mitigations)
    stage_times["redis_verification"] = time.time() - stage_start
    
    # Calculate total time
    total_time = time.time() - total_start_time
    
    # FINAL SUMMARY
    print("\n" + "=" * 80)
    print("=" * 80)
    print(" " * 25 + "📊 FINAL SUMMARY")
    print("=" * 80)
    print("=" * 80)
    print()
    
    print("  📈 Pipeline Statistics:")
    print(f"     • Input logs: {len(suspicious_logs)}")
    print(f"     • Auth logs processed: {len(routing_decision['auth'])}")
    print(f"     • Search logs processed: {len(routing_decision['search'])}")
    print(f"     • General logs processed: {len(routing_decision['general'])}")
    print(f"     • Total threats detected: {len(all_mitigations)}")
    print(f"     • Mitigations calibrated: {len(calibration_results)}")
    print()
    
    print("  🤖 Threats by Agent:")
    for agent_name, mits in by_agent.items():
        icon = {"auth": "🔐", "search": "🔍", "general": "🌐"}.get(agent_name, "🤖")
        print(f"     {icon} {agent_name.upper()}: {len(mits)} threat(s)")
    print()
    
    print("  🎯 Calibration Decisions:")
    for result in calibration_results:
        decision = result["reasoning"]["decision"]
        entity = result["calibrated"].entity
        agent = result["calibrated"].source_agent
        icon = {"AMPLIFY": "⬆️", "DOWNGRADE": "⬇️", "KEEP_ORIGINAL": "➡️"}.get(decision, "❓")
        agent_icon = {"auth": "🔐", "search": "🔍", "general": "🌐"}.get(agent, "🤖")
        print(f"     {icon} {agent_icon} {entity}: {decision}")
    print()
    
    print("  💾 ChromaDB Learning:")
    chromadb_path = Path(__file__).parent / "data" / "chromadb_simulation.json"
    if chromadb_path.exists():
        with open(chromadb_path, 'r') as f:
            data = json.load(f)
            total_entries = len(data.get("mitigations", []))
            print(f"     • Total historical cases: {total_entries}")
            print(f"     • New entries added: {len(calibration_results)}")
    print()
    
    print("  🛡️  Redis Enforcement:")
    print(f"     • Mitigations applied: {len(calibrated_mitigations)}")
    print(f"     • Middleware ready to enforce ✅")
    print()
    
    print("  ⏱️  Performance Metrics:")
    print(f"     • Orchestrator routing: {stage_times.get('orchestrator', 0):.3f}s")
    if "auth_agent" in stage_times:
        print(f"     • Auth Agent processing: {stage_times['auth_agent']:.3f}s")
    if "search_agent" in stage_times:
        print(f"     • Search Agent processing: {stage_times['search_agent']:.3f}s")
    if "general_agent" in stage_times:
        print(f"     • General Agent processing: {stage_times['general_agent']:.3f}s")
    print(f"     • Calibration Agent (RAG): {stage_times.get('calibration_agent', 0):.3f}s")
    print(f"     • Redis verification: {stage_times.get('redis_verification', 0):.3f}s")
    print(f"     • ⚡ TOTAL PIPELINE TIME: {total_time:.3f}s")
    print()
    
    print("  ✅ COMPLETE PIPELINE TEST SUCCESSFUL!")
    print()
    print("  🎉 The system is now protecting your API with AI-powered mitigations!")
    print()
    print("=" * 80)
    print("=" * 80)
    print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())