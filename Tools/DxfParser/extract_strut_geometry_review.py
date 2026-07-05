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
    "C-616", "C-617", "C-618", "C-619",
    "가시설합본"
]

STRUT_LAYER_KEYS = [
    "STRUT",
    "C-STRUT",
    "BEAM-BRACING",
    "버팀",
]

TEXT_KEYS = [
    "CORNER STRUT",
    "WALE",
    "2H-300",
    "H-300",
    "E/ANCHOR",
    "ANCHOR",
    "PILE",
    "NO",
    "EL",
    "G.L",
    "경사 버팀",
    "코너",
    "버팀대",
]

def is_target_file(rel):
    r = rel.replace("\\", "/")
    return any(t in r for t in TARGETS)

def collect_virtual_entities(insert):
    out = []
    try:
        for e in insert.virtual_entities():
            out.append(e)
    except Exception:
        pass
    return out

def is_strut_layer(layer):
    u = layer.upper()
    return any(k.upper() in u for k in STRUT_LAYER_KEYS)

def has_text_key(txt):
    u = txt.upper()
    return any(k.upper() in u for k in TEXT_KEYS)

def pnt(x, y, z=0):
    return {"x": float(x), "y": float(y), "z": float(z)}

def entity_points(e):
    t = e.dxftype()

    try:
        if t == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            return [pnt(s.x, s.y, s.z), pnt(en.x, en.y, en.z)]

        if t == "LWPOLYLINE":
            pts = []
            for v in e.get_points():
                pts.append(pnt(v[0], v[1], 0))
            return pts

        if t == "POLYLINE":
            pts = []
            for v in e.vertices:
                loc = v.dxf.location
                pts.append(pnt(loc.x, loc.y, loc.z))
            return pts

        if t == "ARC":
            c = e.dxf.center
            return [pnt(c.x, c.y, c.z)]

        if t == "CIRCLE":
            c = e.dxf.center
            return [pnt(c.x, c.y, c.z)]

    except Exception:
        pass

    return []

def get_text(e):
    try:
        if e.dxftype() == "TEXT":
            return str(e.dxf.text).strip()
        if e.dxftype() == "MTEXT":
            return str(e.text).strip()
    except Exception:
        return ""
    return ""

def get_insert(e):
    try:
        p = e.dxf.insert
        return pnt(p.x, p.y, p.z)
    except Exception:
        return pnt(0, 0, 0)

def main():
    report = {
        "strut_entities": [],
        "texts": [],
        "file_summary": {}
    }

    for root, dirs, files in os.walk(DXF_ROOT):
        for fname in files:
            if not fname.lower().endswith(".dxf"):
                continue

            path = os.path.join(root, fname)
            rel = os.path.relpath(path, DXF_ROOT)

            if not is_target_file(rel):
                continue

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

                strut_count = 0
                text_count = 0

                for e in ents:
                    layer = str(e.dxf.layer) if hasattr(e, "dxf") else ""
                    etype = e.dxftype()

                    if is_strut_layer(layer):
                        pts = entity_points(e)
                        if len(pts) > 0:
                            report["strut_entities"].append({
                                "file": rel,
                                "layer": layer,
                                "type": etype,
                                "points": pts,
                            })
                            strut_count += 1

                    if etype in ["TEXT", "MTEXT"]:
                        txt = get_text(e)
                        if txt and has_text_key(txt):
                            report["texts"].append({
                                "file": rel,
                                "layer": layer,
                                "type": etype,
                                "text": txt,
                                "position": get_insert(e),
                            })
                            text_count += 1

                report["file_summary"][rel] = {
                    "strut_entities": strut_count,
                    "texts": text_count
                }

            except Exception as ex:
                print("오류:", rel, ex)

    out_json = os.path.join(OUT_DIR, "strut_geometry_review.json")
    out_txt = os.path.join(OUT_DIR, "strut_geometry_review.txt")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("===== FILE SUMMARY =====\n")
        for file, s in report["file_summary"].items():
            f.write(f"{file}\n")
            f.write(f"  STRUT entities: {s['strut_entities']}\n")
            f.write(f"  Text hits     : {s['texts']}\n")

        f.write("\n\n===== TEXT HITS =====\n")
        for t in report["texts"]:
            f.write("=" * 100 + "\n")
            f.write(f"FILE : {t['file']}\n")
            f.write(f"LAYER: {t['layer']}\n")
            f.write(f"POS  : {t['position']}\n")
            f.write(f"TEXT : {t['text']}\n")

        f.write("\n\n===== STRUT ENTITY SAMPLES =====\n")
        for e in report["strut_entities"][:300]:
            f.write("=" * 100 + "\n")
            f.write(f"FILE : {e['file']}\n")
            f.write(f"LAYER: {e['layer']}\n")
            f.write(f"TYPE : {e['type']}\n")
            f.write(f"POINTS: {e['points'][:5]}\n")

    print("")
    print("완료")
    print("STRUT 도형 수:", len(report["strut_entities"]))
    print("관련 텍스트 수:", len(report["texts"]))
    print(out_txt)

if __name__ == "__main__":
    main()
