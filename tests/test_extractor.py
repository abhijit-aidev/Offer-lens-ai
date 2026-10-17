"""
Tests for rule-based extraction in OfferLens AI.
Validates entity extraction for ground-truth offers, input validation,
and handling of missing or malformed inputs.
"""

import pytest
from src.extractor import (
    extract_emails,
    extract_domains,
    extract_company_name,
    extract_job_title,
    extract_salary,
    parse_job_offer_from_text,
)


def test_offer_a_extraction():
    text = """
    Congratulations! NovaEdge Technologies is delighted to offer you the role of Senior Software Engineer.
    Visit our portal at novaedge-example.com.
    Your hiring manager is available at recruit-a@example.test.
    Compensation: $165,000 per year.
    """
    offer = parse_job_offer_from_text(text, offer_id="OFFER-A")
    assert offer.id == "OFFER-A"
    assert offer.company.name == "NovaEdge Technologies"
    assert "novaedge-example.com" in [offer.company.domain] or "novaedge-example.com" in extract_domains(text)
    assert any(c.email == "recruit-a@example.test" for c in offer.contacts)
    assert offer.salary == "$165,000 per year"


def test_offer_b_extraction():
    text = """
    From: recruit-a@example.test
    Subject: Formal Offer - BrightPath AI
    We are excited to welcome you to BrightPath AI (https://brightpath-example.com).
    Role: Machine Learning Engineer
    Base Salary: $180,000
    """
    offer = parse_job_offer_from_text(text, offer_id="OFFER-B")
    assert offer.id == "OFFER-B"
    assert "BrightPath AI" in offer.company.name
    assert any(c.email == "recruit-a@example.test" for c in offer.contacts)


def test_offer_c_extraction():
    text = """
    Company: Summit Digital
    Website: summit-example.com
    Contact recruiter: jobs@summit-example.com
    Role: Full Stack Developer
    """
    offer = parse_job_offer_from_text(text, offer_id="OFFER-C")
    assert offer.id == "OFFER-C"
    assert offer.company.name == "Summit Digital"
    assert any(c.email == "jobs@summit-example.com" for c in offer.contacts)
    # Ensure recruit-a@example.test is NOT in offer C
    assert not any(c.email == "recruit-a@example.test" for c in offer.contacts)


def test_shared_contact_detection_in_data():
    emails_a = extract_emails("Contact: recruit-a@example.test")
    emails_b = extract_emails("Contact: recruit-a@example.test")
    emails_c = extract_emails("Contact: jobs@summit-example.com")

    # A and B share contact
    shared_ab = set(emails_a).intersection(set(emails_b))
    assert "recruit-a@example.test" in shared_ab

    # C does not share contact with A or B
    shared_ac = set(emails_a).intersection(set(emails_c))
    assert len(shared_ac) == 0


def test_empty_and_whitespace_input():
    """Verify parser handles empty or whitespace-only inputs safely."""
    offer = parse_job_offer_from_text("   \n\t  ")
    assert offer.id.startswith("OFFER-")
    assert offer.company.name == "Unknown Company"
    assert offer.company.domain is None
    assert len(offer.contacts) == 0
    assert offer.salary is None


def test_missing_values_graceful_handling():
    """Verify text with minimal or missing fields creates valid models."""
    text = "Join us as a Junior Associate. We are starting next month."
    offer = parse_job_offer_from_text(text)
    assert offer.title is not None
    assert offer.salary is None
    assert offer.contacts == []
    assert offer.company.domain is None


def test_explicit_overrides_precedence():
    """Verify caller can provide explicit company or domain overrides."""
    text = "Contact: test@other.com"
    offer = parse_job_offer_from_text(
        text,
        offer_id="EXPLICIT-01",
        explicit_company="Custom Corp",
        explicit_domain="customcorp.io",
    )
    assert offer.id == "EXPLICIT-01"
    assert offer.company.name == "Custom Corp"
    assert offer.company.domain == "customcorp.io"
