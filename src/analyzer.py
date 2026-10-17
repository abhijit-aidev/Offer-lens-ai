"""
OfferLens AI - Investigation & Risk Analysis Engine.
Rule-based evaluation of job offers, explainable risk signal calculation,
evidence separation (confirmed vs unknown), connection evidence generation,
and verification steps.
"""

import re
from typing import List, Dict, Any, Optional
from src.models import JobOffer, GraphConnection

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
    "aol.com",
    "mail.com",
    "zoho.com",
    "yandex.com",
    "gmx.com",
}

# Heuristic patterns for upfront payment and artificial urgency
UPFRONT_PAYMENT_PATTERN = re.compile(
    r"\b(wire transfer|crypto|cryptocurrency|bitcoin|usdt|gift card|equipment fee|processing fee|"
    r"deposit .* check|cashier'?s check|check advance|advance fee|home office check|upfront cost|"
    r"purchase equipment|reimbursed check)\b",
    re.IGNORECASE,
)

URGENCY_PATTERN = re.compile(
    r"\b(urgent(?:ly)?|immediate(?:ly)? hire|within 24 hours|within 48 hours|act fast|no interview required|"
    r"no formal interview|immediate placement|limited spots|claim offer immediately|expiring in 24h)\b",
    re.IGNORECASE,
)


def evaluate_risk_signals(
    offer: JobOffer,
    connections: List[GraphConnection],
    is_connected: bool,
) -> List[Dict[str, str]]:
    """
    Generate explainable risk signals based on deterministic patterns and graph matches.
    """
    signals = []
    raw_text = offer.raw_text or ""

    # 1. Explicit Upfront Payment Demands (High Risk)
    payment_matches = UPFRONT_PAYMENT_PATTERN.findall(raw_text)
    if payment_matches:
        unique_matches = list({m.lower() for m in payment_matches})
        signals.append({
            "level": "HIGH",
            "category": "Upfront Payment Request",
            "title": "Advance Fee / Check Deposit Language Detected",
            "reason": (
                f"The offer text references advance payment mechanisms ({', '.join(unique_matches)}). "
                f"Legitimate corporate employers ship equipment directly or provide corporate accounts. "
                f"They never require candidates to deposit checks, transfer crypto, or pay onboarding fees."
            ),
            "evidence": f"Matched pattern: {', '.join(unique_matches)}",
        })

    # 2. Artificial Urgency / Pressure Tactics (Medium Risk)
    urgency_matches = URGENCY_PATTERN.findall(raw_text)
    if urgency_matches:
        unique_urgency = list({m.lower() for m in urgency_matches})
        signals.append({
            "level": "MEDIUM",
            "category": "Urgency & Pressure Tactics",
            "title": "Artificial Urgency Language Detected",
            "reason": (
                f"The communication contains aggressive urgency phrases ({', '.join(unique_urgency)}). "
                f"Pressure to sign or respond without standard due diligence or formal interviews is a common "
                f"coercion tactic."
            ),
            "evidence": f"Matched phrase: {', '.join(unique_urgency)}",
        })

    # 3. Graph Cross-Match Signals (Real Neo4j relationships)
    if is_connected:
        shared_contact_conns = [c for c in connections if c.connection_type == "SHARED_CONTACT"]
        if shared_contact_conns:
            distinct_companies = list({c.target_company_name for c in shared_contact_conns})
            distinct_emails = list({c.shared_value for c in shared_contact_conns})
            signals.append({
                "level": "HIGH",
                "category": "Cross-Company Recruiter Overlap",
                "title": "Recruiter Contact Associated With Multiple Companies",
                "reason": (
                    f"Recruiter email ({', '.join(distinct_emails)}) is linked to distinct organization(s): "
                    f"{', '.join(distinct_companies)} in the database graph. While independent recruiting agencies "
                    f"do represent multiple clients, in-house corporate recruiters typically do not hire for competing firms."
                ),
                "evidence": f"Neo4j traversal found {len(shared_contact_conns)} link(s) on email: {', '.join(distinct_emails)}",
            })

        shared_domain_conns = [c for c in connections if c.connection_type == "SHARED_DOMAIN"]
        if shared_domain_conns:
            signals.append({
                "level": "INFO",
                "category": "Shared Domain Infrastructure",
                "title": "Domain Infrastructure Shared Across Registered Offers",
                "reason": (
                    f"Domain ({offer.company.domain}) is shared with registered offer(s) "
                    f"({', '.join(c.target_offer_id for c in shared_domain_conns)})."
                ),
                "evidence": f"Neo4j match on domain: {offer.company.domain}",
            })

    # 4. Public / Free Email Provider Check
    contact_emails = [c.email.lower() for c in offer.contacts]
    public_emails = []
    for em in contact_emails:
        domain = em.split("@")[-1] if "@" in em else ""
        if domain in PUBLIC_EMAIL_DOMAINS:
            public_emails.append(em)

    if public_emails:
        signals.append({
            "level": "MEDIUM",
            "category": "Identity Inconsistency",
            "title": "Public / Generic Email Provider Used",
            "reason": (
                f"Contact address ({', '.join(public_emails)}) uses a public mail service rather than a "
                f"dedicated corporate email domain for {offer.company.name}."
            ),
            "evidence": f"Public email domain: {public_emails[0].split('@')[-1]}",
        })

    # 5. Domain Mismatch Check
    if offer.company.domain and contact_emails:
        company_dom = offer.company.domain.lower().replace("www.", "")
        mismatched = []
        for em in contact_emails:
            em_dom = em.split("@")[-1].lower()
            if em_dom not in company_dom and company_dom not in em_dom and em_dom not in PUBLIC_EMAIL_DOMAINS:
                mismatched.append((em, em_dom))

        if mismatched:
            details = [f"{em} (domain: {dom})" for em, dom in mismatched]
            signals.append({
                "level": "MEDIUM",
                "category": "Domain Discrepancy",
                "title": "Recruiter Email Domain Differs from Company Web Domain",
                "reason": (
                    f"The contact email domain does not match the company website domain ({company_dom}). "
                    f"Third-party staffing agencies may do this legitimately, but independent corporate verification is advised."
                ),
                "evidence": f"Contact: {details[0]} vs Web: {company_dom}",
            })

    # 6. Missing Critical Identifiers
    if not offer.contacts:
        signals.append({
            "level": "LOW",
            "category": "Data Completeness",
            "title": "No Recruiter Contact Email Detected",
            "reason": "The offer text did not contain an explicit recruiter email address.",
            "evidence": "0 email patterns matched in rule-based extraction.",
        })

    if not offer.company.domain:
        signals.append({
            "level": "LOW",
            "category": "Data Completeness",
            "title": "No Corporate Web Domain Specified",
            "reason": "The offer text does not specify an official corporate URL or website.",
            "evidence": "0 web domains matched in rule-based extraction.",
        })

    # 7. Clean / Baseline State
    if not signals:
        signals.append({
            "level": "INFO",
            "category": "Baseline Audit",
            "title": "No Anomalies Detected in Provided Text",
            "reason": "The extracted identifiers show consistent naming and no cross-company conflicts in the database.",
            "evidence": "Passed deterministic baseline checks.",
        })

    return signals


