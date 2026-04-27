from scripts.generate_pdf_report import build_report_sections


def test_build_report_sections_includes_internal_ballistics_metrics():
    sections = build_report_sections(
        {
            "stats": {"Avg velocity": 820, "SD": 11.2},
            "internal_ballistics_summary": {
                "title": "Internballistikk",
                "message": "Fyllrate 97.2%, kompresjon 1.03x.",
                "metrics": [
                    {"name": "Fyllrate", "value": "97.2%"},
                    {"name": "Kompresjon", "value": "1.03x"},
                ],
            },
            "sections": {
                "Anbefaling": ["Verifiser i kald pipe", "Retest ved lav temp"]
            },
        }
    )

    assert sections[0][0] == "Statistikk"
    assert any(heading == "Internballistikk" for heading, _ in sections)
    assert any(
        any("Fyllrate: 97.2%" in line for line in lines)
        for heading, lines in sections
        if heading == "Internballistikk"
    )
    assert any(heading == "Anbefaling" for heading, _ in sections)


def test_build_report_sections_includes_internal_ballistics_context_lines():
    sections = build_report_sections(
        {
            "internal_ballistics_summary": {
                "title": "Internballistikk",
                "message": "Fyllrate 97.2%, kompresjon 1.03x.",
                "metrics": [],
                "context_lines": [
                    "H2O-grunnlag: 53.80 gr fra valgt hylse (4 grunnlagspunkter).",
                    "Trimlengde 48.77 mm fra valgt hylse er tilgjengelig i workflow-konteksten.",
                ],
            },
        }
    )

    assert any(
        any("53.80 gr fra valgt hylse" in line for line in lines)
        for heading, lines in sections
        if heading == "Internballistikk"
    )
    assert any(
        any("Trimlengde 48.77 mm" in line for line in lines)
        for heading, lines in sections
        if heading == "Internballistikk"
    )
