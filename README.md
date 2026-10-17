# OfferLens AI 🔍

> **Graph-Powered Job Offer Intelligence, Recruiter Cross-Referencing & Overlap Detection**  
> Built for Hackathon MVP with **Python**, **Streamlit**, **Neo4j**, **Pydantic**, and **python-dotenv**. Zero paid AI API dependencies.

---

## 🎯 Overview

When candidates or organizations receive multiple job offers or recruiting inquiries, detecting overlaps, recruiters representing multiple companies, or shared domains is difficult with tabular data. 

**OfferLens AI** models job offers as an interconnected **knowledge graph** in Neo4j. By mapping offers, companies, recruiter emails, and domains as graph nodes, OfferLens AI executes real Cypher pattern-matching queries to instantly expose shared contacts and hidden linkages.

---
##
## 🧩 The Ground Truth Dataset

OfferLens AI comes seeded with three fictional job offers designed to test graph relationship queries:

| Offer ID | Company | Domain | Recruiter Contact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **OFFER-A** | NovaEdge Technologies | `novaedge-example.com` | `recruit-a@example.test` | 🔗 **Connected to B** (via shared recruiter) |
| **OFFER-B** | BrightPath AI | `brightpath-example.com` | `recruit-a@example.test` | 🔗 **Connected to A** (via shared recruiter) |
| **OFFER-C** | Summit Digital | `summit-example.com` | `jobs@summit-example.com` | 🛑 **Completely Isolated** (independent identifiers) |

- **Connection Truth:** `OFFER-A` and `OFFER-B` connect through their shared recruiter `recruit-a@example.test`.
- **Isolation Truth:** `OFFER-C` has zero connections to A or B.

---

## 🏗️ Architecture & Graph Topology

### Graph Schema
- `(:Offer {id, title, salary, location, raw_text})`
- `(:Company {name, domain})`
- `(:Domain {name})`
- `(:ContactPerson {email, name})`

### Relationships
- `(:Offer)-[:OFFERED_BY]->(:Company)`
- `(:Company)-[:USES_DOMAIN]->(:Domain)`
- `(:Offer)-[:HAS_CONTACT]->(:ContactPerson)`
- `(:Company)-[:HAS_CONTACT]->(:ContactPerson)`

---

## 💡 Real Cypher Queries Used

### 1. Discover Offers with Shared Recruiter Contacts
```cypher
MATCH (source:Offer {id: $offer_id})-[:HAS_CONTACT]->(contact:ContactPerson)<-[:HAS_CONTACT]-(target:Offer)
WHERE source <> target
MATCH (target)-[:OFFERED_BY]->(target_company:Company)
RETURN target.id AS target_offer_id,
       target_company.name AS target_company_name,
       'SHARED_CONTACT' AS connection_type,
       contact.email AS shared_value,
       'Offers ' + source.id + ' and ' + target.id + ' both list the shared contact: ' + contact.email AS explanation
```

### 2. Discover Offers with Shared Company Domains
```cypher
MATCH (source:Offer {id: $offer_id})-[:OFFERED_BY]->(c1:Company)-[:USES_DOMAIN]->(domain:Domain)<-[:USES_DOMAIN]-(c2:Company)<-[:OFFERED_BY]-(target:Offer)
WHERE source <> target
RETURN target.id AS target_offer_id,
       c2.name AS target_company_name,
       'SHARED_DOMAIN' AS connection_type,
       domain.name AS shared_value,
       'Offers ' + source.id + ' and ' + target.id + ' are connected through the shared domain: ' + domain.name AS explanation
```

---

## 🚀 Quickstart Guide (Step-by-Step for Beginners)

### 1. Set Up Environment
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/offerlens-ai.git
cd offerlens-ai

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Neo4j (Free AuraDB Cloud or Local)

#### Option A: Neo4j AuraDB (Recommended - 2 Minutes Setup, No Install)
1. Go to [Neo4j AuraDB Free Tier](https://neo4j.com/cloud/platform/aura-graph-database/).
2. Create a free AuraDB instance.
3. Download or save your credentials (`URI`, `neo4j`, `password`).
4. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```ini
   NEO4J_URI=neo4j+s://your-db-id.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_actual_password
   NEO4J_DATABASE=neo4j
   ```

#### Option B: Local Neo4j
```bash
# Start local Neo4j (if installed via Homebrew or Desktop)
neo4j console
# Or via brew services
brew services start neo4j
```

### 3. Seed & Verify the Graph via CLI
Run the automated verification script:
```bash
python scripts/seed_neo4j.py
```
This script will:
- Connect to Neo4j.
- Create uniqueness constraints.
- Seed Offers A, B, and C.
- Run real Cypher queries to verify A connects to B via `recruit-a@example.test`, and C is isolated.

### 4. Run Automated Pytest Suite
```bash
PYTHONPATH=. pytest tests/
```

### 5. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🌐 Live Deployment to Streamlit Community Cloud

1. Push this project to your GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of OfferLens AI MVP"
   git remote add origin https://github.com/YOUR_USERNAME/offerlens-ai.git
   git push -u origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub repository and select `app.py` as the main file.
4. In **Advanced Settings > Secrets**, add your Neo4j credentials:
   ```toml
   NEO4J_URI = "neo4j+s://<dbid>.databases.neo4j.io"
   NEO4J_USERNAME = "neo4j"
   NEO4J_PASSWORD = "<your_password>"
   NEO4J_DATABASE = "neo4j"
   ```
5. Click **Deploy**! Your app is now live for hackathon evaluation!

---

## 📁 Project Structure

```
offerlens-ai/
├── .env.example              # Template for Neo4j credentials
├── .gitignore                # Protects credentials and virtual environments
├── README.md                 # Complete documentation and guide
├── requirements.txt          # Python dependencies
├── src/
│   ├── __init__.py
│   ├── config.py             # Environment configuration loader
│   ├── models.py             # Pydantic schemas (Offer, Company, Contact, GraphConnection)
│   ├── extractor.py          # Rule-based entity extraction (no paid AI API)
│   ├── db.py                 # Neo4j Driver & connection lifecycle manager
│   ├── repository.py         # Real Cypher queries (insert, seed, discover, visualize)
│   └── visualizer.py         # Vis.js interactive network graph HTML renderer
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py     # Unit tests for rule-based extractor
│   └── test_neo4j_queries.py # Automated integration tests for Cypher queries
├── scripts/
│   └── seed_neo4j.py         # CLI database seed & verification runner
└── app.py                    # Streamlit web application
```

---

## 🛡️ Security Note
All credentials are kept strictly in `.env` and loaded via `python-dotenv`. The `.gitignore` file prevents `.env` from ever being pushed to version control.
