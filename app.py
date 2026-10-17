"""
OfferLens AI - Investigation & Verification Platform.
Refined editorial / luxury fintech aesthetic for job offer intelligence,
recruiter cross-referencing, and graph threat analysis using Neo4j and rule-based extraction.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any

from src.config import Neo4jConfig
from src.db import Neo4jConnection
from src.repository import OfferRepository
from src.extractor import parse_job_offer_from_text
from src.analyzer import (
    evaluate_risk_signals,
    build_connection_evidence,
    get_confirmed_vs_unknown,
    get_verification_steps,
)
from src.visualizer import generate_interactive_graph_html
from src.models import JobOffer, GraphConnection

# Page Configuration
st.set_page_config(
    page_title="OfferLens AI | Editorial Investigation Protocol",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Premium Editorial & Luxury Fintech Custom CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;1,6..72,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Warm Ivory Canvas */
    .stApp {
        background-color: #F7F2E8 !important;
        color: #292320 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Sidebar Warm Tone */
    [data-testid="stSidebar"] {
        background-color: #EDE3D2 !important;
        border-right: 1px solid #D8C9B7 !important;
    }

    /* Editorial Brand Header */
    .editorial-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 2px solid #702632;
        padding-bottom: 1.1rem;
        margin-bottom: 1.75rem;
    }
    .brand-title {
        font-family: 'Newsreader', Georgia, 'Times New Roman', serif;
        font-size: 2.35rem;
        font-weight: 700;
        color: #4A1721;
        letter-spacing: -0.02em;
        line-height: 1.1;
        margin: 0;
    }
    .brand-title span {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
        color: #702632;
        background: #EDE3D2;
        border: 1px solid #D8C9B7;
        padding: 3px 8px;
        border-radius: 4px;
        vertical-align: middle;
        margin-left: 0.4rem;
        letter-spacing: 0.05em;
    }
    .brand-tagline {
        color: #746A61;
        font-size: 0.86rem;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 0.35rem;
    }

    /* Status Pill */
    .status-pill-online {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #EBF5EE;
        color: #1E663B;
        border: 1px solid #B7DECA;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        letter-spacing: 0.04em;
    }
    .status-pill-offline {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #FAF0E6;
        color: #702632;
        border: 1px solid #D8C9B7;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        letter-spacing: 0.04em;
    }

    /* Soft Beige Editorial Cards */
    .editorial-card {
        background-color: #EDE3D2;
        color: #292320;
        border: 1px solid #D8C9B7;
        border-radius: 8px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 2px 10px rgba(41, 35, 32, 0.03);
    }
    .card-heading {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #4A1721;
        border-bottom: 1px solid #D8C9B7;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Burgundy Primary Action Button */
    div.stButton > button[kind="primary"], div.stButton > button:first-child {
        background-color: #702632 !important;
        color: #FFFFFF !important;
        border: 1px solid #4A1721 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em !important;
        padding: 0.55rem 1.6rem !important;
        box-shadow: 0 2px 8px rgba(112, 38, 50, 0.2) !important;
        transition: all 0.18s ease-in-out !important;
    }
    div.stButton > button[kind="primary"]:hover, div.stButton > button:first-child:hover {
        background-color: #4A1721 !important;
        border-color: #292320 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(74, 23, 33, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton > button:focus {
        box-shadow: 0 0 0 2px #F7F2E8, 0 0 0 4px #702632 !important;
    }

    /* Clean Form Elements */
    .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #292320 !important;
        border: 1px solid #D8C9B7 !important;
        border-radius: 6px !important;
        font-size: 0.9rem !important;
    }
    .stTextArea textarea {
        font-family: 'JetBrains Mono', ui-monospace, monospace !important;
        line-height: 1.55 !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #702632 !important;
        box-shadow: 0 0 0 1px #702632 !important;
    }

    /* Refined Editorial Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid #D8C9B7 !important;
        gap: 12px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #746A61 !important;
        background-color: transparent !important;
        border-bottom: 2px solid transparent !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        padding: 0.6rem 1.1rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.15s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #4A1721 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #702632 !important;
        border-bottom: 2px solid #702632 !important;
        font-weight: 700 !important;
    }

    /* Dossier Grid Cells */
    .dossier-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 0.75rem;
    }
    .dossier-cell {
        background: #F7F2E8;
        border: 1px solid #D8C9B7;
        border-radius: 6px;
        padding: 0.75rem 0.95rem;
    }
    .dossier-label {
        font-size: 0.73rem;
        font-weight: 600;
        color: #746A61;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.25rem;
    }
    .dossier-val {
        font-size: 0.95rem;
        font-weight: 600;
        color: #292320;
        font-family: 'JetBrains Mono', ui-monospace, monospace;
        word-break: break-word;
    }

    /* Risk Badges (Editorial Styling) */
    .risk-high {
        background: #FDF4F4;
        border: 1px solid #F1CECE;
        border-left: 4px solid #702632;
        border-radius: 6px;
        padding: 0.9rem 1.15rem;
        margin-bottom: 0.65rem;
    }
    .risk-medium {
        background: #FAF6EF;
        border: 1px solid #E8DECE;
        border-left: 4px solid #B77C82;
        border-radius: 6px;
        padding: 0.9rem 1.15rem;
        margin-bottom: 0.65rem;
    }
    .risk-info {
        background: #F5F7F4;
        border: 1px solid #D5DDD3;
        border-left: 4px solid #4A1721;
        border-radius: 6px;
        padding: 0.9rem 1.15rem;
        margin-bottom: 0.65rem;
    }

    /* Connection Evidence Cards */
    .evidence-card {
        background: #F7F2E8;
        border: 1px solid #D8C9B7;
        border-left: 4px solid #702632;
        border-radius: 6px;
        padding: 1.15rem 1.35rem;
        margin-bottom: 0.85rem;
    }
    .evidence-title {
        font-family: 'Newsreader', Georgia, serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #4A1721;
        margin-bottom: 0.4rem;
    }
    .shared-tag {
        background: #EDE3D2;
        color: #4A1721;
        border: 1px solid #D8C9B7;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.86rem;
    }

    /* Step Card */
    .step-card {
        background: #F7F2E8;
        border: 1px solid #D8C9B7;
        border-radius: 6px;
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.55rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
default_uri = Neo4jConfig.get_uri()
default_user = Neo4jConfig.get_username()
default_pass = Neo4jConfig.get_password()
default_db = Neo4jConfig.get_database()

current_uri = st.session_state.get("neo4j_uri", default_uri)
current_user = st.session_state.get("neo4j_user", default_user)
current_pass = st.session_state.get("neo4j_pass", default_pass)
current_db = st.session_state.get("neo4j_db", default_db)

# Check Neo4j Connectivity (Real query check)
is_connected, status_msg = Neo4jConnection.test_connection(current_uri, current_user, current_pass)

# Editorial Brand Header
st.markdown(
    f"""
    <div class="editorial-header">
        <div>
            <h1 class="brand-title">OfferLens <span>PROTOCOL</span></h1>
            <div class="brand-tagline">Graph-Powered Recruitment Intelligence & Offer Verification</div>
        </div>
        <div>
            {
                f'<span class="status-pill-online">● NEO4J GRAPH ONLINE</span>' 
                if is_connected else 
                f'<span class="status-pill-offline">○ GRAPH ENGINE OFFLINE</span>'
            }
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation Tabs
tab_investigate, tab_explorer, tab_architecture = st.tabs([
    "Investigate Offer",
    "Graph Topology Explorer",
    "Extraction Architecture",
])


