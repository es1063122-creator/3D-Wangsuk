import os
import re
from pathlib import Path

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

ROOT_DXF = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "SourceDXF",
    "unzipped",
    "dxf"
)

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review"
)

os.makedirs(OUT_DIR, exist_ok=True)

OUT_TXT = os.path.join(OUT_DIR, "floor_keyword_scan_all_dxf.txt")

KEYWORDS = [
    "601동", "602동", "603동", "604동", "605동", "606동", "607동", "608동", "609동",
    "610동", "611동", "612동", "613동", "614동",
    "지하주차장", "주차장",
    "펌프실", "펌프",
    "전기실", "발전기실", "전기계", "전기",
    "열교환실", "열교환",
    "PIT", "피트",
    "기계실", "EL+", "EL(+", "EL"
]

def read_text_any_encoding(path):
    encodings = ["cp949", "utf-8", "euc-kr", "latin1"]
    for enc in encodings:
        try:
            return Path(path).read_text(encoding=enc, errors="ignore")
        except:
            pass
    return ""

def normalize(s):
    s = s.replace("\\P", " ")
    s = re.sub(r"\\[A-Za-z0-9;,.+\-]+", "", s)
    s = s.replace("{", "").replace("}", "")
    return s

def main():
    results = []

    for root, dirs, files in os.walk(ROOT_DXF):
        for f in files:
            if not f.lower().endswith(".dxf"):
                continue

            path = os.path.join(root, f)
            raw = read_text_any_encoding(path)
            text = normalize(raw)

            hits = []
            for kw in KEYWORDS:
                if kw in text:
                    hits.append(kw)

            # 동명 패턴 추가 검색
            dong_hits = re.findall(r"60[1-9]동|61[0-4]동", text)
            hits.extend(dong_hits)

            # EL 패턴 검색
            el_hits = re.findall(r"EL\s*[\(\+]*\s*\+?\s*\d+\.\d+", text, flags=re.IGNORECASE)
            hits.extend(el_hits[:10])

            hits = sorted(set(hits))

            if hits:
                results.append({
                    "file": path,
                    "name": f,
                    "hits": hits,
                    "score": len(hits)
                })

    results.sort(key=lambda x: x["score"], reverse=True)

    with open(OUT_TXT, "w", encoding="utf-8") as out:
        out.write("전체 DXF 바닥/동자리/EL 키워드 검색 결과\n")
        out.write("=" * 100 + "\n\n")

        for r in results[:80]:
            out.write(f"[score {r['score']}] {r['name']}\n")
            out.write(f"path: {r['file']}\n")
            out.write("hits: " + ", ".join(r["hits"][:40]) + "\n")
            out.write("-" * 100 + "\n")

    print("완료")
    print(OUT_TXT)
    print("matched files:", len(results))

if __name__ == "__main__":
    main()
