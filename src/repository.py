"""
Neo4j Repository for OfferLens AI.
Executes real Cypher graph queries to model and discover related offers.
"""

from typing import List, Dict, Any, Optional
from neo4j import Driver

from src.models import JobOffer, Company, ContactPerson, GraphConnection


# Cypher Queries
CYPHER_CREATE_CONSTRAINTS = [
    "CREATE CONSTRAINT offer_id_unique IF NOT EXISTS FOR (o:Offer) REQUIRE o.id IS UNIQUE;",
    "CREATE CONSTRAINT company_name_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE;",
    "CREATE CONSTRAINT domain_name_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE;",
    "CREATE CONSTRAINT contact_email_unique IF NOT EXISTS FOR (p:ContactPerson) REQUIRE p.email IS UNIQUE;",
]

CYPHER_INSERT_OFFER = """
MERGE (o:Offer {id: $offer_id})
SET o.title = $title,
    o.salary = $salary,
    o.location = $location,
    o.raw_text = $raw_text,
    o.company_name = $company_name

MERGE (c:Company {name: $company_name})
MERGE (o)-[:OFFERED_BY]->(c)

FOREACH (dom IN CASE WHEN $domain IS NOT NULL AND $domain <> '' THEN [$domain] ELSE [] END |
    MERGE (d:Domain {name: dom})
    MERGE (c)-[:USES_DOMAIN]->(d)
)

WITH o, c
UNWIND $contacts AS contact
    MERGE (p:ContactPerson {email: contact.email})
    ON CREATE SET p.name = contact.name
    MERGE (o)-[:HAS_CONTACT]->(p)
    MERGE (c)-[:HAS_CONTACT]->(p)
"""

CYPHER_FIND_BY_SHARED_CONTACT = """
MATCH (source:Offer {id: $offer_id})-[:HAS_CONTACT]->(contact:ContactPerson)<-[:HAS_CONTACT]-(target:Offer)
WHERE source <> target
MATCH (target)-[:OFFERED_BY]->(target_company:Company)
RETURN target.id AS target_offer_id,
       target_company.name AS target_company_name,
       'SHARED_CONTACT' AS connection_type,
       contact.email AS shared_value,
       'Offers ' + source.id + ' and ' + target.id + ' both list the shared contact: ' + contact.email AS explanation
"""

CYPHER_FIND_BY_SHARED_DOMAIN = """
MATCH (source:Offer {id: $offer_id})-[:OFFERED_BY]->(c1:Company)-[:USES_DOMAIN]->(domain:Domain)<-[:USES_DOMAIN]-(c2:Company)<-[:OFFERED_BY]-(target:Offer)
WHERE source <> target
RETURN target.id AS target_offer_id,
       c2.name AS target_company_name,
       'SHARED_DOMAIN' AS connection_type,
       domain.name AS shared_value,
       'Offers ' + source.id + ' and ' + target.id + ' are connected through the shared domain: ' + domain.name AS explanation
"""

CYPHER_FIND_BY_CONTACT_EMAILS = """
MATCH (target:Offer)-[:HAS_CONTACT]->(contact:ContactPerson)
WHERE contact.email IN $emails AND ($exclude_id IS NULL OR target.id <> $exclude_id)
MATCH (target)-[:OFFERED_BY]->(target_company:Company)
RETURN target.id AS target_offer_id,
       target_company.name AS target_company_name,
       'SHARED_CONTACT' AS connection_type,
       contact.email AS shared_value,
       'Directly shares contact ' + contact.email + ' with ' + target.id + ' (' + target_company.name + ')' AS explanation
"""

CYPHER_FIND_BY_DOMAINS = """
MATCH (target:Offer)-[:OFFERED_BY]->(c:Company)-[:USES_DOMAIN]->(domain:Domain)
WHERE domain.name IN $domains AND ($exclude_id IS NULL OR target.id <> $exclude_id)
RETURN target.id AS target_offer_id,
       c.name AS target_company_name,
       'SHARED_DOMAIN' AS connection_type,
       domain.name AS shared_value,
       'Directly shares domain ' + domain.name + ' with ' + target.id + ' (' + c.name + ')' AS explanation
"""


