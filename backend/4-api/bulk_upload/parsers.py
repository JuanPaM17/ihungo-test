import csv
import io
from typing import Generator


def parse_csv(file) -> tuple[list[str], Generator[dict, None, None]]:
    text = file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    return list(fieldnames), (row for row in reader)


def parse_xlsx(file) -> tuple[list[str], Generator[dict, None, None]]:
    import openpyxl
    wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], iter([])
    headers = [str(h) if h is not None else "" for h in rows[0]]

    def _rows():
        for row in rows[1:]:
            yield {headers[i]: (str(v) if v is not None else "") for i, v in enumerate(row)}

    return headers, _rows()


def parse_file(file) -> tuple[list[str], Generator[dict, None, None]]:
    name = getattr(file, "name", "") or ""
    # Detect xlsx by extension or by PKZIP magic bytes (xlsx is a zip)
    if name.endswith(".xlsx"):
        return parse_xlsx(file)
    header = file.read(4)
    file.seek(0)
    if header == b"PK\x03\x04":
        return parse_xlsx(file)
    try:
        return parse_csv(file)
    except Exception:
        raise ValueError("Unsupported file format")
