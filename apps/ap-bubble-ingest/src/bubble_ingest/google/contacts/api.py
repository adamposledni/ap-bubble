"""Google People API v1 over plain HTTP: changes of the contacts and of the other contacts."""

from dataclasses import dataclass
from typing import Any

import requests
from google.auth.transport.requests import AuthorizedSession

from bubble_core.log import get_logger
from bubble_ingest.google.http import Json, get_all_pages
from bubble_ingest.l0_sync import CursorExpired

BASE_URL = "https://people.googleapis.com/v1"
_PAGE_SIZE = 1000  # API maximum
_HTTP_BAD_REQUEST = 400  # current API: expired token comes with reason EXPIRED_SYNC_TOKEN
_HTTP_GONE = 410  # older API versions signal an expired token this way
_EXPIRED_REASON = "EXPIRED_SYNC_TOKEN"

# Everything a contact can hold, except profile-only fields (ageRanges, coverPhotos) and
# per-app clientData.
_PERSON_FIELDS = (
    "addresses,biographies,birthdays,calendarUrls,emailAddresses,events,externalIds,genders,"
    "imClients,interests,locales,locations,memberships,metadata,miscKeywords,names,nicknames,"
    "occupations,organizations,phoneNumbers,photos,relations,sipAddresses,skills,urls,userDefined"
)
# All that otherContacts.list allows for its default source (READ_SOURCE_TYPE_CONTACT).
_OTHER_CONTACT_FIELDS = "emailAddresses,metadata,names,phoneNumbers,photos"

logger = get_logger(__name__)


@dataclass(frozen=True)
class PeopleList:
    """A list endpoint of people: its path, the key of its items and its field mask."""

    path: str
    items_key: str
    mask_param: str
    mask: str


CONNECTIONS = PeopleList("people/me/connections", "connections", "personFields", _PERSON_FIELDS)
OTHER_CONTACTS = PeopleList("otherContacts", "otherContacts", "readMask", _OTHER_CONTACT_FIELDS)


@dataclass(frozen=True)
class PeopleChanges:
    people: list[Json]
    next_sync_token: str


def list_people(
    session: AuthorizedSession, people_list: PeopleList, sync_token: str | None
) -> PeopleChanges:
    """People changed since sync_token, or all of them when there is no token.

    Deleted people come as stubs with metadata.deleted (only on incremental fetches).
    Raises CursorExpired when Google no longer accepts the sync token.
    """
    # Every call repeats the same parameters: the API requires it for the sync token.
    params: dict[str, Any] = {
        people_list.mask_param: people_list.mask,
        "pageSize": _PAGE_SIZE,
        "requestSyncToken": "true",
    }
    if sync_token:
        params["syncToken"] = sync_token
    url = f"{BASE_URL}/{people_list.path}"
    try:
        people, last_page = get_all_pages(session, url, params, people_list.items_key)
    except requests.HTTPError as error:
        if _is_expired_token(error.response):
            raise CursorExpired(people_list.path) from error
        raise
    logger.debug("Fetched %d %s (incremental=%s)", len(people), people_list.path, bool(sync_token))
    return PeopleChanges(people, last_page["nextSyncToken"])


def _is_expired_token(response: requests.Response | None) -> bool:
    if response is None:
        return False
    if response.status_code == _HTTP_GONE:
        return True
    return response.status_code == _HTTP_BAD_REQUEST and _EXPIRED_REASON in response.text
