"""
Tests for rule-based extraction in OfferLens AI.
"""

from src.extractor import (
    extract_emails,
    extract_domains,
    extract_company_name,
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
    Role: Full Stack Engineer
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
