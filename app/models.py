from datetime import datetime
from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)


class TicketOut(BaseModel):
    id: int
    subject: str
    description: str
    category: str
    resolver: str
    created_at: datetime


class SimilarTicket(BaseModel):
    id: int
    subject: str
    score: float


class ResolverTicket(BaseModel):
    id: int
    subject: str
    category: str
    created_at: datetime
