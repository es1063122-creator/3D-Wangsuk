import os
import json
import ezdxf
from collections import defaultdict

try:
    from ezdxf.disassemble import recursive_decompose
    HAS_RECURSIVE = True
except Exception:
    HAS_RECURSIVE = False

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

GA_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "SourceDXF",
    "unzipped",
    "dxf",
    "6.가시설공사"
)

OUT_TXT = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "development_strut_wale_level_compare.txt"
)

TARGET_FILES = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

TARGET_LAYERS = [
    "STRUT",
    "WALE",
    "C-WALE",
]

TEXT_KEYS = [
    "EL", "E.L", "GL", "G.L",
    "굴착", "심도", "시공하한선",
    "WALE", "띠장",
    "STRUT", "버팀", "CORNER STRUT",
    "ANCHOR", "앵커",
    "H-300", "2H-300",
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
    t = e.dxftype()

    try:
        if t == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            return [(float(s.x), float(s.y)), (float(en.x), float(en.y))]

        if t == "LWPOLYLINE":
            return [(float(v[0]), float(v[1])) for v in e.get_points()]

        if t == "POLYLINE":
            pts = []
            for v in e.vertices:
                loc = v.dxf.location
                pts.append((float(loc.x), float(loc.y)))
            return pts
    except Exception:
        return []

    return []

def get_mid_y_from_points(pts):
    if not pts:
        return None
    return sum([p[1] for p in pts]) / len(pts)

def get_mid_x_from_points(pts):
    if not pts:
        return None
    return sum([p[0] for p in pts]) / len(pts)

def get_length(pts):
    if len(pts) < 2:
        return 0.0
    a = pts[0]
    b = pts[-1]
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return (dx * dx + dy * dy) ** 0.5

def cluster_values(rows, tolerance=5000.0):
    rows = sorted(rows, key=lambda r: r["mid_y"])
    clusters = []

    for r in rows:
        y = r["mid_y"]

        if not clusters:
            clusters.append([r])
            continue

        avg = sum([x["mid_y"] for x in clusters[-1]]) / len(clusters[-1])

        if abs(y - avg) <= tolerance:
            clusters[-1].append(r)
        else:
            clusters.append([r])

    infos = []
    for c in clusters:
        avg_y = sum([x["mid_y"] for x in c]) / len(c)
        avg_x = sum([x["mid_x"] for x in c]) / len(c)
        avg_len = sum([x["length"] for x in c]) / len(c)
        min_x = min([x["mid_x"] for x in c])
        max_x = max([x["mid_x"] for x in c])

        infos.append({
            "avg_y": avg_y,
            "avg_x": avg_x,
            "avg_len": avg_len,
            "count": len(c),
            "min_x": min_x,
            "max_x": max_x,
        })

    infos.sort(key=lambda x: x["avg_y"], reverse=True)
    return infos

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
        return float(p.x), float(p.y)
    except Exception:
        return 0.0, 0.0

def has_text_key(txt):
    u = txt.upper()
    return any(k.upper() in u for k in TEXT_KEYS)

def main():
    files = []

    for fname in os.listdir(GA_DIR):
        if not fname.lower().endswith(".dxf"):
            continue
        if any(fname.startswith(t) for t in TARGET_FILES):
            files.append(fname)

    files.sort()

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("전개도 STRUT / WALE / C-WALE 높이 비교\n")
        f.write("=" * 120 + "\n\n")

        for fname in files:
            path = os.path.join(GA_DIR, fname)

            try:
                doc = ezdxf.readfile(path)
                ents = decompose_entities(doc.modelspace())

                by_layer = defaultdict(list)
                texts = []

                for e in ents:
                    layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""
                    etype = e.dxftype()

                    if layer.upper() in [x.upper() for x in TARGET_LAYERS]:
                        pts = get_points(e)
                        if len(pts) >= 2:
                            by_layer[layer.upper()].append({
                                "mid_y": get_mid_y_from_points(pts),
                                "mid_x": get_mid_x_from_points(pts),
                                "length": get_length(pts),
                                "type": etype,
                            })

                    if etype in ["TEXT", "MTEXT"]:
                        txt = get_text(e)
                        if txt and has_text_key(txt):
                            x, y = get_text_pos(e)
                            texts.append({
                                "text": txt,
                                "layer": layer,
                                "x": x,
                                "y": y,
                            })

                f.write("=" * 120 + "\n")
                f.write(f"FILE: {fname}\n\n")

                for layer_name in ["STRUT", "WALE", "C-WALE"]:
                    rows = by_layer.get(layer_name, [])
                    f.write(f"[{layer_name}]\n")
                    f.write(f"  entity count: {len(rows)}\n")

                    if rows:
                        clusters = cluster_values(rows, tolerance=5000.0)
                        f.write(f"  y cluster count: {len(clusters)}\n")

                        for idx, c in enumerate(clusters, start=1):
                            f.write(
                                f"  후보 {idx}단 | "
                                f"avg_y={c['avg_y']:.3f} | "
                                f"count={c['count']} | "
                                f"avg_len={c['avg_len']:.1f} | "
                                f"x_range={c['min_x']:.1f} ~ {c['max_x']:.1f}\n"
                            )
                    f.write("\n")

                f.write("[TEXT HITS]\n")
                # 너무 많으면 주요 80개만
                texts_sorted = sorted(texts, key=lambda x: (x["y"], x["x"]), reverse=True)
                for t in texts_sorted[:80]:
                    f.write(f"  y={t['y']:.1f} | x={t['x']:.1f} | {t['layer']} | {t['text']}\n")

                f.write("\n\n")

            except Exception as ex:
                f.write("=" * 120 + "\n")
                f.write(f"FILE: {fname}\n")
                f.write(f"ERROR: {ex}\n\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
