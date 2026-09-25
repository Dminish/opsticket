# Ticket Ops — FastAPI + Neo4j + On-Premise CI/CD

A small scaffold built to close three specific gaps against the Helius "AI Engineer with Python" JD:
FastAPI, graph databases, and CI/CD to an on-premise/VM environment. It reuses the same
domain (IT ticket triage/routing) as your DanTech triage agent, so the concepts transfer directly
into interview answers, this isn't a generic tutorial project.

## What's here and why

| Gap | Where it's addressed |
|---|---|
| FastAPI | `app/main.py` — a real service with request validation (Pydantic), not a toy script |
| LLM pipeline | `app/triage.py` — LangChain + OpenAI (`gpt-4o-mini`) with structured output picks the category; routing to a resolver is a deterministic lookup, not the model's job |
| Data pipeline / ETL | `scripts/ingest_archive.py`, `data/archive/tickets.csv` — bulk-loads a legacy-shaped CSV export into the graph via the same classify pipeline the API uses |
| Graph databases | `graph/schema.cypher`, `graph/seed_data.cypher`, `graph/queries.cypher`, `app/graph_client.py` — tickets, categories and resolvers modelled as a graph, not a vector index |
| On-premise CI/CD | `.github/workflows/deploy.yml` — builds a Docker image and deploys it to a VM over SSH, not a PaaS `git push` |

## Architecture

```
Ticket (POST /tickets)
   │
   ├── triage.py classifies it (category + resolver)   <-- swap this for your LangGraph/Ollama pipeline
   │
   └── graph_client.py writes it into Neo4j as a graph:

   (Ticket)-[:BELONGS_TO]->(Category)
   (Ticket)-[:ROUTED_TO]->(Resolver)
   (Ticket)-[:SIMILAR_TO {score}]->(Ticket)
```

The `triage.py` classifier is intentionally a simple keyword-matcher right now, a placeholder.
The interview-relevant point isn't the classifier, it's the FastAPI/graph/CI-CD scaffolding around it.
If you have time, swap it for a trimmed-down version of your actual LangGraph + Ollama pipeline from
the triage agent project, that turns this from "a demo I built to prep" into "an extension of my
real production project," which is a stronger interview story.

## Run it locally (tonight, no VM needed yet)

Requires Docker Desktop (or Docker + Docker Compose) installed.

```bash
cp .env.example .env   # then fill in OPENAI_API_KEY
docker compose up --build
```

This starts two containers: the FastAPI app on `http://localhost:8000` and Neo4j
(browser UI at `http://localhost:7474`, default credentials from `.env`).

Seed the graph with sample data (`docker compose exec` addresses the container by service
name, so this works regardless of what you name the project folder):

```bash
docker compose exec -T neo4j cypher-shell -u neo4j -p changeme_password < graph/schema.cypher
docker compose exec -T neo4j cypher-shell -u neo4j -p changeme_password < graph/seed_data.cypher
```

Try it:

```bash
curl -X POST http://localhost:8000/tickets -H "Content-Type: application/json" \
  -d '{"subject": "VPN keeps dropping", "description": "VPN disconnects every 10 minutes on Windows laptop"}'

curl http://localhost:8000/tickets/1
curl http://localhost:8000/tickets/1/similar
curl http://localhost:8000/resolvers/network-team/tickets
```

Ingest the sample archival export (legacy-shaped CSV → classified → loaded into the graph):

```bash
pip install -r requirements.txt
python -m scripts.ingest_archive data/archive/tickets.csv
```

Interactive API docs (FastAPI gives you this for free, worth mentioning in the interview):
`http://localhost:8000/docs`

Run the tests:

```bash
pip install -r requirements.txt
python -m pytest
```

## Wiring up the on-premise CI/CD pipeline

`deploy.yml` builds the Docker image and pushes it to GitHub Container Registry (no extra
account needed, just the repo's built-in `GITHUB_TOKEN`), then SSHes into a VM and runs
`docker compose pull && docker compose up -d`. That's a real deploy-to-a-VM pipeline, not a
cloud PaaS `git push`.

To make it actually run, you need a VM. Cheapest realistic option tonight: a $4-6/month
DigitalOcean or Linode droplet (Ubuntu, Docker installed). Then in your GitHub repo, add these
secrets under Settings → Secrets and variables → Actions:

- `VM_HOST` — the droplet's IP address
- `VM_USER` — the SSH user (often `root` or a configured non-root user)
- `VM_SSH_KEY` — the private key that matches a public key added to the droplet

If you don't want to pay for a box tonight, you can still get full credit for understanding the
pattern: the workflow file itself, and being able to walk through what each step does and why
(build once, deploy the same artifact everywhere, no "works on my machine"), is most of what an
interviewer is actually checking for at this stage.

## What to say in the interview

- "I extended my triage agent concept into a small FastAPI service with a graph-modelled backend
  and a CI/CD pipeline that deploys to a VM over SSH, specifically because I didn't have that
  combination in my existing projects and wanted to close the gap rather than talk around it."
- Be ready to explain *why* a graph fits ticket routing (explicit relationships: ticket → category,
  ticket → resolver, ticket → similar ticket) versus *why* vector search fit the original triage
  agent (semantic similarity over free-text descriptions). Knowing when to use which is a stronger
  answer than just having touched both.