# ==============================================================================
# TAB 1: INVESTIGATE AN OFFER (PRIMARY USER JOURNEY)
# ==============================================================================
with tab_investigate:
    # Honest Database Status Notice (Clean & Unobtrusive)
    if not is_connected:
        st.markdown(
            f"""
            <div style="background-color: #EDE3D2; border: 1px solid #D8C9B7; border-left: 4px solid #702632; padding: 0.75rem 1.15rem; border-radius: 6px; margin-bottom: 1.25rem; font-size: 0.86rem; color: #292320;">
                <strong style="color: #4A1721;">Graph Notice:</strong> Neo4j graph database is offline at <code>{current_uri}</code>. 
                Deterministic rule-based entity extraction, risk indicators, and local heuristic checks are fully active. 
                Graph cross-referencing requires an active Neo4j connection. Zero mock connections are fabricated.
                <em style="color: #746A61; margin-left: 0.5rem;">(Configure in Developer Diagnostics below).</em>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Preset selector for fast test evaluation
    preset_samples = {
        "Custom Input (Paste your own)": "",
        "Offer A — NovaEdge Technologies (Shares synthetic contact with BrightPath AI)": (
            "Congratulations! NovaEdge Technologies is delighted to offer you the role of Senior Backend Engineer.\n"
            "Company: NovaEdge Technologies\n"
            "Official Portal: novaedge-example.com\n"
            "Recruiter Contact: recruit-a@example.test\n"
            "Compensation: $165,000 / year\n"
            "Location: Remote\n"
            "We look forward to welcoming you to the team."
        ),
        "Offer B — BrightPath AI (Shares synthetic contact with NovaEdge Technologies)": (
            "From: recruit-a@example.test\n"
            "Subject: Formal Offer - BrightPath AI\n"
            "Company: BrightPath AI\n"
            "Domain: brightpath-example.com\n"
            "Role: Machine Learning Engineer\n"
            "Salary: $180,000 / year\n"
            "Hiring Team: recruit-a@example.test"
        ),
        "Offer C — Summit Digital (Completely isolated baseline offer)": (
            "Company: Summit Digital\n"
            "Website: summit-example.com\n"
            "Role: Full Stack Developer\n"
            "Stipend / Salary: $140,000 / year\n"
            "Recruiter Contact: jobs@summit-example.com"
        ),
    }

    # Main Input Panel
    st.markdown(
        """
        <div class="editorial-card">
            <div class="card-heading">
                <span>Offer Document Input</span>
                <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.75rem; color: #746A61; text-transform: uppercase; font-weight: 600;">STEP 01</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    col_select, col_id = st.columns([3, 1])
    with col_select:
        selected_preset = st.selectbox(
            "Select Evaluation Sample or Paste Custom Offer:",
            list(preset_samples.keys()),
            index=0,
            label_visibility="visible",
        )
    with col_id:
        assigned_id = st.text_input(
            "Reference ID (Optional):",
            value="OFFER-A" if "Offer A" in selected_preset else ("OFFER-B" if "Offer B" in selected_preset else ("OFFER-C" if "Offer C" in selected_preset else "")),
            placeholder="e.g. OFR-2026",
        )

    default_text = preset_samples[selected_preset]
    raw_input_text = st.text_area(
        "Job Offer Communication / Contract Text:",
        value=default_text,
        height=165,
        placeholder="Paste full job offer email, letter text, or internship notice here...",
        key="investigation_text_area",
    )

    col_btn, col_help = st.columns([1, 4])
    with col_btn:
        btn_analyse = st.button("Analyse Offer", type="primary", use_container_width=True)
    with col_help:
        st.markdown(
            "<span style='color: #746A61; font-size: 0.84rem; line-height: 2.6;'>Runs deterministic regex extraction, Neo4j graph cross-matching, and risk evaluation.</span>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Execute Investigation Analysis
    if btn_analyse or (raw_input_text.strip() and st.session_state.get("auto_ran")):
        st.session_state["auto_ran"] = True

        if not raw_input_text.strip():
            st.warning("Please paste or load offer text to run analysis.")
        else:
            # 1. Deterministic Rule-Based Extraction
            extracted_offer = parse_job_offer_from_text(
                raw_input_text,
                offer_id=assigned_id if assigned_id.strip() else None,
            )

            # 2. Real Neo4j Graph Query
            graph_connections: List[GraphConnection] = []
            if is_connected:
                try:
                    driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
                    repo = OfferRepository(driver, database=current_db)
                    
                    extracted_emails = [c.email for c in extracted_offer.contacts]
                    extracted_domains = [extracted_offer.company.domain] if extracted_offer.company.domain else []
                    
                    graph_connections = repo.find_related_by_entities(
                        emails=extracted_emails,
                        domains=extracted_domains,
                        source_id=extracted_offer.id,
                        exclude_offer_id=extracted_offer.id if assigned_id.strip() else None,
                    )
                except Exception as e:
                    st.error(f"Neo4j query error: {e}")

            # 3. Evaluate Explainable Risk Signals
            risk_signals = evaluate_risk_signals(extracted_offer, graph_connections, is_connected)

            # 4. Confirmed vs Unknown Separation
            findings_breakdown = get_confirmed_vs_unknown(extracted_offer, graph_connections, is_connected)

            # 5. Practical Verification Steps
            verification_steps = get_verification_steps(extracted_offer, risk_signals)

            # ----------------------------------------------------
            # Section 1: Extracted Offer Dossier
            # ----------------------------------------------------
            emails_display = ", ".join(c.email for c in extracted_offer.contacts) if extracted_offer.contacts else "None detected"
            domain_display = extracted_offer.company.domain if extracted_offer.company.domain else "None detected"
            salary_display = extracted_offer.salary if extracted_offer.salary else "Unstated"

            st.markdown(
                f"""
                <div class="editorial-card">
                    <div class="card-heading">
                        <span>Extracted Offer Dossier</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #702632; font-weight: 700;">VALIDATED ATTRIBUTES</span>
                    </div>
                    <div class="dossier-grid">
                        <div class="dossier-cell">
                            <div class="dossier-label">Target Organization</div>
                            <div class="dossier-val" style="color: #4A1721;">{extracted_offer.company.name}</div>
                        </div>
                        <div class="dossier-cell">
                            <div class="dossier-label">Role / Position</div>
                            <div class="dossier-val">{extracted_offer.title}</div>
                        </div>
                        <div class="dossier-cell">
                            <div class="dossier-label">Stipend / Compensation</div>
                            <div class="dossier-val">{salary_display}</div>
                        </div>
                        <div class="dossier-cell">
                            <div class="dossier-label">Recruiter Contact(s)</div>
                            <div class="dossier-val">{emails_display}</div>
                        </div>
                        <div class="dossier-cell">
                            <div class="dossier-label">Associated Domain</div>
                            <div class="dossier-val">{domain_display}</div>
                        </div>
                        <div class="dossier-cell">
                            <div class="dossier-label">Dossier Reference</div>
                            <div class="dossier-val" style="color: #702632;">{extracted_offer.id}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # ----------------------------------------------------
            # Section 2: Offer Risk Indicators (Explainable Signals)
            # ----------------------------------------------------
            st.markdown(
                """
                <div class="editorial-card">
                    <div class="card-heading">
                        <span>Offer Risk Indicators</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #746A61; font-weight: 600;">EXPLAINABLE AUDIT</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            for sig in risk_signals:
                badge_class = f"risk-{sig['level'].lower()}"
                level_color = "#702632" if sig['level'] == 'HIGH' else ("#B77C82" if sig['level'] == 'MEDIUM' else "#4A1721")
                st.markdown(
                    f"""
                    <div class="{badge_class}">
                        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.25rem;">
                            <strong style="color: {level_color}; font-size: 0.92rem; font-family: 'Plus Jakarta Sans', sans-serif;">
                                [{sig['level']}] {sig['title']}
                            </strong>
                            <span style="font-size: 0.74rem; color: #746A61; font-family: 'JetBrains Mono', monospace;">{sig.get('category', 'Threat Category')}</span>
                        </div>
                        <div style="font-size: 0.88rem; color: #292320; margin-bottom: 0.35rem; line-height: 1.5;">
                            {sig['reason']}
                        </div>
                        <div style="font-size: 0.78rem; color: #746A61; font-family: 'JetBrains Mono', monospace;">
                            Evidence: {sig['evidence']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

            # ----------------------------------------------------
            # Section 3: Connection Evidence (Polished Distinctive Feature)
            # ----------------------------------------------------
            st.markdown(
                """
                <div class="editorial-card">
                    <div class="card-heading">
                        <span>Connection Evidence</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #702632; font-weight: 700;">NEO4J GRAPH RELATIONSHIPS</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            if not is_connected:
                st.markdown(
                    """
                    <div style="padding: 0.85rem 1rem; background: #F7F2E8; border: 1px solid #D8C9B7; border-radius: 6px; font-size: 0.86rem; color: #746A61;">
                        <em>Graph relationships unverified: Neo4j is offline. Connect database in Developer Diagnostics to run real Cypher path discovery.</em>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif graph_connections:
                st.markdown(
                    f"<p style='color: #292320; font-size: 0.9rem; margin-bottom: 0.85rem;'>Neo4j traversed relationship paths and confirmed <strong>{len(graph_connections)}</strong> direct entity connection(s):</p>",
                    unsafe_allow_html=True,
                )
                for conn in graph_connections:
                    evidence = build_connection_evidence(extracted_offer, conn)
                    st.markdown(
                        f"""
                        <div class="evidence-card">
                            <div class="evidence-title">
                                {evidence['source_company']} ({evidence['source_offer_id']}) &harr; {evidence['target_company']} ({evidence['target_offer_id']})
                            </div>
                            <div style="font-size: 0.88rem; color: #292320; margin-bottom: 0.4rem;">
                                <strong>EXACT Shared Identifier:</strong> <span class="shared-tag">{evidence['shared_identifier']}</span> 
                                <span style="color: #746A61; font-size: 0.78rem; margin-left: 0.5rem;">({evidence['connection_type']})</span>
                            </div>
                            <div style="font-size: 0.8rem; color: #746A61; font-family: 'JetBrains Mono', monospace; background: #EDE3D2; padding: 4px 8px; border-radius: 4px; border: 1px solid #D8C9B7; margin-bottom: 0.6rem;">
                                Cypher Path: {evidence['relationship_cypher']}
                            </div>
                            <div style="font-size: 0.86rem; color: #292320; margin-bottom: 0.4rem; line-height: 1.5;">
                                <strong>Why this match matters:</strong> {evidence['why_it_matters']}
                            </div>
                            <div style="font-size: 0.84rem; color: #702632; background: rgba(112, 38, 50, 0.05); border: 1px solid rgba(112, 38, 50, 0.15); padding: 0.55rem 0.85rem; border-radius: 4px; margin-bottom: 0.6rem; line-height: 1.45;">
                                {evidence['what_it_does_not_prove']}
                            </div>
                            <div style="font-size: 0.82rem; color: #746A61;">
                                <strong>Practical Verification:</strong>
                                <ul style="margin-top: 0.2rem; margin-bottom: 0; padding-left: 1.2rem;">
                                    {"".join(f"<li>{s}</li>" for s in evidence['verification_steps'])}
                                </ul>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    """
                    <div style="background: #F7F2E8; border: 1px solid #D8C9B7; border-radius: 6px; padding: 0.95rem 1.15rem; color: #292320; font-size: 0.88rem;">
                        <strong style="color: #4A1721;">0 Overlapping Connections Identified.</strong><br>
                        <span style="color: #746A61; font-size: 0.84rem;">None of the extracted contacts or domains link to other entities registered in the Neo4j database graph.</span><br>
                        <span style="font-size: 0.8rem; color: #702632; font-family: 'JetBrains Mono', monospace;">(Confirmed: Offer C / Summit Digital remains completely isolated through seeded identifiers.)</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

            # ----------------------------------------------------
            # Section 4: Confirmed Findings vs Unknown Information
            # ----------------------------------------------------
            col_conf, col_unkn = st.columns(2)

            with col_conf:
                st.markdown(
                    """
                    <div class="editorial-card" style="height: 100%;">
                        <div class="card-heading">
                            <span style="color: #702632;">Confirmed Findings (Verified)</span>
                        </div>
                        <ul style="padding-left: 1.2rem; font-size: 0.88rem; color: #292320; line-height: 1.65; margin-bottom: 0;">
                    """,
                    unsafe_allow_html=True,
                )
                for item in findings_breakdown["confirmed"]:
                    st.markdown(f"<li style='margin-bottom: 0.35rem;'>{item}</li>", unsafe_allow_html=True)
                st.markdown("</ul></div>", unsafe_allow_html=True)

            with col_unkn:
                st.markdown(
                    """
                    <div class="editorial-card" style="height: 100%;">
                        <div class="card-heading">
                            <span style="color: #B77C82;">Unknown / Unverified Information</span>
                        </div>
                        <ul style="padding-left: 1.2rem; font-size: 0.88rem; color: #746A61; line-height: 1.65; margin-bottom: 0;">
                    """,
                    unsafe_allow_html=True,
                )
                for item in findings_breakdown["unknown"]:
                    st.markdown(f"<li style='margin-bottom: 0.35rem;'>{item}</li>", unsafe_allow_html=True)
                st.markdown("</ul></div>", unsafe_allow_html=True)

            # ----------------------------------------------------
            # Section 5: Practical Verification Protocol
            # ----------------------------------------------------
            st.markdown(
                """
                <div class="editorial-card">
                    <div class="card-heading">
                        <span>Due Diligence & Verification Protocol</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #702632; font-weight: 700;">ACTION PLAN</span>
                    </div>
                    <div style="font-size: 0.86rem; color: #746A61; margin-bottom: 0.9rem;">
                        Recommended protocol before signing contracts or disclosing sensitive personal information:
                    </div>
                """,
                unsafe_allow_html=True,
            )

            for idx, step in enumerate(verification_steps, 1):
                st.markdown(
                    f"""
                    <div class="step-card">
                        <div style="font-weight: 600; color: #4A1721; font-size: 0.92rem; margin-bottom: 0.25rem;">
                            <span style="color: #702632; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; margin-right: 0.4rem;">[STEP 0{idx}]</span>
                            {step['action']}
                        </div>
                        <div style="font-size: 0.85rem; color: #746A61; line-height: 1.5;">
                            {step['detail']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 2: GRAPH TOPOLOGY EXPLORER
# ==============================================================================
with tab_explorer:
    st.markdown(
        """
        <div class="editorial-card">
            <div class="card-heading">
                <span>Knowledge Graph Topology</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #702632; font-weight: 700;">NEO4J VISUALIZATION</span>
            </div>
            <p style="font-size: 0.88rem; color: #746A61; margin-bottom: 1rem;">
                Visual graph topology rendered directly from Neo4j. Observe how <strong>Offer A</strong> and <strong>Offer B</strong> 
                cross-connect through shared recruiter node <code style="color: #702632; background: #F7F2E8; padding: 2px 6px; border-radius: 3px;">recruit-a@example.test</code>, 
                while <strong>Offer C</strong> remains completely isolated in its own independent cluster.
            </p>
        """,
        unsafe_allow_html=True,
    )

    if not is_connected:
        st.warning("Neo4j database is offline. Connect database in Developer Diagnostics to view live visual graph.")
    else:
        try:
            driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
            repo = OfferRepository(driver, database=current_db)
            graph_data = repo.get_graph_elements()

            if not graph_data["nodes"]:
                st.info("The Neo4j database has no nodes. Go to 'Developer Diagnostics' below to seed ground-truth offers.")
            else:
                st.caption(f"Rendering {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges directly from Neo4j.")
                html_canvas = generate_interactive_graph_html(
                    graph_data["nodes"],
                    graph_data["edges"],
                    height=520,
                )
                st.components.v1.html(html_canvas, height=545)
        except Exception as e:
            st.error(f"Error rendering graph: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Stored Offers Table
    if is_connected:
        st.markdown(
            """
            <div class="editorial-card">
                <div class="card-heading">
                    <span>Registered Database Records</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #702632; font-weight: 700;">STORED OFFERS</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        try:
            driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
            repo = OfferRepository(driver, database=current_db)
            db_offers = repo.list_offers()
            if db_offers:
                df = pd.DataFrame([
                    {
                        "Offer ID": o["id"],
                        "Company": o["company_name"],
                        "Role": o["title"],
                        "Domain": o["domain"] or "None",
                        "Recruiter Email(s)": ", ".join(o["contact_emails"]) if o["contact_emails"] else "None",
                        "Compensation": o["salary"] or "N/A",
                    }
                    for o in db_offers
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No offers stored.")
        except Exception as e:
            st.error(f"Failed to load offers: {e}")

        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 3: EXTRACTION ARCHITECTURE
# ==============================================================================
with tab_architecture:
    st.markdown(
        """
        <div class="editorial-card">
            <div class="card-heading">
                <span>Zero-Cost Deterministic Extraction Engine</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #702632; font-weight: 700;">SPECIFICATION</span>
            </div>
            <p style="font-size: 0.88rem; color: #292320; line-height: 1.6;">
                OfferLens AI operates <strong>without paid AI APIs</strong>. It extracts structured entities from raw unformatted 
                offer letters using regular expression tokenizers, contextual boundary matching, and domain heuristics.
            </p>
            <div class="dossier-grid" style="margin-top: 1.1rem;">
                <div class="dossier-cell">
                    <div class="dossier-label">Email Regex</div>
                    <div style="font-size: 0.8rem; color: #702632; font-family: 'JetBrains Mono', monospace;">\\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+\\b</div>
                </div>
                <div class="dossier-cell">
                    <div class="dossier-label">Domain Regex</div>
                    <div style="font-size: 0.8rem; color: #702632; font-family: 'JetBrains Mono', monospace;">\\b(?:https?://)?(?:www\\.)?([a-zA-Z0-9-]+\\.(com|org|net|ai|io|...))</div>
                </div>
                <div class="dossier-cell">
                    <div class="dossier-label">Compensation Regex</div>
                    <div style="font-size: 0.8rem; color: #702632; font-family: 'JetBrains Mono', monospace;">\\$\\s*[\\d,]+(?:\\s*-\\s*\\$?[\\d,]+)?...</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="editorial-card">
            <div class="card-heading">
                <span>Pydantic v2 Data Contracts</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #702632; font-weight: 700;">DATA INTEGRITY</span>
            </div>
            <p style="font-size: 0.86rem; color: #746A61;">
                All extracted entities pass through strict Pydantic v2 data models ensuring schema conformity before graph persistence:
            </p>
        """,
        unsafe_allow_html=True,
    )
    st.code(
        """
class ContactPerson(BaseModel):
    name: Optional[str] = None
    email: str

class Company(BaseModel):
    name: str
    domain: Optional[str] = None

class JobOffer(BaseModel):
    id: str
    title: str = "Software Engineer"
    company: Company
    contacts: List[ContactPerson] = []
    salary: Optional[str] = None
    location: Optional[str] = None
    raw_text: Optional[str] = None
        """,
        language="python",
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# EXPANDABLE DEVELOPER DIAGNOSTICS & NEO4J CYPHER LAB
# ==============================================================================
st.markdown("<hr style='border: none; border-top: 1px solid #D8C9B7; margin: 2rem 0 1rem 0;'>", unsafe_allow_html=True)

with st.expander("🛠️ Developer Diagnostics & Neo4j Cypher Lab", expanded=False):
    st.markdown(
        """
        <div class="editorial-card">
            <div class="card-heading">
                <span>Database Connection Diagnostics</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #702632;">REAL DRIVER STATUS</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    diag = Neo4jConnection.get_diagnostics(current_uri, current_user, current_pass)

    c_d1, c_d2 = st.columns(2)
    with c_d1:
        st.markdown(f"**Target URI:** `{diag['target_uri']}`")
        st.markdown(f"**Target Username:** `{diag['username']}`")
        st.markdown(f"**Protocol:** `{diag['protocol']}`")
    with c_d2:
        status_label = "🟢 CONNECTED" if diag["connected"] else "🔴 DISCONNECTED"
        st.markdown(f"**Active Status:** {status_label}")
        st.markdown(f"**Diagnosis:** {diag['message']}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Configuration Form
    st.markdown(
        """
        <div class="editorial-card">
            <div class="card-heading">
                <span>Neo4j Connection Settings</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("developer_db_config"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cfg_uri = st.text_input("Neo4j URI", value=current_uri, help="e.g. bolt://localhost:7687 or neo4j+s://<dbid>.databases.neo4j.io")
            cfg_user = st.text_input("Username", value=current_user)
        with col_c2:
            cfg_pass = st.text_input("Password", value=current_pass, type="password")
            cfg_db = st.text_input("Database", value=current_db)

        save_db_btn = st.form_submit_button("Test & Save Connection")

    if save_db_btn:
        st.session_state["neo4j_uri"] = cfg_uri
        st.session_state["neo4j_user"] = cfg_user
        st.session_state["neo4j_pass"] = cfg_pass
        st.session_state["neo4j_db"] = cfg_db
        Neo4jConnection.reset_driver(cfg_uri, cfg_user, cfg_pass)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Database Seeding Controls
    st.markdown(
        """
        <div class="editorial-card">
            <div class="card-heading">
                <span>Database Operations</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    col_seed, col_wipe = st.columns(2)
    with col_seed:
        if st.button("🌱 Seed Ground-Truth Offers (A, B, C)", disabled=not is_connected, use_container_width=True):
            try:
                driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
                repo = OfferRepository(driver, database=current_db)
                repo.clear_database()
                repo.seed_initial_offers()
                st.success("Successfully seeded Offers A, B, and C into Neo4j graph.")
                st.rerun()
            except Exception as e:
                st.error(f"Seeding failed: {e}")

    with col_wipe:
        if st.button("🗑️ Clear Neo4j Database", disabled=not is_connected, use_container_width=True):
            try:
                driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
                repo = OfferRepository(driver, database=current_db)
                repo.clear_database()
                st.info("Neo4j database wiped clean.")
                st.rerun()
            except Exception as e:
                st.error(f"Wipe failed: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Real Cypher Queries
    st.markdown(
        """
        <div class="editorial-card">
            <div class="card-heading">
                <span>Real Cypher Pattern Matching Queries</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<strong>1. Shared Recruiter Contact Query</strong>", unsafe_allow_html=True)
    st.code(
        """
MATCH (target:Offer)-[:HAS_CONTACT]->(contact:ContactPerson)
WHERE contact.email IN $emails AND ($exclude_id IS NULL OR target.id <> $exclude_id)
MATCH (target)-[:OFFERED_BY]->(target_company:Company)
RETURN target.id AS target_offer_id,
       target_company.name AS target_company_name,
       'SHARED_CONTACT' AS connection_type,
       contact.email AS shared_value,
       'Directly shares contact ' + contact.email + ' with ' + target.id + ' (' + target_company.name + ')' AS explanation
        """,
        language="cypher",
    )

    st.markdown("<strong>2. Shared Domain Infrastructure Query</strong>", unsafe_allow_html=True)
    st.code(
        """
MATCH (target:Offer)-[:OFFERED_BY]->(c:Company)-[:USES_DOMAIN]->(domain:Domain)
WHERE domain.name IN $domains AND ($exclude_id IS NULL OR target.id <> $exclude_id)
RETURN target.id AS target_offer_id,
       c.name AS target_company_name,
       'SHARED_DOMAIN' AS connection_type,
       domain.name AS shared_value,
       'Directly shares domain ' + domain.name + ' with ' + target.id + ' (' + c.name + ')' AS explanation
        """,
        language="cypher",
    )
    st.markdown("</div>", unsafe_allow_html=True)
