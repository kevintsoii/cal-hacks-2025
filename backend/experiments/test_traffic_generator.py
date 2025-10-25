#!/usr/bin/env python3
"""
Traffic Generator Script
Sends mixed normal and malicious API requests to test the threat detection system.

NOTE: Only generates GENERAL endpoint traffic (not auth/search) since only 
General Agent is currently connected. Auth and Search agents not yet implemented.

Total: 115 requests (100 attacks + 15 normal)
"""
import requests
import random
import time
from concurrent.futures import ThreadPoolExecutor
import argparse

# Configuration
BASE_URL = "http://localhost:8000"
MOCK_IPS = [
    "192.168.1.100",  # Normal user
    "192.168.1.101",  # Normal user
    "10.0.0.50",      # Attacker IP 1 (brute force)
    "10.0.0.51",      # Attacker IP 2 (scraping)
    "203.0.113.42",   # Attacker IP 3 (rate abuse)
]

NORMAL_USERNAMES = ["alice", "bob", "charlie", "diana", "admin"]
ATTACK_USERNAMES = ["admin", "root", "administrator", "user", "test"]
SEARCH_TERMS = ["user123", "test", "admin", "alice", "bob", "product", "api"]

# Attack patterns - ONLY GENERAL ENDPOINTS (Auth/Search agents not set up yet)
ATTACK_PATTERNS = {
    "rate_abuse_status": {
        "description": "Rapid-fire requests to status endpoint",
        "count": 25,
        "endpoint": "/status",
        "method": "GET",
        "generate_payload": lambda: None
    },
    "endpoint_enumeration": {
        "description": "Scanning different endpoints (reconnaissance)",
        "count": 30,
        "endpoint": lambda: random.choice([
            "/admin", "/api/users", "/api/config", "/api/debug", 
            "/api/healthcheck", "/api/metrics", "/api/internal",
            "/api/settings", "/api/logs", "/dashboard"
        ]),
        "method": "GET",
        "generate_payload": lambda: None
    },
    "ddos_simulation": {
        "description": "DDoS pattern - many requests in short time",
        "count": 30,
        "endpoint": "/",
        "method": "GET",
        "generate_payload": lambda: None
    },
    "api_abuse": {
        "description": "Repeated API endpoint hits",
        "count": 15,
        "endpoint": lambda: random.choice(["/elastic/status", "/redis/status", "/elastic/sample"]),
        "method": "GET",
        "generate_payload": lambda: None
    }
}

# Normal patterns - ONLY GENERAL ENDPOINTS
NORMAL_PATTERNS = {
    "health_check": {
        "description": "Health check requests",
        "count": 5,
        "endpoint": "/status",
        "method": "GET",
        "generate_payload": lambda: None
    },
    "redis_check": {
        "description": "Redis connection checks",
        "count": 3,
        "endpoint": "/redis/status",
        "method": "GET",
        "generate_payload": lambda: None
    },
    "elastic_check": {
        "description": "Elasticsearch connection checks",
        "count": 3,
        "endpoint": "/elastic/status",
        "method": "GET",
        "generate_payload": lambda: None
    },
    "root_endpoint": {
        "description": "Root endpoint requests",
        "count": 4,
        "endpoint": "/",
        "method": "GET",
        "generate_payload": lambda: None
    }
}


def send_request(pattern_name, pattern_config, use_mock_ip=True, delay=0):
    """Send a single request based on pattern configuration."""
    try:
        # Get endpoint (might be a function)
        endpoint = pattern_config["endpoint"]
        if callable(endpoint):
            endpoint = endpoint()
        
        url = f"{BASE_URL}{endpoint}"
        method = pattern_config["method"]
        payload = pattern_config["generate_payload"]()
        
        # Add mock IP header for testing
        headers = {}
        if use_mock_ip:
            mock_ip = random.choice(MOCK_IPS)
            headers["mock-ip"] = mock_ip
        
        # Add delay if specified
        if delay > 0:
            time.sleep(delay)
        
        # Send request
        if method == "POST":
            response = requests.post(url, json=payload, headers=headers, timeout=5)
        else:
            response = requests.get(url, headers=headers, timeout=5)
        
        status_icon = "✓" if response.status_code < 400 else "✗"
        print(f"{status_icon} [{pattern_name}] {method} {endpoint} -> {response.status_code} (IP: {headers.get('mock-ip', 'real')})")
        
        return {
            "pattern": pattern_name,
            "status": response.status_code,
            "success": response.status_code < 400
        }
    
    except requests.RequestException as e:
        print(f"✗ [{pattern_name}] Error: {e}")
        return {
            "pattern": pattern_name,
            "status": None,
            "success": False
        }


