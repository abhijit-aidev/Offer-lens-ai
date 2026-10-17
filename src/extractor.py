"""
Rule-based extraction engine for OfferLens AI.
Extracts company names, recruiter emails, domains, and job details using
deterministic pattern matching (regular expressions and heuristics) without paid AI APIs.
"""

import re
import uuid
from typing import List, Optional
from urllib.parse import urlparse

from src.models import Company, ContactPerson, JobOffer

EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
DOMAIN_REGEX = re.compile(
    r"\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|org|net|ai|io|tech|co|test|xyz|app|dev))\b",
    re.IGNORECASE,
)
SALARY_REGEX = re.compile(
    r"(\$\s*[\d,]+(?:\s*-\s*\$?\s*[\d,]+)?(?:\s*(?:k|K|per year|annually|/yr|/year|USD))?)",
    re.IGNORECASE,
)
COMPANY_PREFIX_REGEX = re.compile(
    r"(?:Company|Employer|Organization|At|From)\s*[:\-]\s*([A-Za-z0-9\s&.,'-]+?)(?=\n|$|,|\.)",
    re.IGNORECASE,
)
ROLE_PREFIX_REGEX = re.compile(
    r"(?:Role|Position|Title|Job\s*Title)\s*[:\-]\s*([A-Za-z0-9\s&.,'/-]+?)(?=\n|$|,|\.)",
    re.IGNORECASE,
)


def extract_emails(text: str) -> List[str]:
    """Extract unique lowercase email addresses from text, stripping trailing punctuation."""
    matches = EMAIL_REGEX.findall(text)
    seen = set()
    emails = []
    for m in matches:
        clean = m.strip().rstrip(".,;:)!?'\"").lower()
        if clean and "@" in clean and clean not in seen:
            seen.add(clean)
            emails.append(clean)
    return emails



def extract_domains(text: str, emails: Optional[List[str]] = None) -> List[str]:
    """Extract unique domains from explicit text matches and email domains."""
    seen = set()
    domains = []

    # 1. From text matches
    for m in DOMAIN_REGEX.finditer(text):
        raw = m.group(1).strip().lower()
        if raw and raw not in seen:
            seen.add(raw)
            domains.append(raw)

    # 2. From email addresses
    if emails:
        for em in emails:
            if "@" in em:
                dom = em.split("@")[-1].strip().lower()
                if dom and dom not in seen:
                    seen.add(dom)
                    domains.append(dom)

    return domains


def extract_company_name(text: str, default_domain: Optional[str] = None) -> str:
    """Extract company name using keyword prefixes or fallback heuristics."""
    match = COMPANY_PREFIX_REGEX.search(text)
    if match:
        name = match.group(1).strip()
        if len(name) > 1:
            return name

    # Check for known patterns like "NovaEdge Technologies", "BrightPath AI", "Summit Digital"
    known_patterns = [
        r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?\s+(?:Technologies|AI|Digital|Corp|Corporation|Inc|LLC|Solutions|Labs|Ventures))\b",
        r"\b([A-Z][a-zA-Z0-9]+\s+[A-Z][a-zA-Z0-9]+)\b",
    ]
    for pat in known_patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()

    # Fallback to deriving name from domain if available
    if default_domain:
        base = default_domain.split(".")[0].replace("-example", "").replace("-", " ").title()
        return base

    return "Unknown Company"


def extract_job_title(text: str) -> str:
    """Extract job role / title from text."""
    match = ROLE_PREFIX_REGEX.search(text)
    if match:
        title = match.group(1).strip()
        if len(title) > 2:
            return title

    # Common job title patterns
    title_patterns = [
        r"\b(Senior\s+Software\s+Engineer)\b",
        r"\b(Software\s+Engineer)\b",
        r"\b(Frontend\s+Engineer)\b",
        r"\b(Backend\s+Engineer)\b",
        r"\b(Full\s*Stack\s+Engineer)\b",
        r"\b(Machine\s+Learning\s+Engineer)\b",
        r"\b(AI\s+Engineer)\b",
        r"\b(Data\s+Scientist)\b",
        r"\b(Product\s+Manager)\b",
    ]
    for pat in title_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return "Software Engineer"


def extract_salary(text: str) -> Optional[str]:
    """Extract salary or compensation string."""
    m = SALARY_REGEX.search(text)
    if m:
        return m.group(1).strip()
    return None


def parse_job_offer_from_text(
    text: str,
    offer_id: Optional[str] = None,
    explicit_company: Optional[str] = None,
    explicit_domain: Optional[str] = None,
) -> JobOffer:
    """
    Complete rule-based parsing pipeline that extracts entities
    and returns a validated JobOffer model.
    """
    emails = extract_emails(text)
    domains = extract_domains(text, emails)

    domain = explicit_domain or (domains[0] if domains else None)
    company_name = explicit_company or extract_company_name(text, default_domain=domain)
    job_title = extract_job_title(text)
    salary = extract_salary(text)

    # Build contacts
    contacts = [ContactPerson(email=e) for e in emails]

    # Generate or use provided ID
    uid = offer_id or f"OFFER-{uuid.uuid4().hex[:6].upper()}"

    company = Company(name=company_name, domain=domain)

    return JobOffer(
        id=uid,
        title=job_title,
        company=company,
        contacts=contacts,
        salary=salary,
        raw_text=text.strip(),
    )