def build_connection_evidence(
    source_offer: JobOffer,
    connection: GraphConnection,
) -> Dict[str, Any]:
    """
    Build detailed, professional Connection Evidence for two connected offers.
    Explains the graph relationship, why it matters, what it does NOT prove,
    and verification steps.
    """
    if connection.connection_type == "SHARED_CONTACT":
        rel_cypher = (
            f"(:Offer {{id: '{source_offer.id}'}})-[:HAS_CONTACT]->"
            f"(:ContactPerson {{email: '{connection.shared_value}'}})"
            f"<-[:HAS_CONTACT]-(:Offer {{id: '{connection.target_offer_id}'}})"
        )
        why_it_matters = (
            f"The recruiter contact '{connection.shared_value}' is directly connected in the knowledge graph "
            f"to both '{source_offer.company.name}' ({source_offer.id}) and '{connection.target_company_name}' ({connection.target_offer_id}). "
            f"In enterprise hiring, in-house recruiters rarely represent multiple independent employers concurrently. "
            f"This overlap flags a need for verification."
        )
        what_it_does_not_prove = (
            "IMPORTANT: A shared contact does NOT prove fraudulent intent by itself. "
            "Legitimate third-party staffing agencies, multi-client recruitment process outsourcing (RPO) firms, "
            "and external recruiters frequently represent several hiring clients using a single professional address."
        )
        verification_steps = [
            f"Verify if '{connection.shared_value}' operates as an accredited external staffing agency or recruitment partner.",
            f"Contact the corporate HR department of {source_offer.company.name} directly via official switchboard.",
            f"Contact the corporate HR department of {connection.target_company_name} to confirm their relationship with the recruiter.",
        ]
    else:  # SHARED_DOMAIN
        rel_cypher = (
            f"(:Offer {{id: '{source_offer.id}'}})-[:OFFERED_BY]->(:Company)-[:USES_DOMAIN]->"
            f"(:Domain {{name: '{connection.shared_value}'}})"
            f"<-[:USES_DOMAIN]-(:Company)<-[:OFFERED_BY]-(:Offer {{id: '{connection.target_offer_id}'}})"
        )
        why_it_matters = (
            f"Both offers share or link to the web domain '{connection.shared_value}'. "
            f"This indicates shared digital infrastructure between {source_offer.company.name} and {connection.target_company_name}."
        )
        what_it_does_not_prove = (
            "A shared domain does NOT prove fraud; parent holding companies, subsidiaries, "
            "and multi-brand corporate groups often share unified web domains and hosting infrastructure."
        )
        verification_steps = [
            f"Inspect WHOIS and corporate registrar data for '{connection.shared_value}'.",
            f"Check if {source_offer.company.name} and {connection.target_company_name} share common ownership or subsidiary status.",
        ]

    return {
        "source_offer_id": source_offer.id,
        "source_company": source_offer.company.name,
        "target_offer_id": connection.target_offer_id,
        "target_company": connection.target_company_name,
        "shared_identifier": connection.shared_value,
        "connection_type": connection.connection_type,
        "relationship_cypher": rel_cypher,
        "why_it_matters": why_it_matters,
        "what_it_does_not_prove": what_it_does_not_prove,
        "verification_steps": verification_steps,
    }


