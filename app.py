"""
OfferLens AI - Streamlit Web Application.
Graph-powered job offer intelligence and relationship discovery using Neo4j and rule-based extraction.
"""

import streamlit as st
import pandas as pd
from typing import Optional

from src.config import Neo4jConfig
from src.db import Neo4jConnection
from src.repository import OfferRepository
from src.extractor import parse_job_offer_from_text
from src.visualizer import generate_interactive_graph_html
from src.models import JobOffer, Company, ContactPerson

st.set_page_config(
    page_title="OfferLens AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .tag-contact {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .tag-domain {
        background-color: #EDE9FE;
        color: #5B21B6;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar: Neo4j Connection Configuration
st.sidebar.title("⚙️ Neo4j Database Settings")

# Default values from .env
default_uri = Neo4jConfig.get_uri()
default_user = Neo4jConfig.get_username()
default_pass = Neo4jConfig.get_password()
default_db = Neo4jConfig.get_database()

with st.sidebar.form("neo4j_form"):
    neo4j_uri = st.text_input("Neo4j URI", value=default_uri, help="e.g. bolt://localhost:7687 or neo4j+s://<dbid>.databases.neo4j.io")
    neo4j_user = st.text_input("Username", value=default_user)
    neo4j_pass = st.text_input("Password", value=default_pass, type="password")
    neo4j_db = st.text_input("Database Name", value=default_db)
    submitted = st.form_submit_button("Connect & Save")

if submitted:
    st.session_state["neo4j_uri"] = neo4j_uri
    st.session_state["neo4j_user"] = neo4j_user
    st.session_state["neo4j_pass"] = neo4j_pass
    st.session_state["neo4j_db"] = neo4j_db
    # Reset cached driver
    Neo4jConnection.reset_driver(neo4j_uri, neo4j_user, neo4j_pass)

# Effective connection settings
current_uri = st.session_state.get("neo4j_uri", default_uri)
current_user = st.session_state.get("neo4j_user", default_user)
current_pass = st.session_state.get("neo4j_pass", default_pass)
current_db = st.session_state.get("neo4j_db", default_db)

# Test Connectivity
is_connected, status_msg = Neo4jConnection.test_connection(current_uri, current_user, current_pass)

if is_connected:
    st.sidebar.success("🟢 Neo4j Connected")
    st.sidebar.caption(f"Host: `{current_uri}`")
else:
    st.sidebar.error("🔴 Neo4j Disconnected")
    st.sidebar.caption(status_msg)

st.sidebar.markdown("---")
st.sidebar.subheader("Database Actions")

if st.sidebar.button("🌱 Seed Fictional Offers (A, B, C)", disabled=not is_connected):
    try:
        driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
        repo = OfferRepository(driver, database=current_db)
        repo.clear_database()
        repo.seed_initial_offers()
        st.sidebar.success("Seeded Offers A, B, and C successfully!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error seeding database: {e}")

if st.sidebar.button("🗑️ Clear Neo4j Graph", disabled=not is_connected):
    try:
        driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
        repo = OfferRepository(driver, database=current_db)
        repo.clear_database()
        st.sidebar.info("Graph database cleared.")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

with st.sidebar.expander("ℹ️ Beginner Setup Guide"):
    st.markdown("""
    **Using Neo4j AuraDB (Cloud Free Tier):**
    1. Go to [neo4j.com/cloud/platform/aura-graph-database](https://neo4j.com/cloud/platform/aura-graph-database/)
    2. Click **Start Free** and create an instance.
    3. Copy the `neo4j+s://...` URI and password.
    4. Paste into the sidebar and click **Connect & Save**.

    **Using Local Neo4j:**
    ```bash
    neo4j console
    # or via Homebrew:
    brew services start neo4j
    ```
    """)


# Main Page Header
st.markdown('<div class="main-title">OfferLens AI 🔍</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Graph-powered job offer intelligence, recruiter cross-referencing, and conflict detection using Neo4j</div>',
    unsafe_allow_html=True,
)

if not is_connected:
    st.warning(
        f"⚠️ **Neo4j is currently disconnected.**\n\n"
        f"Diagnostic: {status_msg}\n\n"
        f"Please start Neo4j locally or paste your free **Neo4j AuraDB** cloud credentials in the sidebar to run live Cypher queries."
    )

# Tab Navigation
tab_discovery, tab_visualizer, tab_extractor, tab_cypher = st.tabs([
    "🎯 Offer Discovery & Conflicts",
    "🕸️ Interactive Graph Visualizer",
    "📝 Rule-Based Extractor",
    "💡 Cypher Query Lab",
])

# ----------------------------------------------------
# TAB 1: Offer Discovery & Graph Matching
# ----------------------------------------------------
with tab_discovery:
    st.header("Graph-Based Offer Discovery")
    st.markdown(
        "OfferLens AI analyzes job offers to uncover hidden connections through "
        "**shared recruiter contacts** or **shared company domains**."
    )

    offers_list = []
    if is_connected:
        try:
            driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
            repo = OfferRepository(driver, database=current_db)
            offers_list = repo.list_offers()
        except Exception as e:
            st.error(f"Could not load offers from database: {e}")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Stored Offers")
        if not offers_list:
            st.info("No offers found in database. Click **'Seed Fictional Offers'** in the sidebar to load the test dataset.")
            selected_offer_id = None
        else:
            offer_options = {
                f"{o['id']} - {o['company_name']}": o['id'] for o in offers_list
            }
            selected_label = st.selectbox("Select Target Offer to Inspect:", list(offer_options.keys()))
            selected_offer_id = offer_options[selected_label]

            # Display selected offer details
            curr_offer = next(o for o in offers_list if o["id"] == selected_offer_id)
            with st.container(border=True):
                st.markdown(f"**Offer ID:** `{curr_offer['id']}`")
                st.markdown(f"**Company:** {curr_offer['company_name']}")
                st.markdown(f"**Role:** {curr_offer['title']}")
                st.markdown(f"**Domain:** `{curr_offer['domain'] or 'None'}`")
                st.markdown(f"**Salary:** {curr_offer['salary'] or 'N/A'}")
                st.markdown(f"**Contacts:** `{', '.join(curr_offer['contact_emails']) if curr_offer['contact_emails'] else 'None'}`")

    with col_right:
        st.subheader("Real Cypher Discovery Results")
        if selected_offer_id and is_connected:
            btn_discover = st.button("🚀 Run Neo4j Graph Discovery", type="primary")

            if btn_discover or st.session_state.get(f"ran_{selected_offer_id}"):
                st.session_state[f"ran_{selected_offer_id}"] = True
                try:
                    driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
                    repo = OfferRepository(driver, database=current_db)
                    connections = repo.find_related_offers(selected_offer_id)

                    if connections:
                        st.success(f"Discovered **{len(connections)}** related offer connection(s)!")
                        for conn in connections:
                            with st.container(border=True):
                                badge_class = "tag-contact" if conn.connection_type == "SHARED_CONTACT" else "tag-domain"
                                st.markdown(
                                    f"### 🔗 Connected to `{conn.target_offer_id}` ({conn.target_company_name})"
                                )
                                st.markdown(
                                    f"<span class='{badge_class}'>{conn.connection_type}</span> via **`{conn.shared_value}`**",
                                    unsafe_allow_html=True,
                                )
                                st.info(conn.explanation)
                    else:
                        st.warning(
                            f"**0 Connections Found.** `{selected_offer_id}` has no shared contacts or domains with other offers in the database.\n\n"
                            f"*(This is expected for Offer C / Summit Digital, which remains completely isolated through the seeded identifiers.)*"
                        )

                except Exception as e:
                    st.error(f"Error querying Neo4j: {e}")
        else:
            st.info("Select an offer and click 'Run Neo4j Graph Discovery' to query real relationships in Neo4j.")


# ----------------------------------------------------
# TAB 2: Interactive Graph Visualizer
# ----------------------------------------------------
with tab_visualizer:
    st.header("Neo4j Knowledge Graph Canvas")
    st.markdown("Visual representation of all Offers, Companies, Recruiter Contacts, and Domains stored in Neo4j.")

    if is_connected:
        try:
            driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
            repo = OfferRepository(driver, database=current_db)
            graph_data = repo.get_graph_elements()

            if not graph_data["nodes"]:
                st.info("The Neo4j database is empty. Click 'Seed Fictional Offers' in the sidebar.")
            else:
                st.caption(f"Loaded {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges from Neo4j.")
                html_canvas = generate_interactive_graph_html(
                    graph_data["nodes"],
                    graph_data["edges"],
                    height=540,
                )
                st.components.v1.html(html_canvas, height=560)
        except Exception as e:
            st.error(f"Failed to render graph: {e}")
    else:
        st.info("Connect Neo4j to visualize the graph live.")


# ----------------------------------------------------
# TAB 3: Rule-Based Offer Extractor (No AI API)
# ----------------------------------------------------
with tab_extractor:
    st.header("Rule-Based Entity Extractor")
    st.markdown("Zero-cost, deterministic extraction of offer entities using regex patterns and heuristics.")

    sample_texts = {
        "Offer A (NovaEdge)": (
            "Congratulations! NovaEdge Technologies is delighted to offer you the role of Senior Backend Engineer.\n"
            "Portal: novaedge-example.com\n"
            "Recruiter contact: recruit-a@example.test\n"
            "Compensation: $165,000 / year"
        ),
        "Offer B (BrightPath)": (
            "From: recruit-a@example.test\n"
            "Subject: Formal Offer - BrightPath AI\n"
            "We are thrilled to bring you onto the team at BrightPath AI (https://brightpath-example.com).\n"
            "Position: Machine Learning Engineer\n"
            "Salary: $180,000 / year"
        ),
        "Offer C (Summit Digital)": (
            "Company: Summit Digital\n"
            "Website: summit-example.com\n"
            "Contact: jobs@summit-example.com\n"
            "Role: Full Stack Developer\n"
            "Salary: $140,000 / year"
        ),
    }

    choice = st.selectbox("Load Sample Text or Type Custom:", ["Custom Input"] + list(sample_texts.keys()))
    default_input = sample_texts.get(choice, "")

    input_text = st.text_area("Job Offer Email or Text:", value=default_input, height=150)

    col1, col2 = st.columns([1, 1])

    with col1:
        custom_id = st.text_input("Assign Offer ID (Optional):", value="", placeholder="e.g. OFFER-D")

    if st.button("🔍 Extract Entities", type="primary"):
        if not input_text.strip():
            st.warning("Please enter job offer text first.")
        else:
            extracted = parse_job_offer_from_text(input_text, offer_id=custom_id or None)
            st.session_state["last_extracted"] = extracted

    if "last_extracted" in st.session_state:
        ext = st.session_state["last_extracted"]
        st.subheader("Extraction Result (Pydantic Validated)")

        c1, c2, c3 = st.columns(3)
        c1.metric("Company", ext.company.name)
        c2.metric("Domain", ext.company.domain or "None")
        c3.metric("Role / Title", ext.title)

        st.json(ext.model_dump())

        if is_connected:
            if st.button("💾 Save Extracted Offer to Neo4j Graph"):
                try:
                    driver = Neo4jConnection.get_driver(current_uri, current_user, current_pass)
                    repo = OfferRepository(driver, database=current_db)
                    repo.add_offer(ext)
                    st.success(f"Offer `{ext.id}` successfully persisted to Neo4j graph!")
                except Exception as e:
                    st.error(f"Error saving to Neo4j: {e}")


# ----------------------------------------------------
# TAB 4: Cypher Query Lab
# ----------------------------------------------------
with tab_cypher:
    st.header("Real Cypher Queries Explored")
    st.markdown("Here are the real Cypher queries implemented in OfferLens AI to identify graph relationships.")

    st.subheader("1. Shared Contact Discovery Query")
    st.code(
        """
MATCH (source:Offer {id: $offer_id})-[:HAS_CONTACT]->(contact:ContactPerson)<-[:HAS_CONTACT]-(target:Offer)
WHERE source <> target
MATCH (target)-[:OFFERED_BY]->(target_company:Company)
RETURN target.id AS target_offer_id,
       target_company.name AS target_company_name,
       'SHARED_CONTACT' AS connection_type,
       contact.email AS shared_value,
       'Offers ' + source.id + ' and ' + target.id + ' both list the shared contact: ' + contact.email AS explanation
        """,
        language="cypher",
    )

    st.subheader("2. Shared Domain Discovery Query")
    st.code(
        """
MATCH (source:Offer {id: $offer_id})-[:OFFERED_BY]->(c1:Company)-[:USES_DOMAIN]->(domain:Domain)<-[:USES_DOMAIN]-(c2:Company)<-[:OFFERED_BY]-(target:Offer)
WHERE source <> target
RETURN target.id AS target_offer_id,
       c2.name AS target_company_name,
       'SHARED_DOMAIN' AS connection_type,
       domain.name AS shared_value,
       'Offers ' + source.id + ' and ' + target.id + ' are connected through the shared domain: ' + domain.name AS explanation
        """,
        language="cypher",
    )

    st.subheader("3. Graph Schema Topology")
    st.markdown(
        """
        - `(:Offer)-[:OFFERED_BY]->(:Company)`
        - `(:Company)-[:USES_DOMAIN]->(:Domain)`
        - `(:Offer)-[:HAS_CONTACT]->(:ContactPerson)`
        - `(:Company)-[:HAS_CONTACT]->(:ContactPerson)`
        """
    )
