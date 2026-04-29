from flask import Flask, render_template, request, send_file
import pandas as pd
import pdfkit
import os
import platform

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── wkhtmltopdf config (auto-detects Windows vs Linux) ──
if platform.system() == "Windows":
    WKHTML_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=WKHTML_PATH)
else:
    config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")

# ── wkhtmltopdf options (fixes ProtocolUnknownError for local files) ──
PDF_OPTIONS = {
    "enable-local-file-access": "",
    "no-stop-slow-scripts": "",
    "encoding": "UTF-8",
    "page-size": "A4",
    "margin-top": "0mm",
    "margin-bottom": "10mm",
    "margin-left": "0mm",
    "margin-right": "0mm",
    "print-media-type": "",
}


def get_sheet_data(filepath):
    """Read all sheets from the Excel file and return structured data."""
    xl = pd.ExcelFile(filepath)
    sheets = []
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name)
        df = df.fillna("")
        columns = list(df.columns)
        records = df.to_dict(orient="records")
        sheets.append({
            "name": sheet_name,
            "columns": columns,
            "records": records,
        })
    return sheets


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("excel")
        if not file:
            return "No file uploaded"

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        try:
            sheets = get_sheet_data(filepath)
        except Exception as e:
            return f"Excel error: {e}"

        # Build absolute path to logo so wkhtmltopdf can load it via file://
        logo_path = os.path.join(app.root_path, "static", "Flexi_logo.png").replace("\\", "/")

        html = render_template("report.html", sheets=sheets, logo_path=logo_path)

        pdf_path = os.path.join(UPLOAD_FOLDER, "VPAT_Report.pdf")

        try:
            pdfkit.from_string(html, pdf_path, configuration=config, options=PDF_OPTIONS)
        except Exception as e:
            return f"PDF error: {e}"

        return send_file(pdf_path, as_attachment=True)

    return render_template("report.html", sheets=None)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, reloader_type="stat")
