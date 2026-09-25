// Sample tickets so /tickets/1/similar and /resolvers/{name}/tickets return something
// immediately, without needing to POST data first.

MERGE (network:Category {name: "network"})
MERGE (access:Category {name: "access"})
MERGE (hardware:Category {name: "hardware"})

MERGE (netTeam:Resolver {name: "network-team"})
MERGE (idTeam:Resolver {name: "identity-team"})
MERGE (hwTeam:Resolver {name: "hardware-team"})

CREATE (t1:Ticket {
  id: 1, subject: "VPN keeps dropping",
  description: "VPN disconnects every 10 minutes on Windows laptop, network connectivity unstable",
  created_at: "2026-09-20T09:00:00Z"
})
CREATE (t2:Ticket {
  id: 2, subject: "Cannot connect to office wifi",
  description: "Wifi connectivity drops intermittently, network keeps disconnecting on laptop",
  created_at: "2026-09-20T10:15:00Z"
})
CREATE (t3:Ticket {
  id: 3, subject: "Account locked after failed MFA",
  description: "Password login blocked, MFA code not accepted, account locked out",
  created_at: "2026-09-20T11:30:00Z"
})

MERGE (t1)-[:BELONGS_TO]->(network)
MERGE (t1)-[:ROUTED_TO]->(netTeam)
MERGE (t2)-[:BELONGS_TO]->(network)
MERGE (t2)-[:ROUTED_TO]->(netTeam)
MERGE (t3)-[:BELONGS_TO]->(access)
MERGE (t3)-[:ROUTED_TO]->(idTeam)

MERGE (t1)-[s:SIMILAR_TO]->(t2)
SET s.score = 0.42
MERGE (t2)-[s2:SIMILAR_TO]->(t1)
SET s2.score = 0.42;
