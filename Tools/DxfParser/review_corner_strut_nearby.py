import os
import json
import ezdxf
import math

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

DXF_ROOT = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "SourceDXF",
    "unzipped"
)

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review"
)

os.makedirs(OUT_DIR, exist_ok=True)

TARGETS = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

RADIUS = 120000.0  # DXF 좌표 기준 주변 텍스트 검색 반경

def collect_virtual_entities(insert):
    out = []
    try:
        for e in insert.virtual_entities():
            out.append(e)
    except Exception:
        pass
    return out

def get_text(e):
    try:
        if e.dxftype() == "TEXT":
            return str(e.dxf.text).strip()
        if e.dxftype() == "MTEXT":
            return str(e.text).strip()
    except Exception:
        return ""
    return ""

def get_pos(e):
    try:
        p = e.dxf.insert
        return (float(p.x), float(p.y), float(p.z))
    except Exception:
        return (0.0, 0.0, 0.0)

def dist2(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx*dx + dy*dy)

def main():
    reports = []

    for root, dirs, files in os.walk(DXF_ROOT):
        for fname in files:
            if not fname.lower().endswith(".dxf"):
                continue

            rel = os.path.relpath(os.path.join(root, fname), DXF_ROOT)
            if not any(t in rel for t in TARGETS):
                continue

            path = os.path.join(root, fname)
            print("분석:", rel)

            try:
                doc = ezdxf.readfile(path)
                msp = doc.modelspace()

                ents = []
                for e in msp:
                    if e.dxftype() == "INSERT":
                        ents.extend(collect_virtual_entities(e))
                    else:
                        ents.append(e)

                texts = []
                for e in ents:
                    if e.dxftype() not in ["TEXT", "MTEXT"]:
                        continue

                    txt = get_text(e)
                    if not txt:
                        continue

                    texts.append({
                        "text": txt,
                        "layer": str(e.dxf.layer),
                        "type": e.dxftype(),
                        "pos": get_pos(e),
                    })

                corner_items = [t for t in texts if "CORNER STRUT" in t["text"].upper() or "코너 스트러트" in t["text"] or "경사 버팀" in t["text"]]

                for c in corner_items:
                    nearby = []
                    for t in texts:
                        d = dist2(c["pos"], t["pos"])
                        if d <= RADIUS:
                            nearby.append({
                                "distance": d,
                                "text": t["text"],
                                "layer": t["layer"],
                                "type": t["type"],
                                "pos": t["pos"],
                            })

                    nearby.sort(key=lambda x: x["distance"])

                    reports.append({
                        "file": rel,
                        "corner_text": c,
                        "nearby": nearby[:80],
                    })

            except Exception as ex:
                print("오류:", rel, ex)

    out_json = os.path.join(OUT_DIR, "corner_strut_nearby_texts.json")
    out_txt = os.path.join(OUT_DIR, "corner_strut_nearby_texts.txt")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        for r in reports:
            f.write("=" * 120 + "\n")
            f.write(f"FILE: {r['file']}\n")
            f.write(f"CORNER: {r['corner_text']['text']}\n")
            f.write(f"POS: {r['corner_text']['pos']}\n")
            f.write("-" * 120 + "\n")
            for n in r["nearby"]:
                f.write(f"{n['distance']:12.1f} | {n['layer']:20s} | {n['text']}\n")

    print("")
    print("완료")
    print("CORNER STRUT 발견 수:", len(reports))
    print(out_txt)

if __name__ == "__main__":
    main()
