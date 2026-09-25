"""
Neo4j access layer.

Graph model:
    (:Ticket {id, subject, description, created_at})
    (:Category {name})
    (:Resolver {name})

    (Ticket)-[:BELONGS_TO]->(Category)
    (Ticket)-[:ROUTED_TO]->(Resolver)
    (Ticket)-[:SIMILAR_TO {score}]->(Ticket)

SIMILAR_TO is computed here with a simple word-overlap (Jaccard) score against other tickets
in the same category. That's a placeholder for real embedding similarity, same idea as the
Pinecone retrieval in the original triage agent, just intentionally simple so this scaffold
has no model/API dependency. Swap it for a real embedding comparison if you have time.
"""

import os
from datetime import datetime, timezone

from neo4j import GraphDatabase

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "changeme_password")

SIMILARITY_THRESHOLD = 0.2

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def _word_set(text: str) -> set[str]:
    return {w.strip(".,!?").lower() for w in text.split() if len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def create_ticket(subject: str, description: str, category: str, resolver: str) -> dict:
    driver = get_driver()
    created_at = datetime.now(timezone.utc).isoformat()

    with driver.session() as session:
        ticket_id = session.execute_write(_next_ticket_id)

        session.execute_write(
            _write_ticket, ticket_id, subject, description, category, resolver, created_at
        )

        existing = session.execute_read(_tickets_in_category, category, exclude_id=ticket_id)
        new_words = _word_set(f"{subject} {description}")
        for other in existing:
            other_words = _word_set(f"{other['subject']} {other['description']}")
            score = _jaccard(new_words, other_words)
            if score >= SIMILARITY_THRESHOLD:
                session.execute_write(_link_similar, ticket_id, other["id"], score)

    return {
        "id": ticket_id,
        "subject": subject,
        "description": description,
        "category": category,
        "resolver": resolver,
        "created_at": created_at,
    }


def get_ticket(ticket_id: int) -> dict | None:
    driver = get_driver()
    with driver.session() as session:
        return session.execute_read(_read_ticket, ticket_id)


def find_similar(ticket_id: int) -> list[dict]:
    driver = get_driver()
    with driver.session() as session:
        return session.execute_read(_read_similar, ticket_id)


def tickets_for_resolver(resolver_name: str) -> list[dict]:
    driver = get_driver()
    with driver.session() as session:
        return session.execute_read(_read_for_resolver, resolver_name)


# --- transaction functions -------------------------------------------------

def _next_ticket_id(tx):
    result = tx.run("MATCH (t:Ticket) RETURN coalesce(max(t.id), 0) + 1 AS next_id")
    return result.single()["next_id"]


def _write_ticket(tx, ticket_id, subject, description, category, resolver, created_at):
    tx.run(
        """
        MERGE (c:Category {name: $category})
        MERGE (r:Resolver {name: $resolver})
        CREATE (t:Ticket {
            id: $ticket_id,
            subject: $subject,
            description: $description,
            created_at: $created_at
        })
        MERGE (t)-[:BELONGS_TO]->(c)
        MERGE (t)-[:ROUTED_TO]->(r)
        """,
        ticket_id=ticket_id,
        subject=subject,
        description=description,
        category=category,
        resolver=resolver,
        created_at=created_at,
    )


def _tickets_in_category(tx, category, exclude_id):
    result = tx.run(
        """
        MATCH (t:Ticket)-[:BELONGS_TO]->(:Category {name: $category})
        WHERE t.id <> $exclude_id
        RETURN t.id AS id, t.subject AS subject, t.description AS description
        """,
        category=category,
        exclude_id=exclude_id,
    )
    return [dict(record) for record in result]


def _link_similar(tx, ticket_id, other_id, score):
    tx.run(
        """
        MATCH (a:Ticket {id: $ticket_id}), (b:Ticket {id: $other_id})
        MERGE (a)-[s:SIMILAR_TO]->(b)
        SET s.score = $score
        MERGE (b)-[s2:SIMILAR_TO]->(a)
        SET s2.score = $score
        """,
        ticket_id=ticket_id,
        other_id=other_id,
        score=score,
    )


def _read_ticket(tx, ticket_id):
    result = tx.run(
        """
        MATCH (t:Ticket {id: $ticket_id})-[:BELONGS_TO]->(c:Category)
        MATCH (t)-[:ROUTED_TO]->(r:Resolver)
        RETURN t.id AS id, t.subject AS subject, t.description AS description,
               c.name AS category, r.name AS resolver, t.created_at AS created_at
        """,
        ticket_id=ticket_id,
    )
    record = result.single()
    return dict(record) if record else None


def _read_similar(tx, ticket_id):
    result = tx.run(
        """
        MATCH (t:Ticket {id: $ticket_id})-[s:SIMILAR_TO]->(other:Ticket)
        RETURN other.id AS id, other.subject AS subject, s.score AS score
        ORDER BY s.score DESC
        """,
        ticket_id=ticket_id,
    )
    return [dict(record) for record in result]


def _read_for_resolver(tx, resolver_name):
    result = tx.run(
        """
        MATCH (t:Ticket)-[:ROUTED_TO]->(:Resolver {name: $resolver_name})
        MATCH (t)-[:BELONGS_TO]->(c:Category)
        RETURN t.id AS id, t.subject AS subject, c.name AS category, t.created_at AS created_at
        ORDER BY t.created_at DESC
        """,
        resolver_name=resolver_name,
    )
    return [dict(record) for record in result]
