import os
import re
from pathlib import Path

PROJECT_ROOT = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer")

DXF_ROOT = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "SourceDXF" / "unzipped" / "dxf"
OUT = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review" / "soil_layer_keyword_scan.txt"

KEYWORDS = [
    "매립층", "퇴적층", "풍화토", "풍화암", "연암", "보통암",
    "지층", "지질", "토층", "층후",
    "EL+", "EL-", "GH", "BH", "N치", "시추", "주상도",
    "굴착저면", "최종굴착", "계획고"
]

def read_text(path):
    for enc in ["cp949", "utf-8", "euc-kr", "latin1"]:
        try:
            return path.read_text(encoding=enc, errors="ignore")
        except:
            pass
    return ""

results = []

for p in DXF_ROOT.rglob("*.dxf"):
    raw = read_text(p)
    hits = []

    for kw in KEYWORDS:
        if kw in raw:
            hits.append(kw)

    el_hits = re.findall(r"EL\s*[\+\-]?\s*\d+\.\d+", raw, flags=re.IGNORECASE)
    if el_hits:
        hits.extend(el_hits[:20])

    if hits:
        results.append((p, sorted(set(hits)), len(set(hits))))

results.sort(key=lambda x: x[2], reverse=True)

with OUT.open("w", encoding="utf-8") as f:
    f.write("지층/토사/EL 관련 DXF 검색 결과\n")
    f.write("=" * 100 + "\n\n")

    for p, hits, score in results[:100]:
        f.write(f"[score {score}] {p.name}\n")
        f.write(f"path: {p}\n")
        f.write("hits: " + ", ".join(hits[:50]) + "\n")
        f.write("-" * 100 + "\n")

print("완료")
print(OUT)
print("matched files:", len(results))
