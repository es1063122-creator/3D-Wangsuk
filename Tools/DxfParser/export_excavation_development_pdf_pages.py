import os
import fitz  # PyMuPDF

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

PDF_PATH = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "SourcePDF",
    "남양주왕숙 A-6BL_토목_설계검증완료도서(도면).pdf"
)

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "pdf_pages_excavation_development"
)

KEYS = [
    "굴착계획 전개도",
    "제거식 E/ANCHOR",
    "E/ANCHOR",
    "WALE",
    "시공하한선"
]

os.makedirs(OUT_DIR, exist_ok=True)

doc = fitz.open(PDF_PATH)

hits = []

for i in range(len(doc)):
    page = doc[i]
    text = page.get_text("text")

    if any(k in text for k in KEYS) and "굴착계획 전개도" in text:
        hits.append(i)

print("굴착계획 전개도 후보 페이지:", [h + 1 for h in hits])

for page_index in hits:
    page = doc[page_index]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)

    out = os.path.join(OUT_DIR, f"page_{page_index+1:03d}_excavation_development.png")
    pix.save(out)
    print(out)

print("완료")
print(OUT_DIR)
