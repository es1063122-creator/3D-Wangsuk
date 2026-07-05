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

TARGET_KEYWORDS_IN_FILE = [
    "C-612",
    "가시설합본",
]

SEARCH_TEXTS = [
    "CORNER STRUT",
    "코너 스트러트",
    "경사 버팀",
]

NEAR_KEYWORDS = [
    "PILE", "P", "NO", "NO.", "H-PILE", "HPILE",
    "WALE", "띠장",
    "STRUT", "버팀", "버팀대",
    "ANCHOR", "앵커",
    "2H-300", "H-300",
    "EL", "G.L", "GL",
    "1단", "2단", "3단",
]

# 넓게 잡음. 전개도는 좌표 스케일이 커서 120000으로 부족할 수 있음
RADIUS_LIST = [150000.0, 300000.0, 600000.0]

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

def d2(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)

def is_target_file(rel):
    rel_norm = rel.replace("\\", "/")
    return any(k in rel_norm for k in TARGET_KEYWORDS_IN_FILE)

def is_corner_text(txt):
    up = txt.upper()
    return any(k.upper() in up for k in SEARCH_TEXTS)

def is_near_candidate(txt):
    up = txt.upper()
    return any(k.upper() in up for k in NEAR_KEYWORDS)

def main():
    reports = []

    dxf_files = []

    for root, dirs, files in os.walk(DXF_ROOT):
        for fname in files:
            if not fname.lower().endswith(".dxf"):
                continue

            path = os.path.join(root, fname)
            rel = os.path.relpath(path, DXF_ROOT)

            if is_target_file(rel):
                dxf_files.append(path)

    print("검색 대상 DXF:", len(dxf_files))
    for p in dxf_files:
        print(" -", os.path.relpath(p, DXF_ROOT))

    for path in dxf_files:
        rel = os.path.relpath(path, DXF_ROOT)
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

            corners = [t for t in texts if is_corner_text(t["text"])]

            for c in corners:
                item = {
                    "file": rel,
                    "corner_text": c,
                    "nearby_by_radius": {}
                }

                for radius in RADIUS_LIST:
                    nearby = []
                    for t in texts:
                        if not is_near_candidate(t["text"]):
                            continue

                        dist = d2(c["pos"], t["pos"])
                        if dist <= radius:
                            nearby.append({
                                "distance": dist,
                                "text": t["text"],
                                "layer": t["layer"],
                                "type": t["type"],
                                "pos": t["pos"],
                            })

                    nearby.sort(key=lambda x: x["distance"])
                    item["nearby_by_radius"][str(int(radius))] = nearby[:150]

                reports.append(item)

        except Exception as ex:
            print("오류:", rel, ex)

    out_json = os.path.join(OUT_DIR, "corner_strut_c612_wide_review.json")
    out_txt = os.path.join(OUT_DIR, "corner_strut_c612_wide_review.txt")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        for r in reports:
            f.write("=" * 140 + "\n")
            f.write(f"FILE   : {r['file']}\n")
            f.write(f"CORNER : {r['corner_text']['text']}\n")
            f.write(f"LAYER  : {r['corner_text']['layer']}\n")
            f.write(f"POS    : {r['corner_text']['pos']}\n")

            for radius, arr in r["nearby_by_radius"].items():
                f.write("-" * 140 + "\n")
                f.write(f"RADIUS {radius}\n")
                for n in arr:
                    f.write(f"{n['distance']:12.1f} | {n['layer']:25s} | {n['text']}\n")

    print("")
    print("완료")
    print("CORNER STRUT 발견 수:", len(reports))
    print(out_txt)

if __name__ == "__main__":
    main()
