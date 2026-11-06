"""Groups L0 items and L1 inputs into units, in the order Claude reads them."""

import sqlite3

from bubble_core.inputs import Input
from bubble_curator.changes import ChangedItem
from bubble_curator.render_chats import ChatTitles, chat_units
from bubble_curator.render_inputs import input_unit
from bubble_curator.render_mail import mail_units
from bubble_curator.render_records import record_unit
from bubble_curator.unit import Unit


def build_units(
    inputs: list[Input], items: list[ChangedItem], chat_titles: ChatTitles
) -> list[Unit]:
    units = [input_unit(i) for i in inputs]
    units += mail_units([i for i in items if i.kind == "mail"])
    units += chat_units([i for i in items if i.kind == "chat_message"], chat_titles)
    units += [record_unit(i) for i in items if i.kind in ("event", "task", "contact")]
    return sorted(units, key=lambda unit: unit.sort_key)


def chat_titles(conn: sqlite3.Connection) -> ChatTitles:
    rows = conn.execute(
        "SELECT account_id, external_id, title FROM l0_items "
        "WHERE source = 'teams_chats' AND kind = 'chat'"
    ).fetchall()
    return {(row["account_id"], row["external_id"]): row["title"] for row in rows}