def run_attack_simulation(include_attacks=True, include_normal=True, parallel=False, delay=0):
    """Run the full attack simulation."""
    
    print("=" * 80)
    print("🚀 API THREAT DETECTION TEST - Traffic Generator")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Attack patterns: {'Enabled' if include_attacks else 'Disabled'}")
    print(f"Normal traffic: {'Enabled' if include_normal else 'Disabled'}")
    print(f"Execution: {'Parallel' if parallel else 'Sequential'}")
    if delay > 0:
        print(f"Delay: {delay}s between requests")
    print("=" * 80)
    print()
    
    # Build request list
    requests_to_send = []
    
    if include_attacks:
        print("📋 Attack Patterns to Execute:")
        for pattern_name, config in ATTACK_PATTERNS.items():
            print(f"  • {config['description']}: {config['count']} requests")
            for _ in range(config["count"]):
                requests_to_send.append((pattern_name, config))
    
    if include_normal:
        print("\n📋 Normal Patterns to Execute:")
        for pattern_name, config in NORMAL_PATTERNS.items():
            print(f"  • {config['description']}: {config['count']} requests")
            for _ in range(config["count"]):
                requests_to_send.append((pattern_name, config))
    
    print(f"\n📊 Total requests to send: {len(requests_to_send)}")
    print("\n" + "=" * 80)
    print("Starting in 3 seconds...")
    time.sleep(3)
    print()
    
    # Shuffle for more realistic traffic
    random.shuffle(requests_to_send)
    
    # Execute requests
    start_time = time.time()
    results = []
    
    if parallel:
        # Parallel execution (faster but more aggressive)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(send_request, pattern_name, config, True, 0)
                for pattern_name, config in requests_to_send
            ]
            results = [f.result() for f in futures]
    else:
        # Sequential execution (more realistic)
        for pattern_name, config in requests_to_send:
            result = send_request(pattern_name, config, True, delay)
            results.append(result)
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 EXECUTION SUMMARY")
    print("=" * 80)
    
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    print(f"Total requests: {total}")
    print(f"Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed/Blocked: {failed} ({failed/total*100:.1f}%)")
    print(f"Execution time: {elapsed_time:.2f}s")
    print(f"Requests/sec: {total/elapsed_time:.2f}")
    print()
    
    # Pattern breakdown
    print("Pattern Breakdown:")
    pattern_stats = {}
    for result in results:
        pattern = result["pattern"]
        if pattern not in pattern_stats:
            pattern_stats[pattern] = {"total": 0, "success": 0}
        pattern_stats[pattern]["total"] += 1
        if result["success"]:
            pattern_stats[pattern]["success"] += 1
    
    for pattern, stats in sorted(pattern_stats.items()):
        success_rate = stats["success"] / stats["total"] * 100
        print(f"  • {pattern}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
    
    print("\n" + "=" * 80)
    print("✅ Test complete! Check your backend logs for threat detection results.")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Generate mixed API traffic for threat detection testing")
    parser.add_argument("--no-attacks", action="store_true", help="Disable attack patterns (normal traffic only)")
    parser.add_argument("--no-normal", action="store_true", help="Disable normal patterns (attacks only)")
    parser.add_argument("--parallel", action="store_true", help="Execute requests in parallel (faster)")
    parser.add_argument("--delay", type=float, default=0, help="Delay between requests in seconds")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Base API URL")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to repeat the test")
    
    args = parser.parse_args()
    
    global BASE_URL
    BASE_URL = args.url
    
    for i in range(args.repeat):
        if args.repeat > 1:
            print(f"\n{'='*80}")
            print(f"🔄 ROUND {i+1}/{args.repeat}")
            print(f"{'='*80}\n")
        
        run_attack_simulation(
            include_attacks=not args.no_attacks,
            include_normal=not args.no_normal,
            parallel=args.parallel,
            delay=args.delay
        )
        
        if i < args.repeat - 1:
            print(f"\n⏳ Waiting 5 seconds before next round...\n")
            time.sleep(5)


