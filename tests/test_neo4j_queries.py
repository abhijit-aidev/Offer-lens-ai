"""
Integration & Unit tests for Neo4j queries in OfferLens AI.
Clearly distinguishes offline unit tests from live database integration tests.
"""

import pytest
from src.db import Neo4jConnection
from src.config import Neo4jConfig
from src.repository import (
    OfferRepository,
    CYPHER_CREATE_CONSTRAINTS,
    CYPHER_INSERT_OFFER,
    CYPHER_FIND_BY_SHARED_CONTACT,
    CYPHER_FIND_BY_SHARED_DOMAIN,
    CYPHER_FIND_BY_CONTACT_EMAILS,
    CYPHER_FIND_BY_DOMAINS,
)
from src.models import JobOffer, Company, ContactPerson


# Check if Neo4j is online before running live graph tests
connected, conn_msg = Neo4jConnection.test_connection()


# ----------------------------------------------------------------------
# LIVE INTEGRATION TESTS (Run only if active Neo4j cluster is reachable)
# ----------------------------------------------------------------------

@pytest.mark.skipif(not connected, reason=f"Live Neo4j database offline: {conn_msg}")
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


# ----------------------------------------------------------------------
# OFFLINE UNIT TESTS (Never require a running database server)
# ----------------------------------------------------------------------

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


def test_offline_connection_diagnostics():
    """Verify connection diagnostic function safely handles an unreachable host without crashing."""
    diag = Neo4jConnection.get_diagnostics("bolt://localhost:9999", "neo4j", "dummy")
    assert diag["connected"] is False
    assert "target_uri" in diag
    assert "bolt://localhost:9999" == diag["target_uri"]
    assert "message" in diag
    assert len(diag["message"]) > 0


def test_cypher_schema_consistency():
    """
    Verify all Cypher query constants strictly conform to the unified graph schema:
    - Node labels: Offer, Company, Domain, ContactPerson
    - Relationships: OFFERED_BY, USES_DOMAIN, HAS_CONTACT
    - Parameterization: Uses $parameters rather than raw string interpolation
    """
    # Verify label consistency in schema constraints
    constraints_str = " ".join(CYPHER_CREATE_CONSTRAINTS)
    assert ":Offer" in constraints_str
    assert ":Company" in constraints_str
    assert ":Domain" in constraints_str
    assert ":ContactPerson" in constraints_str

    # Verify relationships in insertion query
    assert "OFFERED_BY" in CYPHER_INSERT_OFFER
    assert "USES_DOMAIN" in CYPHER_INSERT_OFFER
    assert "HAS_CONTACT" in CYPHER_INSERT_OFFER

    # Verify parameterization (prevents Cypher injection)
    assert "$offer_id" in CYPHER_FIND_BY_SHARED_CONTACT
    assert "$offer_id" in CYPHER_FIND_BY_SHARED_DOMAIN
    assert "$emails" in CYPHER_FIND_BY_CONTACT_EMAILS
    assert "$domains" in CYPHER_FIND_BY_DOMAINS
