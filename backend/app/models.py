from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AppleSignalIngestRequest(BaseModel):
    device_id: str = Field(min_length=6, max_length=256)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signals: Dict[str, float]
    bundle_id: Optional[str] = Field(default=None, max_length=128)
    app_version: Optional[str] = Field(default=None, max_length=64)
    ios_version: Optional[str] = Field(default=None, max_length=64)
    attestation_token: Optional[str] = Field(default=None, max_length=4096)


class IngestResponse(BaseModel):
    accepted: int
    dropped: int
    message: str


class FeedMetrics(BaseModel):
    recovery: str
    focus: str
    balance: str
    action: str


class PublicFeedResponse(BaseModel):
    headline: str
    metrics: FeedMetrics
    updated_at: datetime


class PublicNoteSummary(BaseModel):
    title: str
    slug: str
    summary: str
    generated_at: datetime


class PublicNotesResponse(BaseModel):
    items: List[PublicNoteSummary]


class PublicNoteDetailResponse(BaseModel):
    title: str
    slug: str
    summary: str
    body_markdown: str
    meta_title: str
    meta_description: str
    social_quotes: List[str]
    generated_at: datetime


class RealtimeSessionRequest(BaseModel):
    model: Optional[str] = None
    voice: Optional[str] = None
    instructions: Optional[str] = None


class RealtimeSessionResponse(BaseModel):
    session: Dict[str, Any]


class RefreshResponse(BaseModel):
    refreshed: bool
    feed: PublicFeedResponse


class NotesIdeationRequest(BaseModel):
    context: str = Field(min_length=8, max_length=4000)
    count: int = Field(default=8, ge=3, le=15)


class NoteIdea(BaseModel):
    title: str
    thesis: str
    why_now: str
    format: str
    outline: List[str]


class NotesIdeationResponse(BaseModel):
    ideas: List[NoteIdea]


class NotesDraftRequest(BaseModel):
    brief: str = Field(min_length=20, max_length=12000)
    target_words: int = Field(default=1000, ge=500, le=1800)


class NotesDraftResponse(BaseModel):
    title: str
    slug: str
    summary: str
    body_markdown: str
    meta_title: str
    meta_description: str
    social_quotes: List[str]


class NotesSaveRequest(BaseModel):
    draft: NotesDraftResponse
    subdir: str = Field(default="notes-drafts", min_length=1, max_length=64)


class NotesSaveResponse(BaseModel):
    markdown_path: str
    json_path: str


class NotesPipelineRequest(BaseModel):
    context: str = Field(min_length=8, max_length=4000)
    count: int = Field(default=8, ge=3, le=15)
    draft_idea_index: int = Field(default=0, ge=0, le=14)
    target_words: int = Field(default=1000, ge=500, le=1800)
    save_to_disk: bool = True
    subdir: str = Field(default="notes-drafts", min_length=1, max_length=64)


class NotesPipelineResponse(BaseModel):
    ideas: List[NoteIdea]
    selected_brief: str
    draft: NotesDraftResponse
    saved: Optional[NotesSaveResponse] = None


class EditorialMemoryUpsertRequest(BaseModel):
    theme: str = Field(min_length=2, max_length=80)
    notes: str = Field(min_length=4, max_length=2000)


class EditorialMemoryItem(BaseModel):
    id: int
    theme: str
    notes: str
    updated_at: datetime


class EditorialMemoryResponse(BaseModel):
    items: List[EditorialMemoryItem]


class AppleIdentityVerifyRequest(BaseModel):
    identity_token: str = Field(min_length=40, max_length=10000)
    nonce: Optional[str] = Field(default=None, max_length=256)


class AppleIdentityVerifyResponse(BaseModel):
    valid: bool
    subject: str
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    audience: str
    issuer: str
    expires_at: datetime


class AppAttestChallengeRequest(BaseModel):
    device_id: str = Field(min_length=6, max_length=256)


class AppAttestChallengeResponse(BaseModel):
    challenge: str
    expires_at: datetime


