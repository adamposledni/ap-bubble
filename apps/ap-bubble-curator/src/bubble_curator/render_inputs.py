"""L1 inputs as units: Adam's own notes and files, shown first in a batch."""

from bubble_core.inbox import path_of
from bubble_core.inputs import Input
from bubble_curator.unit import Unit, local_time


def input_unit(item: Input) -> Unit:
    lines = [item.text.strip()] if item.text else []
    if item.files:
        lines.append("Files (read them):")
        lines += [
            f"- {path_of(f.stored_path)} ({f.media_type or 'unknown type'})" for f in item.files
        ]
    heading = f"Input from Adam [input:{item.id}] — {local_time(item.created_at)}"
    return Unit(
        heading,
        "\n".join(lines),
        sort_key=f"0{item.id:08d}",
        input_ids=[item.id],
        file_count=len(item.files),
    )
