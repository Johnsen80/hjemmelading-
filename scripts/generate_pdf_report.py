from __future__ import annotations

import os
import sys
import tempfile
from importlib import import_module
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

format_internal_ballistics_text = import_module(
    "src.utils.internal_ballistics"
).format_internal_ballistics_text


def _coerce_section_lines(value: Any) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (list, tuple)):
        lines: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                lines.append(text)
        return lines
    return []


def build_report_sections(data: dict[str, Any]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []

    stats = data.get("stats") or {}
    if isinstance(stats, dict) and stats:
        stat_lines = [f"{key}: {value}" for key, value in stats.items()]
        sections.append(("Statistikk", stat_lines))

    internal_ballistics = data.get("internal_ballistics_summary")
    if isinstance(internal_ballistics, dict):
        lines = format_internal_ballistics_text(internal_ballistics)
        if lines:
            heading = lines[0]
            sections.append((heading, lines[1:] or []))

    extra_sections = data.get("sections") or {}
    if isinstance(extra_sections, dict):
        for heading, value in extra_sections.items():
            lines = _coerce_section_lines(value)
            if lines:
                sections.append((str(heading), lines))

    return sections


def _load_reportlab_dependencies() -> tuple[tuple[float, float], Any, Any]:
    pagesizes = import_module("reportlab.lib.pagesizes")
    utils = import_module("reportlab.lib.utils")
    pdfgen = import_module("reportlab.pdfgen.canvas")
    return pagesizes.A4, utils.ImageReader, pdfgen


def _draw_section(
    pdf: Any,
    *,
    heading: str,
    lines: list[str],
    y_pos: float,
    width: float,
    height: float,
) -> float:
    if y_pos < 120:
        pdf.showPage()
        y_pos = height - 60
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_pos, heading)
    y_pos -= 18
    pdf.setFont("Helvetica", 10)
    for line in lines:
        if y_pos < 70:
            pdf.showPage()
            y_pos = height - 60
            pdf.setFont("Helvetica", 10)
        pdf.drawString(55, y_pos, str(line)[:120])
        y_pos -= 14
    return y_pos - 4


def generate_pdf_report(data: dict[str, Any], pdf_path: str) -> None:
    """
    Genererer PDF-rapport med statistikk, graf og valgfrie seksjoner.

    `data` kan inneholde:
    - `title`
    - `stats`: dict
    - `x`, `y`: plottdata
    - `internal_ballistics_summary`: summary fra internal_ballistics
    - `sections`: dict[str, str | list[str]]
    """
    A4, ImageReader, canvas = _load_reportlab_dependencies()
    fig, ax = plt.subplots()
    ax.plot(data["x"], data["y"], marker="o")
    ax.set_title(data.get("title", "Ballistikkrapport"))
    ax.set_xlabel(data.get("x_label", "Ladning (gr)"))
    ax.set_ylabel(data.get("y_label", "Hastighet (fps)"))

    tmp_img = tempfile.mktemp(suffix=".png")
    fig.savefig(tmp_img)
    plt.close(fig)

    pdf = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, height - 60, data.get("title", "Ballistikkrapport"))

    y_pos = height - 100
    for heading, lines in build_report_sections(data):
        y_pos = _draw_section(
            pdf,
            heading=heading,
            lines=lines,
            y_pos=y_pos,
            width=width,
            height=height,
        )

    graph_y = min(y_pos - 320, 200)
    if graph_y < 120:
        pdf.showPage()
        graph_y = height - 380
    img = ImageReader(tmp_img)
    pdf.drawImage(img, 40, graph_y, width=500, height=300)
    pdf.showPage()
    pdf.save()
    os.remove(tmp_img)


if __name__ == "__main__":
    test_data = {
        "title": "Ladder Test",
        "stats": {"Avg velocity": 820, "SD": 12.5, "ES": 32},
        "internal_ballistics_summary": {
            "title": "Internballistikk",
            "message": "Fyllrate 97.2%, kompresjon 1.03x, modellert forbrent andel 91%.",
            "metrics": [
                {"name": "Fyllrate", "value": "97.2%"},
                {"name": "Kompresjon", "value": "1.03x"},
            ],
        },
        "x": [40.0, 41.0, 42.0, 43.0, 44.0],
        "y": [800, 810, 820, 830, 840],
    }
    generate_pdf_report(test_data, "ballistics_report.pdf")
    print("PDF-rapport generert: ballistics_report.pdf")
