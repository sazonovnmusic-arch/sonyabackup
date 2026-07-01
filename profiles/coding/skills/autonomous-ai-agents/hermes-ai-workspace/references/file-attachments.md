# File attachments in AI Workspace chat

## Storage layout

Files are stored under the Bridge directory so they are independent of Hermes `state.db`:

```
bridge/files/
├── coding/
│   └── <session_id>/
│       └── test-upload.txt
└── default/
    └── ...
```

## FastAPI endpoints

```python
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
import shutil, mimetypes

FILE_STORAGE = Path(__file__).parent / "files"

@app.post("/api/sessions/{profile}/{session_id}/files")
def upload_file(profile: str, session_id: str, file: UploadFile):
    d = FILE_STORAGE / profile / session_id
    d.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "untitled").name
    dest = d / safe_name
    with dest.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)
    mime = mimetypes.guess_type(str(dest))[0]
    return {
        "session_id": session_id,
        "filename": safe_name,
        "path": str(dest.relative_to(Path(__file__).parent)),
        "mime_type": mime or "application/octet-stream",
        "uploaded_at": time.time(),
    }

@app.get("/api/sessions/{profile}/{session_id}/files")
def list_files(profile: str, session_id: str):
    d = FILE_STORAGE / profile / session_id
    files = []
    for p in sorted(d.glob("*")):
        if p.is_file():
            files.append({
                "session_id": session_id,
                "filename": p.name,
                "path": str(p.relative_to(Path(__file__).parent)),
                "mime_type": mimetypes.guess_type(str(p))[0],
                "uploaded_at": p.stat().st_mtime,
            })
    return files

@app.get("/api/files/{profile}/{session_id}/{filename}")
def download_file(profile: str, session_id: str, filename: str):
    path = FILE_STORAGE / profile / session_id / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(path)
```

## Pitfall: always import `shutil` and `mimetypes`

The file endpoints rely on `shutil.copyfileobj` and `mimetypes.guess_type`. In an existing `main.py` that grew iteratively, it's easy to add the upload route but forget the imports; the runtime error will be `NameError: name 'shutil' is not defined`. Verify imports at the top of the bridge module whenever adding file handling.

## Sending a message with files

`ChatRequest` carries both `content` and `attached_files: list[str] | None` of filenames already uploaded to the session.

**Critical:** do not make `content` required with `min_length=1`. The UI may send a message that consists only of attached files, e.g. `{"content": "", "attached_files": ["notes.txt"]}`. If `content` is required or `attached_files` is missing from the model, the `/messages` endpoint will return `500 Internal Server Error` with a non-JSON body, and the UI will show `Unexpected token 'I', "Internal S"... is not valid JSON`.

```python
class ChatRequest(BaseModel):
    content: str = Field(default="")
    attached_files: list[str] | None = None
```

On send, the bridge builds a prompt:

```python
def _build_file_prompt(files: list[Path], text: str) -> tuple[str, Path | None]:
    image = next((f for f in files if _is_image(mimetypes.guess_type(str(f))[0])), None)
    chunks = [text] if text else []
    for f in files:
        mime, _ = mimetypes.guess_type(str(f))
        if _is_image(mime):
            continue
        content = _read_text_file(f, limit_bytes=100_000)
        if content:
            chunks.append(f"\n\n--- File: {f.name} ---\n{content}\n--- End file: {f.name} ---")
    return "\n".join(chunks), image
```

Then invoke Hermes:

```bash
hermes --profile <name> chat -q "<prompt_text>" --resume <session_id> --source api --image /path/to/image.png
```

## UI implementation notes

- Add a hidden `<input type="file" multiple>` triggered by a paperclip button.
- Handle `onDrop` on the chat container for drag-and-drop uploads.
- Show uploaded files as chips; let the user toggle which ones are attached to the next message.
- If no session is active, create one first with the file name as title, then upload.

## Limitations

- Hermes CLI only supports `--image` for vision, not generic `--file`. Textual files are inlined in the prompt.
- Very large files should be truncated to avoid context-window overflow.
