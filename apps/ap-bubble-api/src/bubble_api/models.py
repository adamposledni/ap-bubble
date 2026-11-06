"""Response models: the core's read models as camelCase JSON."""

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from bubble_core.accounts import Context
from bubble_core.inputs import Status
from bubble_core.knowledge import Folder


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class AgendaEventOut(ApiModel):
    key: str
    calendar: str | None
    context: Context
    title: str | None
    start: str
    end: str
    all_day: bool
    location: str | None
    recurring: bool


class OpenTaskOut(ApiModel):
    id: int
    list_name: str | None
    context: Context
    title: str | None
    notes: str | None
    due: str | None
    subtasks: list["OpenTaskOut"]


class JobStatusOut(ApiModel):
    job_name: str
    scope: str | None
    last_status: str
    last_started_at: str
    last_success_at: str | None
    last_error: str | None
    items_in_l0: int | None
    stale: bool


class JobRunOut(ApiModel):
    id: int
    job_name: str
    scope: str | None
    status: str
    started_at: str
    finished_at: str | None
    duration_seconds: float | None
    items_processed: int
    error: str | None
    dry_run: bool


class RunningJobOut(ApiModel):
    run: JobRunOut
    batch_current: int | None
    batch_total: int | None


class MonitorOut(ApiModel):
    jobs: list[JobStatusOut]
    runs: list[JobRunOut]
    running: list[RunningJobOut]
    queue: dict[str, int]


class BatchOut(ApiModel):
    name: str
    status: str
    summary: str | None
    num_turns: int | None
    duration_seconds: float | None
    cost_usd: float | None


class RunDetailOut(ApiModel):
    run: JobRunOut
    batches: list[BatchOut]


class InputFileOut(ApiModel):
    id: int
    name: str
    media_type: str | None
    size_bytes: int


class QuestionOut(ApiModel):
    id: str
    text: str


class InputOut(ApiModel):
    id: int
    text: str | None
    status: Status
    error: str | None
    created_at: str
    processed_at: str | None
    files: list[InputFileOut]


class SnippetPartOut(ApiModel):
    text: str
    match: bool


class KnowledgeHitOut(ApiModel):
    folder: Folder
    slug: str
    name: str
    tags: list[str]
    updated: str | None
    snippet: list[SnippetPartOut]


class KnowledgeSearchOut(ApiModel):
    total: int
    hits: list[KnowledgeHitOut]


class KnowledgeMetaOut(ApiModel):
    name: str
    aliases: list[str]
    emails: list[str]
    phones: list[str]
    tags: list[str]
    updated: str | None


class KnowledgeRefOut(ApiModel):
    folder: Folder
    slug: str
    name: str


class KnowledgeDocOut(ApiModel):
    folder: Folder
    slug: str
    meta: KnowledgeMetaOut
    body: str
    backlinks: list[KnowledgeRefOut]


class ItemAccountOut(ApiModel):
    email: str
    context: Context


class ItemSummaryOut(ApiModel):
    id: int
    source: str
    kind: str
    title: str | None
    starts_at: str | None
    ends_at: str | None
    deleted: bool
    account: ItemAccountOut
    changed_at: str


class ItemDetailOut(ItemSummaryOut):
    text: str | None
    payload: dict[str, Any]


class ItemRangeOut(ApiModel):
    items: list[ItemSummaryOut]
    truncated: bool
