import os
import tempfile

import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

REPORT_FIELDS = [
    ("firearm", "Våpen"),
    ("component_bullet", "Kule"),
    ("component_powder", "Krutt"),
    ("component_primer", "Primer"),
    ("component_case", "Hylse"),
    ("load_recipe", "Ladning"),
    ("test_session", "Testresultat"),
    ("velocity", "Hastighet"),
    ("group_size", "Gruppe (mm)"),
    ("sd", "Standardavvik"),
    ("es", "Extreme Spread"),
    ("terrain", "Terrengprofil"),
    ("graph", "Graf"),
]


def generate_custom_pdf_report(data, selected_fields, pdf_path):
    """
    Genererer PDF-rapport basert på valgte felter.
    data: dict med alle mulige felter
    selected_fields: liste av feltnavn (str)
    pdf_path: filsti for PDF
    """
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 60, data.get("title", "Ballistikkrapport"))
    c.setFont("Helvetica", 12)
    y_pos = height - 100
    for field, label in REPORT_FIELDS:
        if field in selected_fields and field in data:
            value = data[field]
            if field == "graph" and isinstance(value, dict):
                # Lag graf
                fig, ax = plt.subplots()
                ax.plot(value["x"], value["y"], marker="o")
                ax.set_title(label)
                ax.set_xlabel(value.get("xlabel", "X"))
                ax.set_ylabel(value.get("ylabel", "Y"))
                tmp_img = tempfile.mktemp(suffix=".png")
                fig.savefig(tmp_img)
                plt.close(fig)
                img = ImageReader(tmp_img)
                c.drawImage(img, 40, y_pos - 320, width=500, height=300)
                os.remove(tmp_img)
                y_pos -= 340
            elif field == "terrain" and isinstance(value, list):
                c.drawString(40, y_pos, f"{label}:")
                y_pos -= 20
                for pt in value:
                    c.drawString(
                        60, y_pos, f"Lat: {pt[0]:.5f}, Lon: {pt[1]:.5f}, Elev: {pt[2]}"
                    )
                    y_pos -= 15
            else:
                c.drawString(40, y_pos, f"{label}: {value}")
                y_pos -= 20
    c.showPage()
    c.save()


# Eksempelbruk:
if __name__ == "__main__":
    test_data = {
        "title": "Custom Test",
        "firearm": "Tikka T3x",
        "component_bullet": "Lapua Scenar 155gr",
        "component_powder": "N150",
        "velocity": 820,
        "group_size": 18.5,
        "sd": 12.5,
        "es": 32,
        "terrain": [(59.91, 10.75, 120), (59.92, 10.76, 122)],
        "graph": {
            "x": [40, 41, 42, 43, 44],
            "y": [800, 810, 820, 830, 840],
            "xlabel": "Ladning (gr)",
            "ylabel": "Hastighet (fps)",
        },
    }
    selected = [
        "firearm",
        "component_bullet",
        "velocity",
        "group_size",
        "sd",
        "es",
        "terrain",
        "graph",
    ]
    generate_custom_pdf_report(test_data, selected, "custom_report.pdf")
    print("PDF-rapport generert: custom_report.pdf")
