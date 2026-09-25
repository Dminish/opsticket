// Example queries worth running live in the Neo4j browser (http://localhost:7474) if you're
// asked to demonstrate this in an interview. Each shows a different reason to reach for a
// graph rather than a vector index: explicit relationships and multi-hop traversal.

// 1. All tickets routed to a given resolver, most recent first.
MATCH (t:Ticket)-[:ROUTED_TO]->(:Resolver {name: "network-team"})
RETURN t.id, t.subject, t.created_at
ORDER BY t.created_at DESC;

// 2. Tickets similar to a given ticket, ranked by similarity score.
MATCH (t:Ticket {id: 1})-[s:SIMILAR_TO]->(other:Ticket)
RETURN other.id, other.subject, s.score
ORDER BY s.score DESC;

// 3. Ticket volume per category per resolver — an aggregation query, good to show you're not
//    just doing single-hop lookups.
MATCH (t:Ticket)-[:BELONGS_TO]->(c:Category)
MATCH (t)-[:ROUTED_TO]->(r:Resolver)
RETURN c.name AS category, r.name AS resolver, count(t) AS ticket_count
ORDER BY ticket_count DESC;

// 4. Multi-hop: resolvers who tend to receive tickets similar to a given ticket's category —
//    the kind of query that's awkward in a relational schema but natural in a graph.
MATCH (t:Ticket {id: 1})-[:SIMILAR_TO]->(similar:Ticket)-[:ROUTED_TO]->(r:Resolver)
RETURN DISTINCT r.name AS resolver, count(similar) AS similar_ticket_count
ORDER BY similar_ticket_count DESC;

// 5. Categories with no dedicated resolver yet routed through them — a graph gap-detection
//    query, useful for the "how would you monitor agent/routing health" style question.
MATCH (c:Category)
WHERE NOT EXISTS {
  MATCH (:Ticket)-[:BELONGS_TO]->(c)
}
RETURN c.name AS unused_category;
