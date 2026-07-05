import os
import re
import csv
import json
from pathlib import Path

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

DXF_PATH = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "SourceDXF",
    "unzipped",
    "dxf",
    "6.가시설공사",
    "C-605 굴착계획 평면도.dxf"
)

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review"
)

os.makedirs(OUT_DIR, exist_ok=True)

OUT_TXT = os.path.join(OUT_DIR, "c605_all_text_precise.txt")
OUT_CSV = os.path.join(OUT_DIR, "c605_all_text_precise.csv")
OUT_JSON = os.path.join(OUT_DIR, "floor_review_candidates_v2.json")

KEYWORDS = [
    "601", "602", "603", "604", "605", "606", "607", "608", "609",
    "610", "611", "612", "613", "614",
    "동", "주차장", "펌프", "전기", "발전", "열교환", "PIT", "피트", "기계",
    "EL", "EL+", "EL(+", "+31.34", "+31.54", "+33.24", "+33.54", "+35.04", "+35.09", "+35.44"
]

def clean_text(s):
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\\P", " ")
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\\[A-Za-z0-9;,.+\-/]+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def category_for(text):
    t = text.upper()

    if re.search(r"60[1-9]\s*동|61[0-4]\s*동", text):
        return "building"
    if "주차장" in text:
        return "parking"
    if "펌프" in text:
        return "pump"
    if "전기" in text or "발전" in text:
        return "electric"
    if "열교환" in text:
        return "heat"
    if "PIT" in t or "피트" in text:
        return "pit"
    if "기계" in text:
        return "machine"
    if "EL" in t or re.search(r"\+\d+\.\d+", text):
        return "el"
    return "etc"

def color_for(cat):
    return {
        "building": "#45F2B5",
        "parking": "#4DC9FF",
        "pump": "#FF9A3D",
        "electric": "#FFD84D",
        "heat": "#B06CFF",
        "pit": "#FF4D8D",
        "machine": "#40E0D0",
        "el": "#FFFFFF",
        "etc": "#CCCCCC",
    }.get(cat, "#CCCCCC")

def keep_text(s):
    if not s:
        return False
    for k in KEYWORDS:
        if k in s:
            return True
    if re.search(r"60[1-9]\s*동|61[0-4]\s*동", s):
        return True
    if re.search(r"EL\s*[\(\+]*\s*\+?\s*\d+\.\d+", s.upper()):
        return True
    if re.search(r"\+\d+\.\d+", s):
        return True
    return False

def extract_with_ezdxf():
    try:
        import ezdxf
    except Exception as e:
        print("ezdxf import 실패:", e)
        return []

    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()
    rows = []

    def add_row(text, x, y, layer, entity_type, source):
        label = clean_text(text)
        if not label:
            return
        rows.append({
            "text": label,
            "x": float(x),
            "y": float(y),
            "layer": layer or "",
            "entity_type": entity_type,
            "source": source
        })

    # 1) modelspace 직접 텍스트
    for e in msp:
        typ = e.dxftype()
        try:
            if typ == "TEXT":
                p = e.dxf.insert
                add_row(e.dxf.text, p.x, p.y, e.dxf.layer, typ, "modelspace")

            elif typ == "MTEXT":
                p = e.dxf.insert
                add_row(e.text, p.x, p.y, e.dxf.layer, typ, "modelspace")

            elif typ == "ATTRIB":
                p = e.dxf.insert
                add_row(e.dxf.text, p.x, p.y, e.dxf.layer, typ, "modelspace")

            elif typ == "INSERT":
                # block attribute
                if hasattr(e, "attribs"):
                    for a in e.attribs:
                        p = a.dxf.insert
                        add_row(a.dxf.text, p.x, p.y, a.dxf.layer, "ATTRIB", "insert_attrib")

                # virtual entities inside block
                try:
                    for ve in e.virtual_entities():
                        vtyp = ve.dxftype()
                        if vtyp == "TEXT":
                            p = ve.dxf.insert
                            add_row(ve.dxf.text, p.x, p.y, ve.dxf.layer, "BLOCK_TEXT", "virtual_block")
                        elif vtyp == "MTEXT":
                            p = ve.dxf.insert
                            add_row(ve.text, p.x, p.y, ve.dxf.layer, "BLOCK_MTEXT", "virtual_block")
                    pass
                except:
                    pass
        except Exception:
            pass

    return rows

def main():
    all_rows = extract_with_ezdxf()

    # 전체 텍스트 저장
    all_rows_sorted = sorted(all_rows, key=lambda r: (r["y"], r["x"]))

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["text", "x", "y", "layer", "entity_type", "source"])
        w.writeheader()
        for r in all_rows_sorted:
            w.writerow(r)

    # 후보만 필터
    candidates = []
    seen = set()

    for r in all_rows_sorted:
        label = r["text"]
        if not keep_text(label):
            continue

        key = (label, round(r["x"] / 100), round(r["y"] / 100))
        if key in seen:
            continue
        seen.add(key)

        cat = category_for(label)
        candidates.append({
            "label": label,
            "category": cat,
            "color": color_for(cat),
            "dxf_x": r["x"],
            "dxf_y": r["y"],
            "layer": r["layer"],
            "entity_type": r["entity_type"],
            "source": r["source"]
        })

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-605 전체 텍스트 정밀 추출 결과\n")
        f.write("=" * 120 + "\n")
        f.write(f"source: {DXF_PATH}\n")
        f.write(f"all text count: {len(all_rows_sorted)}\n")
        f.write(f"candidate count: {len(candidates)}\n\n")

        f.write("[후보 텍스트]\n")
        f.write("-" * 120 + "\n")
        for c in candidates:
            f.write(f"[{c['category']}] {c['label']} / x={c['dxf_x']:.1f}, y={c['dxf_y']:.1f}, layer={c['layer']}, type={c['entity_type']}, source={c['source']}\n")

        f.write("\n\n[전체 텍스트 상위 300개]\n")
        f.write("-" * 120 + "\n")
        for r in all_rows_sorted[:300]:
            f.write(f"{r['text']} / x={r['x']:.1f}, y={r['y']:.1f}, layer={r['layer']}, type={r['entity_type']}, source={r['source']}\n")

    result = {
        "name": "Wangsuk A-6BL Floor Review Candidates v2",
        "status": "C-605 DXF TEXT/MTEXT/ATTRIB/BLOCK 텍스트 정밀 추출 후보",
        "source_dxf": "C-605 굴착계획 평면도.dxf",
        "markers": candidates
    }

    Path(OUT_JSON).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("완료")
    print(OUT_TXT)
    print(OUT_CSV)
    print(OUT_JSON)
    print("all text count:", len(all_rows_sorted))
    print("candidate count:", len(candidates))

if __name__ == "__main__":
    main()
