#!/usr/bin/env python3
"""
Test the security incident RAG pipeline with CSV-style data.
"""

import asyncio
from simple_rag import add_incident_from_csv, query_similar_items, get_all_flagged_items, get_rag_stats, clear_all_incidents

async def test_security_incidents():
    """Test with security incidents in CSV format."""
    print("🚀 Testing Security Incident RAG")
    print("=" * 50)
    
    # Clear existing data for clean test
    print("🧹 Clearing existing data...")
    await clear_all_incidents()
    
    # Add incidents from your CSV format
    incidents = [
        ("user_001", "192.168.1.24", 5, "User attempted to log into the admin account over 5000 times within 30 seconds, suggesting automated brute-force behavior."),
        ("guest_user", "10.0.0.55", 4, "Repeated login attempts with invalid credentials across multiple endpoints. Possible credential stuffing detected."),
        ("api_tester_23", "172.16.5.101", 2, "Excessive GET requests to documentation routes without modification attempts. Likely an automated scanner or load tester."),
        ("john_doe", "203.0.113.12", 3, "User accessed multiple unrelated API routes with random query parameters. Indicative of exploratory probing behavior."),
        ("anonymous", "8.8.8.8", 5, "Multiple failed attempts to escalate privileges combined with SQL injection-like payloads in POST requests."),
        ("dev_admin", "45.76.91.32", 1, "Legitimate internal admin access with slightly unusual frequency. Requires monitoring but not immediate mitigation."),
        ("temp_user_91", "192.0.2.77", 4, "Detected pattern of sequential login attempts across 200 usernames from the same IP within one minute. Likely brute-force bot."),
        ("bot_user_404", "198.51.100.23", 5, "Requests contained known malicious headers and User-Agent spoofing patterns typical of automated attack tools."),
        ("service_user_12", "203.0.113.45", 3, "Burst of 400 requests to mixed endpoints with inconsistent headers, indicative of scripted probing."),
        ("qa_bot_v2", "198.51.100.77", 2, "Periodic OPTIONS and HEAD requests across all routes at fixed intervals, likely an automated monitor."),
        ("suspicious_cli", "192.0.2.101", 4, "High-frequency login attempts alternating between two usernames, consistent with password spraying."),
        ("crawler_x", "203.0.113.88", 3, "Sequential traversal of resource IDs without authentication, indicative of IDOR probing."),
        ("unknown_mobile", "10.10.10.10", 2, "Short spike of GET requests with mobile UA but desktop-only paths, likely device spoofing test."),
        ("temp_admin_probe", "172.16.8.45", 5, "POST payloads include base64-encoded SQL fragments attempting UNION SELECT injection."),
        ("legacy_script", "198.51.100.200", 1, "Consistent low-rate traffic to deprecated endpoints, likely a leftover cron job."),
        ("anon_777", "8.8.4.4", 4, "Rapid 429 responses followed by retries with varying query params, attempting rate-limit evasion."),
        ("trial_user_x", "203.0.113.129", 3, "GraphQL introspection attempts followed by unusual nested queries targeting admin fields."),
        ("headless_scan", "192.0.2.210", 4, "Headless browser signatures with randomized accept-language headers probing auth flows."),
        ("cloud_func_01", "35.201.10.5", 2, "Burst from cloud provider IPs fetching doc and health routes; moderate suspicion."),
        ("toolkit_sig", "52.11.24.36", 5, "Known malicious toolkit headers detected; sequence matches past credential stuffing wave."),
        ("lab_machine", "10.3.2.9", 1, "Internal subnet host performing legitimate performance tests at agreed window."),
        ("partner_api_key", "203.0.113.230", 3, "Partner token used outside normal time window with higher-than-average error rates."),
        ("free_proxy_user", "103.21.244.0", 4, "Requests from public proxy ranges rotating every minute, targeting auth and profile endpoints."),
        ("automation_hint", "198.18.0.45", 2, "Uniform inter-request timing at 500ms suggests scripted client; low variance payloads."),
        ("enum_attempt", "203.0.113.15", 4, "Username enumeration via timing differences on password reset endpoint."),
        ("payload_fuzzer", "192.0.2.66", 5, "Multipart form fields include fuzzing dictionaries and boundary anomalies characteristic of exploit tooling."),
        ("vpn_cluster", "89.160.20.112", 3, "Same session token observed across IPs in quick succession, likely VPN exit rotation."),
        ("edge_probe", "64.233.160.0", 2, "Edge network addresses performing cache-busting patterns; limited scope, moderate risk."),
            ]
    
    print("\n📝 Adding security incidents...")
    for user, ip, severity, reasoning in incidents:
        item_id = await add_incident_from_csv(user, ip, severity, reasoning)
        print(f"✅ Added: {user} ({ip}) - Severity {severity}")
    
    # Get stats
    stats = await get_rag_stats()
    print(f"\n📊 Total incidents: {stats['total_items']}")
    
    # Test semantic queries
    print("\n🔍 Testing semantic queries...")
    
    queries = [
        "brute force login attacks",
        "credential stuffing attempts", 
        "automated scanning behavior",
        "SQL injection attacks",
        "privilege escalation attempts",
        "User attempted to log into the admin account over 5000 times within 30 seconds, suggesting automated brute-force behavior."
        
    ]
    
    for query in queries:
        print(f"\n🔎 Query: '{query}'")
        results = await query_similar_items(query, k=3)
        
        for i, item in enumerate(results, 1):
            metadata = item['metadata']
            print(f"  {i}. Score: {item['score']:.3f} | Severity: {metadata.get('severity', 'unknown')}")
            print(f"     User: {metadata.get('user', 'unknown')} | IP: {metadata.get('ip', 'unknown')}")
            print(f"     Reasoning: {item['text'][:80]}...")
    
    # Show all incidents with metadata
    print(f"\n📋 All security incidents:")
    all_items = await get_all_flagged_items()
    for i, item in enumerate(all_items, 1):
        metadata = item['metadata']
        print(f"  {i}. {metadata.get('user', 'unknown')} ({metadata.get('ip', 'unknown')}) - Severity {metadata.get('severity', 'unknown')}")
        print(f"     Reasoning: {item['text'][:60]}...")
    
    print("\n✅ Security incident RAG test complete!")

if __name__ == "__main__":
    asyncio.run(test_security_incidents())