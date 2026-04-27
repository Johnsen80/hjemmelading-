from __future__ import annotations

import argparse
import datetime as dt
import re
import sqlite3
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


def _excel_col_name(index: int) -> str:
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cell_xml(row_idx: int, col_idx: int, value) -> str:
    ref = f"{_excel_col_name(col_idx)}{row_idx}"
    if value is None:
        return f'<c r="{ref}"/>'
    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"><v>{value}</v></c>'
    text = str(value)
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'


def _sheet_xml(headers: list[str], rows: list[tuple]) -> str:
    xml_rows: list[str] = []
    header_cells = "".join(
        _cell_xml(1, col_idx + 1, header) for col_idx, header in enumerate(headers)
    )
    xml_rows.append(f'<row r="1">{header_cells}</row>')

    for row_idx, row in enumerate(rows, start=2):
        cells = "".join(
            _cell_xml(row_idx, col_idx + 1, value) for col_idx, value in enumerate(row)
        )
        xml_rows.append(f'<row r="{row_idx}">{cells}</row>')

    dimension_end = f"{_excel_col_name(max(len(headers), 1))}{max(len(rows) + 1, 1)}"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{dimension_end}"/>'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f"<sheetData>{''.join(xml_rows)}</sheetData>"
        "</worksheet>"
    )


def _sanitize_sheet_name(name: str, used: set[str]) -> str:
    cleaned = re.sub(r"[:\\\\/?*\\[\\]]", "_", name).strip() or "Sheet"
    cleaned = cleaned[:31]
    candidate = cleaned
    suffix = 1
    while candidate in used:
        extra = f"_{suffix}"
        candidate = f"{cleaned[:31-len(extra)]}{extra}"
        suffix += 1
    used.add(candidate)
    return candidate


def export_sqlite_to_excel(
    db_path: str | Path,
    output_path: str | Path,
    skip_empty: bool = False,
    include_summary: bool = False,
    only_tables: list[str] | None = None,
) -> dict[str, int]:
    db_path = Path(db_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    tables = [
        row["name"]
        for row in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    if only_tables:
        wanted = {name.strip() for name in only_tables if str(name).strip()}
        tables = [name for name in tables if name in wanted]

    used_sheet_names: set[str] = set()
    sheets: list[tuple[str, str]] = []
    table_count = 0
    row_count = 0

    table_summaries: list[tuple[str, int]] = []
    for table in tables:
        rows = list(cur.execute(f'SELECT * FROM "{table}"'))
        headers = [item[1] for item in cur.execute(f'PRAGMA table_info("{table}")')]
        table_summaries.append((table, len(rows)))
        if skip_empty and not rows:
            continue
        sheet_name = _sanitize_sheet_name(table, used_sheet_names)
        sheets.append((sheet_name, _sheet_xml(headers, [tuple(row) for row in rows])))
        table_count += 1
        row_count += len(rows)

    if include_summary:
        summary_headers = ["table_name", "row_count"]
        summary_rows = [
            (name, count)
            for name, count in table_summaries
            if (count or not skip_empty)
        ]
        sheets.insert(
            0,
            (
                _sanitize_sheet_name("summary", used_sheet_names),
                _sheet_xml(summary_headers, summary_rows),
            ),
        )
        table_count += 1

    con.close()

    content_types = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for idx in range(len(sheets)):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{idx + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )

    workbook_sheets = []
    workbook_rels = []
    for idx, (sheet_name, _) in enumerate(sheets, start=1):
        workbook_sheets.append(
            f'<sheet name="{escape(sheet_name)}" sheetId="{idx}" r:id="rId{idx}"/>'
        )
        workbook_rels.append(
            f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>'
        )

    created = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            f"{''.join(content_types)}"
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "docProps/core.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            "<dc:creator>Codex</dc:creator>"
            "<cp:lastModifiedBy>Codex</cp:lastModifiedBy>"
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>'
            "</cp:coreProperties>",
        )
        zf.writestr(
            "docProps/app.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
            'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            "<Application>Codex SQLite Export</Application>"
            "</Properties>",
        )
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<bookViews><workbookView/></bookViews>"
            f"<sheets>{''.join(workbook_sheets)}</sheets>"
            "</workbook>",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{''.join(workbook_rels)}"
            "</Relationships>",
        )
        for idx, (_, sheet_payload) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{idx}.xml", sheet_payload)

    return {"tables_exported": table_count, "rows_exported": row_count}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", type=Path)
    parser.add_argument("output_path", type=Path)
    parser.add_argument("--skip-empty", action="store_true")
    parser.add_argument("--include-summary", action="store_true")
    parser.add_argument("--only-tables", nargs="*")
    args = parser.parse_args()
    report = export_sqlite_to_excel(
        args.db_path,
        args.output_path,
        skip_empty=args.skip_empty,
        include_summary=args.include_summary,
        only_tables=args.only_tables,
    )
    print(report)


if __name__ == "__main__":
    main()
