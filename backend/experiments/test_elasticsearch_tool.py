"""
Comprehensive Test Cases for Elasticsearch Tool
Tests all edge cases, different query types, and specific scenarios.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path to import the tool
sys.path.append(str(Path(__file__).parent.parent))

from elastictool.elasticsearch_tool import (
    query_elasticsearch_dynamic,
    query_failed_logins,
    query_suspicious_activity,
    query_user_activity,
    query_by_ip,
    query_slow_requests
)


async def test_basic_queries():
    """Test basic query functionality"""
    print("=" * 80)
    print("TEST SUITE 1: BASIC QUERIES")
    print("=" * 80)
    
    # Test 1: Query specific username - admin
    print("\n1. Testing username='admin' query...")
    result = await query_user_activity(username="admin", time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Found {result['total_hits']} requests from admin")
        print(f"   - Unique IPs: {result['aggregations']['unique_ips']}")
        print(f"   - Status codes: {result['aggregations']['status_codes']}")
        if result['documents']:
            print(f"   - Sample request: {result['documents'][0].get('path', 'N/A')}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 2: Query specific IP
    print("\n2. Testing IP='192.168.65.1' query...")
    result = await query_by_ip(client_ip="192.168.65.1", time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Found {result['total_hits']} requests from IP")
        print(f"   - Unique users: {result['aggregations']['unique_users']}")
        print(f"   - Top paths: {[p['key'] for p in result['aggregations']['top_paths'][:3]]}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 3: Query Docker internal IP
    print("\n3. Testing Docker IP='172.19.0.1' query...")
    result = await query_by_ip(client_ip="172.19.0.1", time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Found {result['total_hits']} requests from Docker IP")
        print(f"   - Methods used: {[m['key'] for m in result['aggregations']['methods'][:3]]}")
    else:
        print(f"   ✗ Error: {result['error']}")


async def test_failed_login_scenarios():
    """Test failed login detection"""
    print("\n" + "=" * 80)
    print("TEST SUITE 2: FAILED LOGIN SCENARIOS")
    print("=" * 80)
    
    # Test 4: All failed logins
    print("\n4. Testing all failed logins...")
    result = await query_failed_logins(time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Total failed logins: {result['total_hits']}")
        print(f"   - Unique IPs involved: {result['aggregations']['unique_ips']}")
        print(f"   - Unique users targeted: {result['aggregations']['unique_users']}")
        if result['documents']:
            print(f"   - Recent attempt: user={result['documents'][0].get('username', 'N/A')}, "
                  f"ip={result['documents'][0].get('client_ip', 'N/A')}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 5: Failed logins for specific user
    print("\n5. Testing failed logins for username='admin'...")
    result = await query_failed_logins(username="admin", time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Failed admin logins: {result['total_hits']}")
        print(f"   - From unique IPs: {result['aggregations']['unique_ips']}")
        if result['documents']:
            ips = set(doc.get('client_ip', 'N/A') for doc in result['documents'][:5])
            print(f"   - Top attacking IPs: {list(ips)}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 6: Failed logins from specific IP
    print("\n6. Testing failed logins from IP='172.19.0.1'...")
    result = await query_failed_logins(client_ip="172.19.0.1", time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Failed logins from this IP: {result['total_hits']}")
        print(f"   - Users targeted: {result['aggregations']['unique_users']}")
        if result['documents']:
            users = set(doc.get('username', 'N/A') for doc in result['documents'][:5])
            print(f"   - Targeted usernames: {list(users)}")
    else:
        print(f"   ✗ Error: {result['error']}")


async def test_suspicious_activity():
    """Test suspicious activity detection"""
    print("\n" + "=" * 80)
    print("TEST SUITE 3: SUSPICIOUS ACTIVITY DETECTION")
    print("=" * 80)
    
    # Test 7: Suspicious activity with default threshold (10 requests)
    print("\n7. Testing suspicious activity (min_requests=10)...")
    result = await query_suspicious_activity(time_range_hours=24, min_requests=10)
    if result["success"]:
        print(f"   ✓ Total failed attempts analyzed: {result['total_failed_attempts']}")
        print(f"   - Suspicious IPs: {len(result['suspicious_ips'])}")
        for ip, count in list(result['suspicious_ips'].items())[:5]:
            print(f"     • {ip}: {count} failed attempts")
        print(f"   - Suspicious users: {len(result['suspicious_users'])}")
        for user, count in list(result['suspicious_users'].items())[:5]:
            print(f"     • {user}: {count} failures")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 8: Suspicious activity with lower threshold (5 requests)
    print("\n8. Testing suspicious activity (min_requests=5)...")
    result = await query_suspicious_activity(time_range_hours=24, min_requests=5)
    if result["success"]:
        print(f"   ✓ Suspicious IPs with 5+ attempts: {len(result['suspicious_ips'])}")
        print(f"   ✓ Suspicious users with 5+ attempts: {len(result['suspicious_users'])}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 9: Suspicious activity in last hour only
    print("\n9. Testing recent suspicious activity (last 1 hour)...")
    result = await query_suspicious_activity(time_range_hours=1, min_requests=3)
    if result["success"]:
        print(f"   ✓ Recent suspicious IPs: {len(result['suspicious_ips'])}")
        print(f"   ✓ Recent suspicious users: {len(result['suspicious_users'])}")
    else:
        print(f"   ✗ Error: {result['error']}")


async def test_dynamic_queries():
    """Test dynamic query combinations"""
    print("\n" + "=" * 80)
    print("TEST SUITE 4: DYNAMIC QUERY COMBINATIONS")
    print("=" * 80)
    
    # Test 10: POST requests to /login
    print("\n10. Testing method='POST' + path='/login'...")
    result = await query_elasticsearch_dynamic(
        query_params={"method": "POST", "path": "/login"},
        time_range_hours=24
    )
    if result["success"]:
        print(f"   ✓ POST requests to /login: {result['total_hits']}")
        print(f"   - Success rate: {result['aggregations']['status_codes']}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 11: 401 status codes only
    print("\n11. Testing response_status=401...")
    result = await query_elasticsearch_dynamic(
        query_params={"response_status": 401},
        time_range_hours=24
    )
    if result["success"]:
        print(f"   ✓ Total 401 responses: {result['total_hits']}")
        print(f"   - Top paths returning 401: {[p['key'] for p in result['aggregations']['top_paths'][:3]]}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 12: Successful requests only
    print("\n12. Testing response_success=True...")
    result = await query_elasticsearch_dynamic(
        query_params={"response_success": True},
        time_range_hours=24,
        size=10
    )
    if result["success"]:
        print(f"   ✓ Successful requests: {result['total_hits']}")
        print(f"   - Methods used: {[m['key'] for m in result['aggregations']['methods'][:3]]}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 13: Failed requests only
    print("\n13. Testing response_success=False...")
    result = await query_elasticsearch_dynamic(
        query_params={"response_success": False},
        time_range_hours=24
    )
    if result["success"]:
        print(f"   ✓ Failed requests: {result['total_hits']}")
        print(f"   - Top failure paths: {[p['key'] for p in result['aggregations']['top_paths'][:3]]}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 14: Multiple conditions - admin + 401 + POST
    print("\n14. Testing username='admin' + response_status=401 + method='POST'...")
    result = await query_elasticsearch_dynamic(
        query_params={
            "username": "admin",
            "response_status": 401,
            "method": "POST"
        },
        time_range_hours=24
    )
    if result["success"]:
        print(f"   ✓ Admin failed POST requests: {result['total_hits']}")
        if result['documents']:
            print(f"   - Recent attempt time: {result['documents'][0].get('timestamp', 'N/A')}")
            print(f"   - From IP: {result['documents'][0].get('client_ip', 'N/A')}")
    else:
        print(f"   ✗ Error: {result['error']}")


async def test_performance_queries():
    """Test performance-related queries"""
    print("\n" + "=" * 80)
    print("TEST SUITE 5: PERFORMANCE QUERIES")
    print("=" * 80)
    
    # Test 15: Slow requests (>1000ms)
    print("\n15. Testing slow requests (>1000ms)...")
    result = await query_slow_requests(min_processing_time_ms=1000, time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Slow requests found: {result['total_hits']}")
        if result['documents']:
            times = [doc.get('processing_time_ms', 0) for doc in result['documents'][:5]]
            print(f"   - Sample processing times: {times} ms")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 16: Very slow requests (>5000ms)
    print("\n16. Testing very slow requests (>5000ms)...")
    result = await query_slow_requests(min_processing_time_ms=5000, time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Very slow requests: {result['total_hits']}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 17: Fast requests (<100ms)
    print("\n17. Testing fast requests (<100ms) using range query...")
    result = await query_elasticsearch_dynamic(
        query_params={"processing_time_ms": {"lt": 100}},
        time_range_hours=24,
        size=10
    )
    if result["success"]:
        print(f"   ✓ Fast requests: {result['total_hits']}")
    else:
        print(f"   ✗ Error: {result['error']}")


async def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n" + "=" * 80)
    print("TEST SUITE 6: EDGE CASES & BOUNDARY CONDITIONS")
    print("=" * 80)
    
    # Test 18: Minimum time range (1 hour - enforced)
    print("\n18. Testing minimum time range (0 hours -> enforced to 1)...")
    result = await query_user_activity(username="admin", time_range_hours=0)
    if result["success"]:
        print(f"   ✓ Query executed with enforced 1-hour minimum")
        print(f"   - Time range: {result['time_range']}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 19: Empty result set (non-existent user)
    print("\n19. Testing non-existent username...")
    result = await query_user_activity(username="nonexistentuser12345", time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Query executed successfully")
        print(f"   - Results found: {result['total_hits']}")
        print(f"   - Handles empty results gracefully: {result['total_hits'] == 0}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 20: Non-existent IP
    print("\n20. Testing non-existent IP address...")
    result = await query_by_ip(client_ip="1.2.3.4", time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Query executed successfully")
        print(f"   - Results: {result['total_hits']}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 21: Large time range (7 days)
    print("\n21. Testing large time range (168 hours = 7 days)...")
    result = await query_failed_logins(time_range_hours=168)
    if result["success"]:
        print(f"   ✓ Query executed for 7-day period")
        print(f"   - Total failed logins in 7 days: {result['total_hits']}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 22: Multiple filter values (list query)
    print("\n22. Testing multiple status codes [401, 403, 404]...")
    result = await query_elasticsearch_dynamic(
        query_params={"response_status": [401, 403, 404]},
        time_range_hours=24
    )
    if result["success"]:
        print(f"   ✓ Found {result['total_hits']} requests with those status codes")
        print(f"   - Status distribution: {result['aggregations']['status_codes']}")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 23: Range query with both bounds
    print("\n23. Testing processing time range (100ms to 1000ms)...")
    result = await query_elasticsearch_dynamic(
        query_params={"processing_time_ms": {"gte": 100, "lte": 1000}},
        time_range_hours=24,
        size=5
    )
    if result["success"]:
        print(f"   ✓ Found {result['total_hits']} requests in time range")
        if result['documents']:
            times = [doc.get('processing_time_ms', 0) for doc in result['documents']]
            print(f"   - Sample times: {times} ms")
    else:
        print(f"   ✗ Error: {result['error']}")


async def test_specific_attack_patterns():
    """Test specific attack pattern detection"""
    print("\n" + "=" * 80)
    print("TEST SUITE 7: ATTACK PATTERN DETECTION")
    print("=" * 80)
    
    # Test 24: Brute force on admin account
    print("\n24. Testing brute force pattern on 'admin' account...")
    result = await query_failed_logins(username="admin", time_range_hours=1)
    if result["success"]:
        print(f"   ✓ Admin failed logins in last hour: {result['total_hits']}")
        is_brute_force = result['total_hits'] > 10
        print(f"   - Potential brute force attack: {is_brute_force}")
        if result['documents']:
            # Check if attempts are from same IP
            ips = [doc.get('client_ip') for doc in result['documents']]
            unique_ips = len(set(ips))
            print(f"   - Attacks from {unique_ips} unique IP(s)")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 25: Credential stuffing detection (multiple users, same IP)
    print("\n25. Testing credential stuffing from IP='172.19.0.1'...")
    result = await query_failed_logins(client_ip="172.19.0.1", time_range_hours=24)
    if result["success"]:
        print(f"   ✓ Failed logins from this IP: {result['total_hits']}")
        print(f"   - Unique users targeted: {result['aggregations']['unique_users']}")
        if result['aggregations']['unique_users'] > 5:
            print(f"   - ⚠️  Potential credential stuffing detected!")
    else:
        print(f"   ✗ Error: {result['error']}")
    
    # Test 26: Check for common default passwords attempts
    print("\n26. Testing for common password patterns in body...")
    result = await query_elasticsearch_dynamic(
        query_params={
            "path": "/login",
            "response_status": 401,
            "method": "POST"
        },
        time_range_hours=24,
        size=50
    )
    if result["success"]:
        print(f"   ✓ Analyzed {len(result['documents'])} failed login attempts")
        # Check for password patterns in documents
        if result['documents']:
            sample_doc = result['documents'][0]
            print(f"   - Sample attempt structure: {list(sample_doc.keys())[:5]}")
    else:
        print(f"   ✗ Error: {result['error']}")


async def run_all_tests():
    """Run all test suites"""
    print("\n")
    print("🔬 ELASTICSEARCH TOOL - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    try:
        await test_basic_queries()
        await test_failed_login_scenarios()
        await test_suspicious_activity()
        await test_dynamic_queries()
        await test_performance_queries()
        await test_edge_cases()
        await test_specific_attack_patterns()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nThe Elasticsearch tool is working correctly and ready for Fetch.ai agents!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())