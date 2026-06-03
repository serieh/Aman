from agent.config import PDF_DIR, EXCEL_DIR

def get_pdf_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    if not PDF_DIR.is_dir():
        return sources
    for pdf in sorted(PDF_DIR.glob("*.pdf")):
        key = pdf.stem.lower().replace(" ", "_")[:60]
        sources[key] = str(pdf.resolve())
    return sources

# def get_csv_sources() -> dict[str, str]:
#     """All Excel datasets under ShifaaAMHC/."""
#     dataset_dir = SOURCES_DIR / "ShifaaAMHC"
#     sources: dict[str, str] = {}
#     if not dataset_dir.is_dir():
#         return sources
#     for index, xlsx in enumerate(sorted(dataset_dir.glob("*.xlsx")), start=1):
#         key = f"consultations_{index}"
#         sources[key] = str(xlsx.resolve())
#     return sources