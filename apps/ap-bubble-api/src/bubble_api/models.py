"""Response models: the core's read models as camelCase JSON."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from bubble_core.inputs import Status


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class AgendaEventOut(ApiModel):
    key: str
    calendar: str | None
    title: str | None
    start: str
    end: str
    all_day: bool
    location: str | None
    recurring: bool


class OpenTaskOut(ApiModel):
    id: int
    list_name: str | None
    title: str | None
    notes: str | None
    due: str | None
    subtasks: list["OpenTaskOut"]


class InputFileOut(ApiModel):
    id: int
    name: str
    media_type: str | None
    size_bytes: int


class InputOut(ApiModel):
    id: int
    text: str | None
    status: Status
    error: str | None
    created_at: str
    processed_at: str | None
    files: list[InputFileOut]
