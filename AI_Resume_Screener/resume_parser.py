from io import BytesIO


def _parse_raw(raw, filename="", content_type=""):
    if not raw:
        return ""

    filename = (filename or "").lower()
    content_type = (content_type or "").lower()

    # Try PDF parsing first for typical resume uploads.
    if filename.endswith(".pdf") or "pdf" in content_type:
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(raw))
            pages = [(page.extract_text() or "") for page in reader.pages]
            text = "\n".join(pages).strip()
            if text:
                return text
        except Exception:
            pass

    try:
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text(file_storage):
    if file_storage is None:
        return ""
    raw = file_storage.read()
    file_storage.seek(0)
    return _parse_raw(raw, filename=file_storage.filename, content_type=file_storage.content_type)


def extract_text_from_path(path):
    try:
        with open(path, "rb") as file:
            raw = file.read()
    except OSError:
        return ""
    return _parse_raw(raw, filename=path, content_type="")
