"""
Tests for OfferLens AI Investigation & Risk Analyzer.
Validates explainable risk signals, Connection Evidence generation,
upfront payment/urgency detection, and database-unavailable handling.
"""

from src.models import JobOffer, Company, ContactPerson, GraphConnection
from src.analyzer import (
    evaluate_risk_signals,
    build_connection_evidence,
    get_confirmed_vs_unknown,
    get_verification_steps,
)


def test_shared_contact_risk_signal():
    offer_a = JobOffer(
        id="OFFER-A",
        title="Senior Software Engineer",
        company=Company(name="NovaEdge Technologies", domain="novaedge-example.com"),
        contacts=[ContactPerson(email="recruit-a@example.test")],
    )

    conn = GraphConnection(
        source_offer_id="OFFER-A",
        target_offer_id="OFFER-B",
        target_company_name="BrightPath AI",
        connection_type="SHARED_CONTACT",
        shared_value="recruit-a@example.test",
        explanation="Offers share contact recruit-a@example.test",
    )

    signals = evaluate_risk_signals(offer_a, [conn], is_connected=True)
    high_signals = [s for s in signals if s["level"] == "HIGH"]
    assert len(high_signals) == 1
    assert "Recruiter Contact Associated With Multiple Companies" in high_signals[0]["title"]
    assert "BrightPath AI" in high_signals[0]["reason"]


def test_connection_evidence_generation():
    """Verify detailed connection evidence structure for hackathon judges."""
    offer_a = JobOffer(
        id="OFFER-A",
        title="Senior Backend Engineer",
        company=Company(name="NovaEdge Technologies", domain="novaedge-example.com"),
        contacts=[ContactPerson(email="recruit-a@example.test")],
    )

    conn = GraphConnection(
        source_offer_id="OFFER-A",
        target_offer_id="OFFER-B",
        target_company_name="BrightPath AI",
        connection_type="SHARED_CONTACT",
        shared_value="recruit-a@example.test",
        explanation="Offers share contact recruit-a@example.test",
    )

    evidence = build_connection_evidence(offer_a, conn)
    assert evidence["source_offer_id"] == "OFFER-A"
    assert evidence["source_company"] == "NovaEdge Technologies"
    assert evidence["target_offer_id"] == "OFFER-B"
    assert evidence["target_company"] == "BrightPath AI"
    assert evidence["shared_identifier"] == "recruit-a@example.test"
    assert "why_it_matters" in evidence
    assert "what_it_does_not_prove" in evidence
    # Ensure it emphasizes non-defamatory phrasing
    assert "NOT prove fraudulent intent" in evidence["what_it_does_not_prove"]
    assert len(evidence["verification_steps"]) > 0


def test_upfront_payment_risk_signal():
    """Verify detection of advance fee and equipment check fraud patterns."""
    offer = JobOffer(
        id="OFFER-PAY",
        title="Virtual Assistant",
        company=Company(name="Shady LLC"),
        raw_text="We will mail you a check advance to purchase equipment via wire transfer or bitcoin.",
    )
    signals = evaluate_risk_signals(offer, [], is_connected=True)
    pay_signals = [s for s in signals if s["category"] == "Upfront Payment Request"]
    assert len(pay_signals) >= 1
    assert pay_signals[0]["level"] == "HIGH"


def test_urgency_pressure_risk_signal():
    """Verify detection of artificial urgency and pressure tactics."""
    offer = JobOffer(
        id="OFFER-URGENT",
        title="Data Entry",
        company=Company(name="Fast Hire Inc"),
        raw_text="Immediate hire without interview! You must act fast within 24 hours to secure your spot.",
    )
    signals = evaluate_risk_signals(offer, [], is_connected=True)
    urgency_signals = [s for s in signals if s["category"] == "Urgency & Pressure Tactics"]
    assert len(urgency_signals) >= 1
    assert urgency_signals[0]["level"] == "MEDIUM"


def test_public_email_risk_signal():
    offer = JobOffer(
        id="OFFER-X",
        title="Frontend Developer",
        company=Company(name="Alpha Corp", domain="alphacorp.com"),
        contacts=[ContactPerson(email="recruiter@gmail.com")],
    )
    signals = evaluate_risk_signals(offer, [], is_connected=True)
    med_signals = [s for s in signals if s["level"] == "MEDIUM"]
    assert any("Public / Generic Email Provider" in s["title"] for s in med_signals)


def test_confirmed_vs_unknown_separation():
    offer = JobOffer(
        id="OFFER-C",
        title="Full Stack Developer",
        company=Company(name="Summit Digital", domain="summit-example.com"),
        contacts=[ContactPerson(email="jobs@summit-example.com")],
    )
    breakdown = get_confirmed_vs_unknown(offer, [], is_connected=True)
    assert len(breakdown["confirmed"]) > 0
    assert len(breakdown["unknown"]) > 0
    assert any("Summit Digital" in c for c in breakdown["confirmed"])
    # Ensure operational unknowns are explicitly present
    assert any("Legal entity status unverified" in u for u in breakdown["unknown"])


def test_database_offline_handling_in_analyzer():
    """Verify that when Neo4j is offline, analyzer gracefully handles absence of graph links."""
    offer = JobOffer(
        id="OFFER-OFFLINE",
        title="Security Analyst",
        company=Company(name="Secure Net", domain="securenet.org"),
        contacts=[ContactPerson(email="hr@securenet.org")],
    )
    breakdown = get_confirmed_vs_unknown(offer, [], is_connected=False)
    assert any("Neo4j database is offline" in u for u in breakdown["unknown"])
    # No fake connections should be present
    signals = evaluate_risk_signals(offer, [], is_connected=False)
    assert not any(s["category"] == "Cross-Company Recruiter Overlap" for s in signals)
