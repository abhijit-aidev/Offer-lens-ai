"""
Pydantic data models for OfferLens AI.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class ContactPerson(BaseModel):
    name: Optional[str] = None
    email: str = Field(..., description="Recruiter or contact email address")


class Company(BaseModel):
    name: str = Field(..., description="Company name")
    domain: Optional[str] = Field(None, description="Company website or email domain")


class JobOffer(BaseModel):
    id: str = Field(..., description="Unique identifier for the offer, e.g. OFFER-A")
    title: str = Field(default="Software Engineer", description="Job role or title")
    company: Company = Field(..., description="Company making the offer")
    contacts: List[ContactPerson] = Field(default_factory=list, description="Associated contacts/recruiters")
    salary: Optional[str] = Field(None, description="Estimated or offered compensation")
    location: Optional[str] = Field(None, description="Work location / remote")
    raw_text: Optional[str] = Field(None, description="Original offer letter or email snippet")


class GraphConnection(BaseModel):
    source_offer_id: str
    target_offer_id: str
    target_company_name: str
    connection_type: str  # "SHARED_CONTACT" or "SHARED_DOMAIN"
    shared_value: str
    explanation: str
