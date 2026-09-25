// Run once against a fresh Neo4j instance.
// Uniqueness constraints double as indexes in Neo4j, so lookups by these properties stay fast.

CREATE CONSTRAINT ticket_id_unique IF NOT EXISTS
FOR (t:Ticket) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT category_name_unique IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT resolver_name_unique IF NOT EXISTS
FOR (r:Resolver) REQUIRE r.name IS UNIQUE;
