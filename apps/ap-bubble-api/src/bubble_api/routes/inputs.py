"""L1 input: queue text and/or files, list the queue, delete queued items, download files."""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse

from bubble_api.deps import Conn
from bubble_api.models import InputOut
from bubble_core.inputs import (
    InputNotFound,
    InputNotQueued,
    NewFile,
    add_input,
    delete_input,
    get_file,
    list_inputs,
)

router = APIRouter(prefix="/inputs")


@router.get("")
def get_inputs(conn: Conn) -> list[InputOut]:
    return [InputOut.model_validate(item) for item in list_inputs(conn)]


@router.post("", status_code=201)
def post_input(
    conn: Conn,
    text: Annotated[str | None, Form()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
) -> InputOut:
    new_files = [
        NewFile(name=upload.filename or "file", media_type=upload.content_type, content=upload.file)
        for upload in files or []
    ]
    try:
        return InputOut.model_validate(add_input(conn, text, new_files))
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.delete("/{input_id}", status_code=204)
def remove_input(conn: Conn, input_id: int) -> Response:
    try:
        delete_input(conn, input_id)
    except InputNotFound as error:
        raise HTTPException(404, str(error)) from error
    except InputNotQueued as error:
        raise HTTPException(409, str(error)) from error
    return Response(status_code=204)


@router.get("/files/{file_id}")
def download_file(conn: Conn, file_id: int) -> FileResponse:
    try:
        file, path = get_file(conn, file_id)
    except InputNotFound as error:
        raise HTTPException(404, str(error)) from error
    return FileResponse(path, media_type=file.media_type, filename=file.name)
