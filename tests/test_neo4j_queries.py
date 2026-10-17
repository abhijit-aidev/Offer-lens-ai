"""
Integration tests for Neo4j queries in OfferLens AI.
Tests real Neo4j queries if an active Neo4j database is reachable.
"""

import pytest
from src.db import Neo4jConnection
from src.config import Neo4jConfig
from src.repository import OfferRepository
from src.models import JobOffer, Company, ContactPerson


# Check if Neo4j is online before running live graph tests
connected, conn_msg = Neo4jConnection.test_connection()


@pytest.mark.skipif(not connected, reason=f"Neo4j database offline: {conn_msg}")
def test_real_neo4j_graph_connectivity():
    """
    Live Neo4j graph test verifying that:
    - Offer A and Offer B connect through recruit-a@example.test
    - Offer C remains isolated through seeded identifiers
    """
    driver = Neo4jConnection.get_driver()
    repo = OfferRepository(driver, database=Neo4jConfig.get_database())

    # 1. Clean slate
    repo.clear_database()

    # 2. Seed Offers A, B, C
    repo.seed_initial_offers()

    # 3. Test Offer A connections
    conn_a = repo.find_related_offers("OFFER-A")
    assert len(conn_a) >= 1, "OFFER-A should discover related offers"
    target_ids_a = [c.target_offer_id for c in conn_a]
    assert "OFFER-B" in target_ids_a, "OFFER-A should connect to OFFER-B"
    assert "OFFER-C" not in target_ids_a, "OFFER-A should NOT connect to OFFER-C"

    # Verify connection detail
    b_match = next(c for c in conn_a if c.target_offer_id == "OFFER-B")
    assert b_match.connection_type == "SHARED_CONTACT"
    assert b_match.shared_value == "recruit-a@example.test"

    # 4. Test Offer B connections
    conn_b = repo.find_related_offers("OFFER-B")
    target_ids_b = [c.target_offer_id for c in conn_b]
    assert "OFFER-A" in target_ids_b, "OFFER-B should connect to OFFER-A"
    assert "OFFER-C" not in target_ids_b, "OFFER-B should NOT connect to OFFER-C"

    # 5. Test Offer C connections
    conn_c = repo.find_related_offers("OFFER-C")
    assert len(conn_c) == 0, "OFFER-C must remain completely isolated from A and B"


def test_repository_models():
    """Verify repository data structures and query parameter formatting without database."""
    offer = JobOffer(
        id="OFFER-TEST",
        title="Software Engineer",
        company=Company(name="Test Corp", domain="test.org"),
        contacts=[ContactPerson(email="test@test.org")],
    )
    assert offer.company.name == "Test Corp"
    assert offer.contacts[0].email == "test@test.org"
