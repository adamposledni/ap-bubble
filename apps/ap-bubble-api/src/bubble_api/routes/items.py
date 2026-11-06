"""L0 items as knowledge files cite them: one item (l0:123) or a range of ids (l0:504–519)."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from bubble_api.deps import Conn
from bubble_api.models import ItemDetailOut, ItemRangeOut
from bubble_core.log import get_logger
from bubble_core.queries.item_detail import ItemNotFound, get_item, item_range

router = APIRouter(prefix="/items")

logger = get_logger(__name__)


@router.get("")
def get_item_range(
    conn: Conn,
    first: Annotated[int, Query(alias="from")],
    last: Annotated[int, Query(alias="to")],
) -> ItemRangeOut:
    try:
        return ItemRangeOut.model_validate(item_range(conn, first, last))
    except ValueError as error:
        logger.debug("Rejected item range: %s", error)
        raise HTTPException(422, str(error)) from error


@router.get("/{item_id}")
def get_one_item(conn: Conn, item_id: int) -> ItemDetailOut:
    try:
        return ItemDetailOut.model_validate(get_item(conn, item_id))
    except ItemNotFound as error:
        raise HTTPException(404, str(error)) from error
