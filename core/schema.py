from typing import Literal, Optional
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """
    Structured business or system requirement.
    The type field captures whether it's functional, non-functional, a constraint, or an assumption.
    Priority remains 'unspecified' unless the client explicitly stated priority.
    """
    id: str  # R1, R2, ...
    title: str
    type: Literal["functional", "non_functional", "constraint", "assumption"]
    description: str
    priority: Literal["must", "should", "could", "wont", "unspecified"] = "unspecified"
    stakeholder: Optional[str] = None
    source_quote: str  # exact words from the input for traceability & anti-hallucination
    ambiguity_flags: list[str] = Field(default_factory=list)


class UserStory(BaseModel):
    """
    Agile user story following the INVEST criteria.
    Must link directly to a requirement_id.
    Requires at least 2 acceptance criteria formatted in Given / When / Then.
    """
    id: str  # US1, US2, ...
    requirement_id: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: list[str] = Field(min_length=2)  # Given / When / Then


class ActionItem(BaseModel):
    """
    Action item with accountability.
    Owner and due_date default to None if missing from transcript (never guessed).
    """
    task: str
    owner: Optional[str] = None
    due_date: Optional[str] = None
    source_quote: str


class Extraction(BaseModel):
    """
    Root contract between the LLM and the application.
    Contains all project artifacts derived from unstructured transcripts or emails.
    """
    summary: str
    requirements: list[Requirement]
    user_stories: list[UserStory]
    action_items: list[ActionItem]
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    status_update: str