class AppAttestVerifyRequest(BaseModel):
    device_id: str = Field(min_length=6, max_length=256)
    key_id: str = Field(min_length=6, max_length=512)
    bundle_id: str = Field(min_length=3, max_length=128)
    challenge: str = Field(min_length=16, max_length=256)
    attestation_object_b64: str = Field(min_length=32, max_length=100000)
    client_data_hash_b64: str = Field(min_length=16, max_length=2048)


class AppAttestVerifyResponse(BaseModel):
    accepted: bool
    mode: str
    device_hash: str
    key_id: str
    verified_at: datetime


class LabDailyBriefRequest(BaseModel):
    priorities: List[str] = Field(min_length=1, max_length=12)
    risks: List[str] = Field(default_factory=list, max_length=12)
    context: str = Field(default="", max_length=5000)


class LabDailyBriefResponse(BaseModel):
    headline: str
    top_actions: List[str]
    watchouts: List[str]
    communication_draft: str
    generated_at: datetime


class DecisionJournalEntryCreateRequest(BaseModel):
    title: str = Field(min_length=4, max_length=200)
    context: str = Field(min_length=6, max_length=6000)
    options: List[str] = Field(min_length=1, max_length=8)
    chosen_option: str = Field(min_length=1, max_length=500)
    rationale: str = Field(min_length=6, max_length=4000)
    follow_up_date: Optional[str] = Field(default=None, max_length=32)


class DecisionJournalEntry(BaseModel):
    id: int
    title: str
    context: str
    options: List[str]
    chosen_option: str
    rationale: str
    follow_up_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DecisionJournalListResponse(BaseModel):
    items: List[DecisionJournalEntry]


class EndpointToggleItem(BaseModel):
    path: str
    platform: str
    enabled: bool
    updated_at: Optional[datetime] = None


class EndpointToggleListResponse(BaseModel):
    items: List[EndpointToggleItem]


class EndpointToggleUpdateRequest(BaseModel):
    path: str = Field(min_length=3, max_length=128)
    enabled: bool


class OpenAIConnectRequest(BaseModel):
    api_key: str = Field(min_length=20, max_length=300)
    model: Optional[str] = Field(default=None, max_length=100)


class OpenAIConnectResponse(BaseModel):
    connected: bool
    model: str
    account_hint: str


class AppleConnectRequest(BaseModel):
    identity_token: str = Field(min_length=40, max_length=10000)
    nonce: Optional[str] = Field(default=None, max_length=256)


class AppleConnectResponse(BaseModel):
    connected: bool
    subject: str
    audience: str
    expires_at: datetime


class SquarespaceWebhookIngestResponse(BaseModel):
    accepted: bool
    event_type: str
    event_id: str


class SquarespaceEventItem(BaseModel):
    id: int
    event_id: str
    event_type: str
    website_id: str
    created_at: datetime
    received_at: datetime


class SquarespaceEventsResponse(BaseModel):
    items: List[SquarespaceEventItem]


class AgentTaskSpec(BaseModel):
    role: str = Field(min_length=2, max_length=80)
    objective: str = Field(min_length=6, max_length=2000)
    priority: int = Field(default=2, ge=0, le=3)


class ChiefDispatchRequest(BaseModel):
    mission: str = Field(min_length=10, max_length=4000)
    context: str = Field(default="", max_length=12000)
    tasks: List[AgentTaskSpec] = Field(default_factory=list, max_length=16)
    auto_execute: bool = False


class AgentTaskItem(BaseModel):
    id: int
    run_id: int
    role: str
    objective: str
    status: str
    priority: int
    output: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ChiefDispatchResponse(BaseModel):
    run_id: int
    mission: str
    status: str
    planner_summary: str
    tasks: List[AgentTaskItem]
    created_at: datetime


class AgentRunItem(BaseModel):
    id: int
    mission: str
    status: str
    planner_summary: str
    created_at: datetime
    updated_at: datetime


class AgentRunsResponse(BaseModel):
    items: List[AgentRunItem]


class AgentRunDetailResponse(BaseModel):
    run: AgentRunItem
    tasks: List[AgentTaskItem]


class AgentTaskUpdateRequest(BaseModel):
    status: str = Field(min_length=3, max_length=24)
    output: str = Field(default="", max_length=16000)
