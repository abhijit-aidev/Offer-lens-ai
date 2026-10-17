#!/usr/bin/env python3
"""
Seed and verify OfferLens AI data in Neo4j.
Runs real Cypher queries to seed Offers A, B, and C, and verifies graph connectivity.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import Neo4jConfig
from src.db import Neo4jConnection
from src.repository import OfferRepository


def main():
    print("=" * 60)
    print(" OfferLens AI - Neo4j Seed & Graph Discovery Verifier")
    print("=" * 60)

    uri = Neo4jConfig.get_uri()
    user = Neo4jConfig.get_username()
    database = Neo4jConfig.get_database()

    print(f"[*] Target Neo4j URI:      {uri}")
    print(f"[*] Target Neo4j User:     {user}")
    print(f"[*] Target Neo4j Database: {database}\n")

    print("[1/4] Testing connection to Neo4j...")
    connected, message = Neo4jConnection.test_connection()
    if not connected:
        print(f"[!] FAILED: {message}\n")
        print("To connect Neo4j:")
        print("  Option A (Recommended for Hackathons):")
        print("    1. Create a free Neo4j AuraDB cloud database at: https://neo4j.com/cloud/platform/aura-graph-database/")
        print("    2. Copy your URI, Username, and Password into your .env file.")
        print("  Option B (Local):")
        print("    1. Start Neo4j locally: neo4j console (or brew services start neo4j)")
        print("    2. Update .env with bolt://localhost:7687 and your credentials.")
        sys.exit(1)

    print(f"[+] SUCCESS: {message}\n")

    driver = Neo4jConnection.get_driver()
    repo = OfferRepository(driver=driver, database=database)

    print("[2/4] Initializing Schema & Constraints...")
    repo.init_schema()
    print("[+] Uniqueness constraints applied.\n")

    print("[3/4] Seeding the 3 Fictional Offers...")
    repo.clear_database()
    seeded = repo.seed_initial_offers()
    for o in seeded:
        contacts_str = ", ".join(c.email for c in o.contacts)
        print(f"  - [{o.id}] {o.company.name} | Domain: {o.company.domain} | Contact: {contacts_str}")
    print("[+] 3 offers successfully seeded into Neo4j graph.\n")

    print("[4/4] Verifying Real Graph Connections via Cypher Queries...")
    
    # Test Offer A
    conn_a = repo.find_related_offers("OFFER-A")
    print(f"\n-> Checking connections for OFFER-A (NovaEdge Technologies):")
    if conn_a:
        for c in conn_a:
            print(f"   [LINK DETECTED] Connected to {c.target_offer_id} ({c.target_company_name})")
            print(f"     Reason: {c.connection_type} ({c.shared_value})")
            print(f"     Details: {c.explanation}")
    else:
        print("   [!] No connections found!")

    # Test Offer B
    conn_b = repo.find_related_offers("OFFER-B")
    print(f"\n-> Checking connections for OFFER-B (BrightPath AI):")
    if conn_b:
        for c in conn_b:
            print(f"   [LINK DETECTED] Connected to {c.target_offer_id} ({c.target_company_name})")
            print(f"     Reason: {c.connection_type} ({c.shared_value})")
    else:
        print("   [!] No connections found!")

    # Test Offer C
    conn_c = repo.find_related_offers("OFFER-C")
    print(f"\n-> Checking connections for OFFER-C (Summit Digital):")
    if conn_c:
        print(f"   [!] UNEXPECTED: OFFER-C found connections: {conn_c}")
    else:
        print("   [ISOLATED] Confirmed 0 connections. Offer C remains completely unrelated.")

    # Validation checks
    assert any(c.target_offer_id == "OFFER-B" for c in conn_a), "OFFER-A must connect to OFFER-B"
    assert any(c.target_offer_id == "OFFER-A" for c in conn_b), "OFFER-B must connect to OFFER-A"
    assert len(conn_c) == 0, "OFFER-C must have 0 connections"

    print("\n" + "=" * 60)
    print(" VERIFICATION PASSED: Real Neo4j graph queries verified!")
    print("=" * 60)


if __name__ == "__main__":
    main()