CYPHER_LIST_OFFERS = """
MATCH (o:Offer)-[:OFFERED_BY]->(c:Company)
OPTIONAL MATCH (o)-[:HAS_CONTACT]->(p:ContactPerson)
OPTIONAL MATCH (c)-[:USES_DOMAIN]->(d:Domain)
RETURN o.id AS id,
       o.title AS title,
       c.name AS company_name,
       d.name AS domain,
       o.salary AS salary,
       collect(DISTINCT p.email) AS contact_emails,
       o.raw_text AS raw_text
ORDER BY o.id ASC
"""

CYPHER_GET_ALL_GRAPH_ELEMENTS = """
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN collect(DISTINCT {
    id: id(n),
    labels: labels(n),
    name: coalesce(n.name, n.id, n.email, 'Unknown'),
    type: head(labels(n))
}) AS nodes,
collect(DISTINCT {
    source: id(n),
    target: id(m),
    type: type(r)
}) AS edges
"""


class OfferRepository:
    def __init__(self, driver: Driver, database: Optional[str] = "neo4j"):
        self.driver = driver
        self.database = database

    def init_schema(self) -> None:
        """Create uniqueness constraints for fast lookup and graph consistency."""
        with self.driver.session(database=self.database) as session:
            for constraint_query in CYPHER_CREATE_CONSTRAINTS:
                try:
                    session.run(constraint_query)
                except Exception:
                    # Older Neo4j versions might use different constraint syntax, continue gracefully
                    pass

    def add_offer(self, offer: JobOffer) -> None:
        """Insert a JobOffer and its graph entities into Neo4j."""
        params = {
            "offer_id": offer.id,
            "title": offer.title,
            "company_name": offer.company.name,
            "domain": offer.company.domain,
            "salary": offer.salary,
            "location": offer.location,
            "raw_text": offer.raw_text,
            "contacts": [{"email": c.email, "name": c.name} for c in offer.contacts],
        }
        with self.driver.session(database=self.database) as session:
            session.run(CYPHER_INSERT_OFFER, params)

    def seed_initial_offers(self) -> List[JobOffer]:
        """
        Seed the 3 required fictional offers:
        A: NovaEdge Technologies, novaedge-example.com, recruit-a@example.test
        B: BrightPath AI, brightpath-example.com, recruit-a@example.test
        C: Summit Digital, summit-example.com, jobs@summit-example.com
        """
        self.init_schema()

        offer_a = JobOffer(
            id="OFFER-A",
            title="Senior Backend Engineer",
            company=Company(name="NovaEdge Technologies", domain="novaedge-example.com"),
            contacts=[ContactPerson(name="Recruiter Alex", email="recruit-a@example.test")],
            salary="$165,000 / year",
            location="Remote",
            raw_text="NovaEdge Technologies (novaedge-example.com). Contact: recruit-a@example.test",
        )

        offer_b = JobOffer(
            id="OFFER-B",
            title="Machine Learning Engineer",
            company=Company(name="BrightPath AI", domain="brightpath-example.com"),
            contacts=[ContactPerson(name="Talent Team", email="recruit-a@example.test")],
            salary="$180,000 / year",
            location="San Francisco / Hybrid",
            raw_text="BrightPath AI (brightpath-example.com). Contact: recruit-a@example.test",
        )

        offer_c = JobOffer(
            id="OFFER-C",
            title="Full Stack Developer",
            company=Company(name="Summit Digital", domain="summit-example.com"),
            contacts=[ContactPerson(name="Hiring Desk", email="jobs@summit-example.com")],
            salary="$140,000 / year",
            location="Austin, TX",
            raw_text="Summit Digital (summit-example.com). Contact: jobs@summit-example.com",
        )

        for off in [offer_a, offer_b, offer_c]:
            self.add_offer(off)

        return [offer_a, offer_b, offer_c]

    def list_offers(self) -> List[Dict[str, Any]]:
        """List all offers currently stored in the Neo4j database."""
        with self.driver.session(database=self.database) as session:
            result = session.run(CYPHER_LIST_OFFERS)
            offers = []
            for record in result:
                offers.append(
                    {
                        "id": record["id"],
                        "title": record["title"],
                        "company_name": record["company_name"],
                        "domain": record["domain"],
                        "salary": record["salary"],
                        "contact_emails": [e for e in record["contact_emails"] if e],
                        "raw_text": record["raw_text"],
                    }
                )
            return offers

    def find_related_offers(self, offer_id: str) -> List[GraphConnection]:
        """
        Discover related offers using real Cypher queries via:
        1. Shared contacts (recruiter emails)
        2. Shared company domains
        """
        connections: List[GraphConnection] = []
        seen_keys = set()

        with self.driver.session(database=self.database) as session:
            # 1. Query shared contacts
            result_contacts = session.run(CYPHER_FIND_BY_SHARED_CONTACT, {"offer_id": offer_id})
            for record in result_contacts:
                key = (record["target_offer_id"], record["connection_type"], record["shared_value"])
                if key not in seen_keys:
                    seen_keys.add(key)
                    connections.append(
                        GraphConnection(
                            source_offer_id=offer_id,
                            target_offer_id=record["target_offer_id"],
                            target_company_name=record["target_company_name"],
                            connection_type=record["connection_type"],
                            shared_value=record["shared_value"],
                            explanation=record["explanation"],
                        )
                    )

            # 2. Query shared domains
            result_domains = session.run(CYPHER_FIND_BY_SHARED_DOMAIN, {"offer_id": offer_id})
            for record in result_domains:
                key = (record["target_offer_id"], record["connection_type"], record["shared_value"])
                if key not in seen_keys:
                    seen_keys.add(key)
                    connections.append(
                        GraphConnection(
                            source_offer_id=offer_id,
                            target_offer_id=record["target_offer_id"],
                            target_company_name=record["target_company_name"],
                            connection_type=record["connection_type"],
                            shared_value=record["shared_value"],
                            explanation=record["explanation"],
                        )
                    )

        return connections

    def find_related_by_entities(
        self,
        emails: List[str],
        domains: List[str],
        source_id: str = "NEW-OFFER",
        exclude_offer_id: Optional[str] = None,
    ) -> List[GraphConnection]:
        """
        Discover existing offers that share any of the extracted emails or domains.
        Allows immediate graph cross-referencing even for newly pasted offers.
        """
        connections: List[GraphConnection] = []
        seen_keys = set()

        with self.driver.session(database=self.database) as session:
            # 1. Search shared emails
            if emails:
                res_emails = session.run(
                    CYPHER_FIND_BY_CONTACT_EMAILS,
                    {"emails": emails, "exclude_id": exclude_offer_id},
                )
                for record in res_emails:
                    key = (record["target_offer_id"], record["connection_type"], record["shared_value"])
                    if key not in seen_keys:
                        seen_keys.add(key)
                        connections.append(
                            GraphConnection(
                                source_offer_id=source_id,
                                target_offer_id=record["target_offer_id"],
                                target_company_name=record["target_company_name"],
                                connection_type=record["connection_type"],
                                shared_value=record["shared_value"],
                                explanation=record["explanation"],
                            )
                        )

            # 2. Search shared domains
            valid_domains = [d for d in domains if d]
            if valid_domains:
                res_dom = session.run(
                    CYPHER_FIND_BY_DOMAINS,
                    {"domains": valid_domains, "exclude_id": exclude_offer_id},
                )
                for record in res_dom:
                    key = (record["target_offer_id"], record["connection_type"], record["shared_value"])
                    if key not in seen_keys:
                        seen_keys.add(key)
                        connections.append(
                            GraphConnection(
                                source_offer_id=source_id,
                                target_offer_id=record["target_offer_id"],
                                target_company_name=record["target_company_name"],
                                connection_type=record["connection_type"],
                                shared_value=record["shared_value"],
                                explanation=record["explanation"],
                            )
                        )

        return connections


    def get_graph_elements(self) -> Dict[str, Any]:
        """Fetch all graph nodes and edges for visualization."""
        with self.driver.session(database=self.database) as session:
            result = session.run(CYPHER_GET_ALL_GRAPH_ELEMENTS)
            record = result.single()
            if not record:
                return {"nodes": [], "edges": []}

            # Filter valid edges where target exists
            nodes = record["nodes"] or []
            edges = [e for e in (record["edges"] or []) if e.get("target") is not None]
            return {"nodes": nodes, "edges": edges}

    def clear_database(self) -> None:
        """Wipe all nodes and relationships."""
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n;")
