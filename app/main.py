from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app import graph_client
from app.models import ResolverTicket, SimilarTicket, TicketCreate, TicketOut
from app.triage import classify

app = FastAPI(
    title="Ticket Ops",
    description="Ticket triage/routing service — FastAPI + Neo4j scaffold.",
    version="0.1.0",
)


@app.on_event("shutdown")
def shutdown():
    graph_client.close_driver()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(payload: TicketCreate):
    result = classify(payload.subject, payload.description)
    ticket = graph_client.create_ticket(
        subject=payload.subject,
        description=payload.description,
        category=result.category,
        resolver=result.resolver,
    )
    return ticket


@app.get("/tickets/{ticket_id}", response_model=TicketOut)
def read_ticket(ticket_id: int):
    ticket = graph_client.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.get("/tickets/{ticket_id}/similar", response_model=list[SimilarTicket])
def read_similar_tickets(ticket_id: int):
    if graph_client.get_ticket(ticket_id) is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return graph_client.find_similar(ticket_id)


@app.get("/resolvers/{resolver_name}/tickets", response_model=list[ResolverTicket])
def read_tickets_for_resolver(resolver_name: str):
    return graph_client.tickets_for_resolver(resolver_name)


# Registered last so it only catches requests the routes above didn't match.
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