async def test_tool_calling():
    """
    Test the general agent's tool calling functionality with detailed step-by-step output.
    
    Shows:
    1. Initial batch from orchestrator to General Agent
    2. Groq's response (with tool call if any)
    3. Extended batch (original + ES logs if fetched)
    4. Final mitigations
    """
    import sys
    import os
    import logging
    
    # Add the agents directory to the path
    agents_dir = os.path.join(os.path.dirname(__file__), "agents")
    if agents_dir not in sys.path:
        sys.path.insert(0, agents_dir)
    
    from models import SpecialistRequest
    from general_agent import handle_batch
    
    # Create a mock context with a logger
    class MockContext:
        def __init__(self):
            self.logger = logging.getLogger("test")
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('    %(message)s'))
            self.logger.addHandler(handler)
    
    ctx = MockContext()
    
    # Create test batch with suspicious activity from specific IP
    test_logs = [
        "10.0.0.50,/admin,GET,,,15",
        "10.0.0.50,/api/users,GET,,,10",
        "10.0.0.50,/api/config,GET,,,8",
        "10.0.0.50,/api/debug,GET,,,12",
        "10.0.0.50,/dashboard,GET,,,9",
        "203.0.113.42,/status,GET,,,50",
        "203.0.113.42,/,GET,,,45",
        "192.168.1.100,/status,GET,,,2",
        "192.168.1.101,/,GET,,,1",
    ]
    
    request = SpecialistRequest(logs=test_logs)
    
    print("\n" + "=" * 80)
    print(" " * 20 + "🧪 GENERAL AGENT TOOL CALLING TEST")
    print("=" * 80)
    print()
    
    # STEP 1: Show initial batch
    print("┌" + "─" * 78 + "┐")
    print("│ STEP 1: INITIAL BATCH FROM ORCHESTRATOR → GENERAL AGENT" + " " * 20 + "│")
    print("└" + "─" * 78 + "┘")
    print()
    print(f"  📦 Batch Size: {len(test_logs)} logs")
    print(f"  📊 Format: ip_address, path, method, user_id, body, count")
    print()
    print("  Logs:")
    for i, log in enumerate(test_logs, 1):
        # Parse the log to show it nicely
        parts = log.split(',')
        ip = parts[0]
        path = parts[1]
        count = parts[5] if len(parts) > 5 else '1'
        print(f"    {i:2d}. IP: {ip:15s} | Path: {path:20s} | Count: {count:3s}")
    print()
    
    # STEP 2: Call the agent and get detailed results
    print("┌" + "─" * 78 + "┐")
    print("│ STEP 2: GROQ ANALYSIS WITH TOOL CALLING SUPPORT" + " " * 29 + "│")
    print("└" + "─" * 78 + "┘")
    print()
    print("  🤖 Sending batch to Groq LLM with Elasticsearch tool available...")
    print()
    
    try:
        result = await handle_batch(ctx, request, return_metadata=True)
        
        if "error" in result:
            print(f"\n  ❌ Error occurred: {result['error']}")
            return []
        
        tool_called = result.get("tool_called", False) or (es_query is not None)
        es_query = result.get("es_query_used", None)
        additional_logs = result.get("additional_logs_from_es", [])
        
        print()
        if tool_called:
            print("  ✅ Groq Response: TOOL CALL REQUESTED")
            print(f"  🔧 Tool: fetch_from_elasticsearch")
            print(f"  🔍 Query: \"{es_query}\"")
        else:
            print("  ✅ Groq Response: NO TOOL CALL (analyzing with original batch only)")
        print()
        
        # STEP 3: Show extended batch if tool was called
        if tool_called:
            print("┌" + "─" * 78 + "┐")
            print("│ STEP 3: EXTENDED BATCH (ORIGINAL + ELASTICSEARCH LOGS)" + " " * 22 + "│")
            print("└" + "─" * 78 + "┘")
            print()
            print(f"  📊 Original Batch: {result['original_batch_size']} logs")
            print(f"  📊 Additional Logs from ES: {len(additional_logs)} logs")
            print(f"  📊 Total Extended Batch: {result['extended_batch_size']} logs")
            print()
            
            if additional_logs:
                print(f"  Additional logs retrieved from Elasticsearch:")
                for i, log in enumerate(additional_logs[:10], 1):
                    parts = log.split(',')
                    ip = parts[0] if len(parts) > 0 else 'unknown'
                    path = parts[1] if len(parts) > 1 else '/'
                    count = parts[5] if len(parts) > 5 else '1'
                    print(f"    {i:2d}. IP: {ip:15s} | Path: {path:20s} | Count: {count:3s}")
                
                if len(additional_logs) > 10:
                    print(f"    ... and {len(additional_logs) - 10} more logs")
            
            print()
            print("  🔄 Sending extended batch back to Groq for complete analysis...")
            print()
        else:
            print("┌" + "─" * 78 + "┐")
            print("│ STEP 3: BATCH ANALYSIS (NO EXTENSION NEEDED)" + " " * 31 + "│")
            print("└" + "─" * 78 + "┘")
            print()
            print("  ℹ️  Groq determined that the original batch contains sufficient context.")
            print("  ℹ️  Proceeding with analysis of original 9 logs only.")
            print()
        
        # STEP 4: Show final mitigations
        mitigations = result.get("mitigations", [])
        
        print("┌" + "─" * 78 + "┐")
        print("│ STEP 4: FINAL MITIGATIONS" + " " * 50 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        print(f"  ⚡ Analysis Time: {result.get('latency', 0):.2f} seconds")
        print(f"  🎯 Mitigations Identified: {len(mitigations)}")
        print()
        
        if mitigations:
            print("  Mitigation Actions Required:")
            print()
            for i, m in enumerate(mitigations, 1):
                entity_type = m.get('entity_type', 'unknown')
                entity = m.get('entity', 'unknown')
                severity = m.get('severity', 'unknown')
                mitigation = m.get('mitigation', 'unknown')
                reason = m.get('reason', 'No reason provided')
                
                # Color code severity
                severity_icon = {
                    'low': '🟢',
                    'medium': '🟡',
                    'high': '🟠',
                    'critical': '🔴'
                }.get(severity.lower(), '⚪')
                
                print(f"    {i}. {severity_icon} Entity: {entity_type.upper()} {entity}")
                print(f"       ├─ Severity: {severity.upper()}")
                print(f"       ├─ Action: {mitigation.upper()}")
                print(f"       └─ Reason: {reason}")
                print()
        else:
            print("  ✅ No threats detected - all traffic appears legitimate")
            print()
        
        # Summary
        print("=" * 80)
        print(" " * 30 + "📊 TEST SUMMARY")
        print("=" * 80)
        print()
        print(f"  ✓ Initial Batch Size:     {result['original_batch_size']} logs")
        print(f"  ✓ Tool Called:            {'YES' if tool_called else 'NO'}")
        if tool_called:
            print(f"  ✓ ES Logs Retrieved:      {len(additional_logs)} logs")
            print(f"  ✓ Total Analyzed:         {result['extended_batch_size']} logs")
        print(f"  ✓ Mitigations Generated:  {len(mitigations)}")
        print(f"  ✓ Processing Time:        {result.get('latency', 0):.2f}s")
        print()
        print("=" * 80)
        print()
        
        return mitigations
        
    except Exception as e:
        print(f"\n  ❌ Test failed with error: {e}")
        import traceback
        print()
        traceback.print_exc()
        return []


def run_tool_calling_test():
    """Wrapper to run the async tool calling test."""
    import asyncio
    asyncio.run(test_tool_calling())


async def test_calibration_workflow():
    """
    Test the complete calibration workflow with RAG.
    
    Shows the full pipeline:
    1. General Agent detects threats → sends to Calibration Agent
    2. Calibration Agent queries ChromaDB for similar cases
    3. Analyzes effectiveness and calibrates mitigation (amplify/downgrade)
    4. Saves to ChromaDB for future RAG
    5. Applies to Redis for middleware enforcement
    """
    import sys
    import os
    import logging
    import json
    
    # Add the agents directory to the path
    agents_dir = os.path.join(os.path.dirname(__file__), "agents")
    if agents_dir not in sys.path:
        sys.path.insert(0, agents_dir)
    
    from models import Mitigation, MitigationBatch
    from calibration_agent import (
        query_chromadb, calibrate_with_rag, save_to_chromadb, apply_to_redis
    )
    
    # Create a mock context with a logger
    class MockContext:
        def __init__(self):
            self.logger = logging.getLogger("calibration_test")
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('    %(message)s'))
            self.logger.addHandler(handler)
    
    ctx = MockContext()
    
    print("\n" + "=" * 80)
    print(" " * 20 + "🎯 CALIBRATION WORKFLOW TEST")
    print("=" * 80)
    print()
    
    # Simulate mitigations from General Agent
    test_mitigations = [
        Mitigation(
            entity_type="ip",
            entity="10.0.0.50",
            severity="high",
            mitigation="temp_block",
            reason="Endpoint enumeration detected across 15+ admin endpoints",
            source_agent="general"
        ),
        Mitigation(
            entity_type="ip",
            entity="203.0.113.42",
            severity="medium",
            mitigation="delay",
            reason="High frequency requests to status endpoint (50+ in short time)",
            source_agent="general"
        )
    ]
    
    print("┌" + "─" * 78 + "┐")
    print("│ SIMULATED INPUT FROM GENERAL AGENT" + " " * 43 + "│")
    print("└" + "─" * 78 + "┘")
    print()
    print(f"  📨 Received {len(test_mitigations)} mitigations from specialist agent:")
    print()
    
    for i, mitigation in enumerate(test_mitigations, 1):
        print(f"  {i}. Entity: {mitigation.entity_type.upper()} {mitigation.entity}")
        print(f"     Severity: {mitigation.severity.upper()}")
        print(f"     Mitigation: {mitigation.mitigation.upper()}")
        print(f"     Reason: {mitigation.reason}")
        print()
    
    # Process each mitigation through the calibration workflow
    for mitigation_num, mitigation in enumerate(test_mitigations, 1):
        print("\n" + "=" * 80)
        print(f" " * 25 + f"PROCESSING MITIGATION {mitigation_num}/{len(test_mitigations)}")
        print("=" * 80)
        print()
        
        # STEP 1: Query ChromaDB
        print("┌" + "─" * 78 + "┐")
        print("│ STEP 1: QUERY CHROMADB FOR SIMILAR CASES (RAG)" + " " * 32 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        print(f"  🔍 Querying historical data for similar cases...")
        print(f"  📊 Search criteria:")
        print(f"     - Reason: \"{mitigation.reason}\"")
        print(f"     - Entity: {mitigation.entity}")
        print()
        
        similar_cases = await query_chromadb(ctx, mitigation.reason, mitigation.entity)
        
        if similar_cases:
            print(f"  ✅ Found {len(similar_cases)} similar past cases:")
            print()
            for i, case in enumerate(similar_cases, 1):
                effectiveness = case.get('effectiveness', 0) or 0
                eff_icon = "🟢" if effectiveness >= 70 else "🟡" if effectiveness >= 50 else "🔴"
                print(f"    {i}. {eff_icon} Case ID: {case.get('id', 'unknown')[:8]}...")
                print(f"       Entity: {case.get('entity_type')} {case.get('entity')}")
                print(f"       Mitigation: {case.get('mitigation')} (Severity: {case.get('severity')})")
                print(f"       Result: {case.get('result', 'pending')}")
                print(f"       Effectiveness: {effectiveness}%")
                print(f"       Reason: {case.get('reason', 'N/A')[:60]}...")
                print()
        else:
            print(f"  ℹ️  No similar cases found - this is a first-time scenario")
            print()
        
        # STEP 2: Calibrate with RAG
        print("┌" + "─" * 78 + "┐")
        print("│ STEP 2: ANALYZE & CALIBRATE MITIGATION" + " " * 38 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        print(f"  ⚖️  Analyzing historical effectiveness...")
        print()
        
        calibrated_mitigation, reasoning = await calibrate_with_rag(ctx, mitigation, similar_cases)
        
        decision_icon = {
            "AMPLIFY": "⬆️",
            "DOWNGRADE": "⬇️",
            "KEEP_ORIGINAL": "➡️"
        }.get(reasoning["decision"], "❓")
        
        print(f"  {decision_icon} DECISION: {reasoning['decision']}")
        print(f"  📊 Confidence: {reasoning['confidence'].upper()}")
        if reasoning.get("cases_analyzed"):
            print(f"  📈 Cases Analyzed: {reasoning['cases_analyzed']}")
            print(f"  📈 Average Effectiveness: {reasoning['avg_effectiveness']}%")
        print()
        print(f"  💭 Reasoning:")
        print(f"     {reasoning['reasoning']}")
        print()
        print(f"  📋 Calibration Result:")
        print(f"     Original:   {mitigation.severity.upper():10s} → {mitigation.mitigation.upper()}")
        print(f"     Calibrated: {calibrated_mitigation.severity.upper():10s} → {calibrated_mitigation.mitigation.upper()}")
        print()
        
        # STEP 3: Save to ChromaDB
        print("┌" + "─" * 78 + "┐")
        print("│ STEP 3: SAVE TO CHROMADB (CREATE MEMORY)" + " " * 36 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        print(f"  💾 Saving calibrated mitigation for future RAG queries...")
        
        await save_to_chromadb(ctx, calibrated_mitigation, reasoning)
        
        print(f"  ✅ Saved to ChromaDB")
        print(f"  📝 This will be used for future similar cases")
        print()
        
        # STEP 4: Apply to Redis
        print("┌" + "─" * 78 + "┐")
        print("│ STEP 4: APPLY TO REDIS (MIDDLEWARE ENFORCEMENT)" + " " * 28 + "│")
        print("└" + "─" * 78 + "┘")
        print()
        print(f"  🔧 Applying mitigation to Redis...")
        
        await apply_to_redis(ctx, calibrated_mitigation)
        
        # Map severity to description
        severity_descriptions = {
            "low": "Small delay (100-500ms)",
            "medium": "CAPTCHA challenge required",
            "high": "Temporary block (15-60 min)",
            "critical": "Permanent ban"
        }
        
        print(f"  ✅ Applied to Redis")
        print(f"  🛡️  Middleware will now enforce:")
        print(f"     Action: {severity_descriptions.get(calibrated_mitigation.severity, 'Unknown')}")
        print(f"     Target: {calibrated_mitigation.entity_type} {calibrated_mitigation.entity}")
        print(f"     Duration: 1 hour TTL")
        print()
    
    # Summary
    print("=" * 80)
    print(" " * 30 + "📊 WORKFLOW SUMMARY")
    print("=" * 80)
    print()
    print(f"  ✅ Mitigations Processed: {len(test_mitigations)}")
    print(f"  ✅ ChromaDB Queries: {len(test_mitigations)}")
    print(f"  ✅ Mitigations Saved: {len(test_mitigations)}")
    print(f"  ✅ Redis Updates: {len(test_mitigations)}")
    print()
    print("  🎯 Complete Workflow Executed:")
    print("     1. ✅ Received mitigations from specialist agent")
    print("     2. ✅ Queried ChromaDB for historical data (RAG)")
    print("     3. ✅ Analyzed effectiveness and calibrated")
    print("     4. ✅ Saved to ChromaDB for future learning")
    print("     5. ✅ Applied to Redis for middleware enforcement")
    print()
    print("=" * 80)
    print()
    
    # Show ChromaDB contents
    print("┌" + "─" * 78 + "┐")
    print("│ CHROMADB CONTENTS (MEMORY FOR FUTURE RAG)" + " " * 34 + "│")
    print("└" + "─" * 78 + "┘")
    print()
    
    from pathlib import Path
    chromadb_path = Path(__file__).parent / "data" / "chromadb_simulation.json"
    
    if chromadb_path.exists():
        with open(chromadb_path, 'r') as f:
            data = json.load(f)
            total = len(data.get("mitigations", []))
            print(f"  📚 Total Entries in ChromaDB: {total}")
            print()
            if total > 0:
                print(f"  Recent entries (last 5):")
                for i, entry in enumerate(data["mitigations"][-5:], 1):
                    print(f"    {i}. ID: {entry['id'][:8]}... | Entity: {entry['entity']} | {entry['mitigation']}")
    else:
        print(f"  ℹ️  ChromaDB file not found (will be created on first run)")
    
    print()
    print("=" * 80)
    print()


def run_calibration_test():
    """Wrapper to run the async calibration test."""
    import asyncio
    asyncio.run(test_calibration_workflow())


if __name__ == "__main__":
    import sys
    
    # Check if running in test mode
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-tool-calling":
            run_tool_calling_test()
        elif sys.argv[1] == "--test-calibration":
            run_calibration_test()
        else:
            print("Unknown test mode. Available options:")
            print("  --test-tool-calling   Test General Agent tool calling with Elasticsearch")
            print("  --test-calibration    Test Calibration Agent workflow with RAG")
    else:
        main()