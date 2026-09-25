"""
Ticket classification and routing.

An LLM (via LangChain + OpenAI) picks the category from a fixed vocabulary; routing that
category to a resolver queue is a deterministic lookup, not something the model decides. This
is the same split as the DanTech triage agent (classify, then route), just OpenAI instead of
Ollama and wired into a FastAPI endpoint / graph-backed store instead of Streamlit + Pinecone.

Requires OPENAI_API_KEY in the environment.
"""

from dataclasses import dataclass
from enum import Enum

from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class Category(str, Enum):
    network = "network"
    access = "access"
    hardware = "hardware"
    productivity_apps = "productivity-apps"
    general = "general"


RESOLVER_FOR_CATEGORY = {
    Category.network: "network-team",
    Category.access: "identity-team",
    Category.hardware: "hardware-team",
    Category.productivity_apps: "app-support-team",
    Category.general: "service-desk",
}

_SYSTEM_PROMPT = (
    "You triage IT support tickets. Read the subject and description and pick the single "
    "best-fitting category."
)


class _CategoryPick(BaseModel):
    category: Category


@dataclass
class Classification:
    category: str
    resolver: str


_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(
            _CategoryPick
        )
    return _classifier


def classify(subject: str, description: str) -> Classification:
    pick = _get_classifier().invoke(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", f"Subject: {subject}\nDescription: {description}"),
        ]
    )
    return Classification(category=pick.category.value, resolver=RESOLVER_FOR_CATEGORY[pick.category])
