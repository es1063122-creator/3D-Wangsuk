import os
import json
import math
import ezdxf

try:
    from ezdxf.disassemble import recursive_decompose
    HAS_RECURSIVE = True
except Exception:
    HAS_RECURSIVE = False

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

OUT_TXT = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "c605_corner_strut_beam_bracing_review.txt"
)

OUT_JSON = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "c605_corner_strut_beam_bracing_review.json"
)

TEXT_KEYS = [
    "CORNER STRUT",
    "WALE",
    "STRUT",
    "H-300",
    "2H-300",
    "H-300x300x10x15",
    "H-300x200x9x14",
    "버팀",
    "띠장",
    "코너",
]

def decompose_entities(msp):
    if HAS_RECURSIVE:
        try:
            return list(recursive_decompose(msp))
        except Exception:
            pass

    result = []
    for e in msp:
        if e.dxftype() == "INSERT":
            try:
                result.extend(list(e.virtual_entities()))
            except Exception:
                pass
        else:
            result.append(e)
    return result

def get_points(e):
    try:
        if e.dxftype() == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            return [(float(s.x), float(s.y), float(s.z)), (float(en.x), float(en.y), float(en.z))]

        if e.dxftype() == "LWPOLYLINE":
            return [(float(v[0]), float(v[1]), 0.0) for v in e.get_points()]

        if e.dxftype() == "POLYLINE":
            pts = []
            for v in e.vertices:
                p = v.dxf.location
                pts.append((float(p.x), float(p.y), float(p.z)))
            return pts
    except Exception:
        return []

    return []

def mid_point(pts):
    x = sum(p[0] for p in pts) / len(pts)
    y = sum(p[1] for p in pts) / len(pts)
    z = sum(p[2] for p in pts) / len(pts)
    return x, y, z

def length_2d(pts):
    if len(pts) < 2:
        return 0.0
    a = pts[0]
    b = pts[-1]
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return math.sqrt(dx * dx + dy * dy)

def get_text(e):
    try:
        if e.dxftype() == "TEXT":
            return str(e.dxf.text).strip()
        if e.dxftype() == "MTEXT":
            return str(e.text).strip()
    except Exception:
        return ""
    return ""

def get_text_pos(e):
    try:
        p = e.dxf.insert
        return float(p.x), float(p.y), float(p.z)
    except Exception:
        return 0.0, 0.0, 0.0

def text_hit(txt):
    u = txt.upper()
    return any(k.upper() in u for k in TEXT_KEYS)

def dist(a, b):
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    return math.sqrt(dx * dx + dy * dy)

def main():
    doc = ezdxf.readfile(DXF_PATH)
    ents = decompose_entities(doc.modelspace())

    bracings = []
    struts = []
    texts = []

    for e in ents:
        try:
            layer = str(e.dxf.layer).strip()
        except Exception:
            layer = ""

        etype = e.dxftype()

        if layer.upper() in ["BEAM-BRACING", "STRUT"]:
            pts = get_points(e)
            if len(pts) >= 2:
                mx, my, mz = mid_point(pts)
                item = {
                    "layer": layer,
                    "type": etype,
                    "x": mx,
                    "y": my,
                    "z": mz,
                    "length": length_2d(pts),
                    "points": pts,
                }

                if layer.upper() == "BEAM-BRACING":
                    bracings.append(item)
                else:
                    struts.append(item)

        if etype in ["TEXT", "MTEXT"]:
            txt = get_text(e)
            if txt and text_hit(txt):
                x, y, z = get_text_pos(e)
                texts.append({
                    "layer": layer,
                    "text": txt,
                    "x": x,
                    "y": y,
                    "z": z,
                })

    # BEAM-BRACING 주변 텍스트/STRUT 찾기
    result = []

    for i, b in enumerate(bracings, start=1):
        near_texts = sorted(
            [
                dict(t, distance=dist(b, t))
                for t in texts
                if dist(b, t) < 80000
            ],
            key=lambda x: x["distance"]
        )[:20]

        near_struts = sorted(
            [
                dict(s, distance=dist(b, s))
                for s in struts
                if dist(b, s) < 80000
            ],
            key=lambda x: x["distance"]
        )[:20]

        result.append({
            "index": i,
            "beam_bracing": b,
            "near_texts": near_texts,
            "near_struts": near_struts,
        })

    os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-605 BEAM-BRACING / CORNER STRUT 주변 검토\n")
        f.write("=" * 120 + "\n\n")
        f.write(f"BEAM-BRACING count: {len(bracings)}\n")
        f.write(f"STRUT count: {len(struts)}\n\n")

        for r in result:
            b = r["beam_bracing"]
            f.write("=" * 120 + "\n")
            f.write(f"BEAM-BRACING #{r['index']}\n")
            f.write(f"  center: x={b['x']:.1f}, y={b['y']:.1f}\n")
            f.write(f"  length: {b['length']:.1f}\n")
            f.write("\n  주변 TEXT:\n")

            for t in r["near_texts"]:
                f.write(
                    f"    dist={t['distance']:.1f} | "
                    f"x={t['x']:.1f}, y={t['y']:.1f} | "
                    f"{t['layer']} | {t['text']}\n"
                )

            f.write("\n  주변 STRUT:\n")
            for s in r["near_struts"]:
                f.write(
                    f"    dist={s['distance']:.1f} | "
                    f"x={s['x']:.1f}, y={s['y']:.1f} | "
                    f"length={s['length']:.1f}\n"
                )

            f.write("\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