def get_confirmed_vs_unknown(
    offer: JobOffer,
    connections: List[GraphConnection],
    is_connected: bool,
) -> Dict[str, List[str]]:
    """
    Clearly separate verified, extracted facts from unconfirmed assumptions.
    """
    confirmed = []
    unknown = []

    # Confirmed from extraction
    if offer.company.name and offer.company.name != "Unknown Company":
        confirmed.append(f"Company name stated in text: **{offer.company.name}**")
    else:
        unknown.append("Company name is unstated or ambiguous in provided text.")

    if offer.title:
        confirmed.append(f"Job role / position stated: **{offer.title}**")

    if offer.salary:
        confirmed.append(f"Compensation / stipend stated: **{offer.salary}**")
    else:
        unknown.append("Compensation amount is unstated in the provided text.")

    if offer.contacts:
        emails_str = ", ".join(f"`{c.email}`" for c in offer.contacts)
        confirmed.append(f"Extracted contact address(es): {emails_str}")
    else:
        unknown.append("No recruiter email address provided in text.")

    if offer.company.domain:
        confirmed.append(f"Declared corporate domain: `{offer.company.domain}`")
    else:
        unknown.append("No corporate domain or website specified.")

    # Graph connectivity
    if is_connected:
        if connections:
            for conn in connections:
                confirmed.append(
                    f"**Neo4j Graph Traversal:** Linked to `{conn.target_offer_id}` ({conn.target_company_name}) "
                    f"via {conn.connection_type} (`{conn.shared_value}`)."
                )
        else:
            confirmed.append("**Neo4j Graph Audit:** 0 overlapping contacts or domains found in current database.")
    else:
        unknown.append("Graph relationship traversal unverified: Neo4j database is offline.")

    # Crucial operational unknowns (Never claim real-world verification without external registry)
    unknown.append("Legal entity status unverified (requires official State Business Registry / SEC EDGAR lookup).")
    unknown.append("Recruiter employee standing unverified (requires corporate directory or DNS MX lookup).")
    unknown.append("Written employment contract validity unconfirmed.")

    return {
        "confirmed": confirmed,
        "unknown": unknown,
    }


def get_verification_steps(
    offer: JobOffer,
    signals: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Generate tailored, actionable verification steps for the investigator.
    """
    steps = []

    # Step 1: Corporate Domain Verification
    domain = offer.company.domain or (offer.contacts[0].email.split("@")[-1] if offer.contacts else None)
    if domain:
        steps.append({
            "action": f"Verify Domain WHOIS & MX Records for `{domain}`",
            "detail": (
                f"Check the creation date and registrant of `{domain}`. Newly registered domains "
                f"(under 6 months old) imitating established firms are a primary indicator of recruitment impersonation."
            ),
        })

    # Step 2: Cross-Reference Official Careers Page
    if offer.company.name:
        steps.append({
            "action": f"Cross-Reference Openings on Official {offer.company.name} Portal",
            "detail": (
                f"Navigate directly to the verified corporate website of {offer.company.name} (do not click links "
                f"contained in unsolicited messages) and verify that the role '{offer.title}' is actively posted."
            ),
        })

    # Step 3: Recruiter Verification
    if offer.contacts:
        email = offer.contacts[0].email
        steps.append({
            "action": f"Validate Recruiter Email `{email}`",
            "detail": (
                "Search LinkedIn or contact the company's official general switchboard or HR desk to verify "
                "that the named recruiter is an active authorized representative."
            ),
        })

    # Step 4: Financial Safety
    steps.append({
        "action": "Enforce Zero-Payment Protocol",
        "detail": (
            "Never send funds, purchase gift cards, or deposit checks for 'home office equipment' or "
            "'application background checks'. Legitimate employers provide equipment directly."
        ),
    })

    return steps
