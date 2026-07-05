import os
import math
import ezdxf
from collections import defaultdict

try:
    from ezdxf.disassemble import recursive_decompose
    HAS_RECURSIVE = True
except Exception:
    HAS_RECURSIVE = False

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

DXF_DIR = os.path.join(
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
    "development_anchor_near_text_cad_review.txt"
)

TARGET_PREFIXES = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

ANCHOR_LAYER_KEYS = [
    "@토목-앵커",
    "앵커",
    "ANCHOR",
    "ANCH",
    "C-ANCH-FREE",
    "C-ANCH-BOND",
]

WALE_LAYER_KEYS = [
    "WALE",
    "C-WALE",
    "띠장",
]

TEXT_KEYS = [
    "1단", "2단", "3단",
    "E/ANCHOR", "ANCHOR", "앵커", "제거식",
    "WALE", "띠장",
    "굴착심도", "시공하한선", "EL",
    "단면"
]

def hit_any(value, keys):
    u = str(value).upper()
    return any(k.upper() in u for k in keys)

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
            return [(float(s.x), float(s.y)), (float(en.x), float(en.y))]

        if e.dxftype() == "LWPOLYLINE":
            return [(float(v[0]), float(v[1])) for v in e.get_points()]

        if e.dxftype() == "POLYLINE":
            pts = []
            for v in e.vertices:
                p = v.dxf.location
                pts.append((float(p.x), float(p.y)))
            return pts
    except Exception:
        return []

    return []

def length_2d(pts):
    if len(pts) < 2:
        return 0.0
    a = pts[0]
    b = pts[-1]
    return math.hypot(b[0] - a[0], b[1] - a[1])

def mid_xy(pts):
    return (
        sum(p[0] for p in pts) / len(pts),
        sum(p[1] for p in pts) / len(pts)
    )

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

def cluster_by_y(rows, tolerance=5000.0):
    rows = sorted(rows, key=lambda r: r["y"])
    clusters = []

    for r in rows:
        if not clusters:
            clusters.append([r])
            continue

        avg_y = sum(x["y"] for x in clusters[-1]) / len(clusters[-1])

        if abs(r["y"] - avg_y) <= tolerance:
            clusters[-1].append(r)
        else:
            clusters.append([r])

    result = []
    for c in clusters:
        result.append({
            "avg_y": sum(x["y"] for x in c) / len(c),
            "count": len(c),
            "min_x": min(x["x"] for x in c),
            "max_x": max(x["x"] for x in c),
            "avg_len": sum(x["len"] for x in c) / len(c),
            "items": c,
        })

    result.sort(key=lambda r: r["avg_y"], reverse=True)
    return result

def near_texts(cx, cy, texts, dx_limit=25000.0, dy_limit=12000.0, max_count=15):
    near = []

    for t in texts:
        dx = abs(t["x"] - cx)
        dy = abs(t["y"] - cy)

        if dx <= dx_limit and dy <= dy_limit:
            score = dx + dy * 3.0
            near.append((score, dx, dy, t))

    near.sort(key=lambda x: x[0])
    return near[:max_count]

def main():
    files = []
    for fname in os.listdir(DXF_DIR):
        if not fname.lower().endswith(".dxf"):
            continue
        if any(fname.startswith(p) for p in TARGET_PREFIXES):
            files.append(fname)

    files.sort()

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-612~C-619 CAD 직접 분석: 앵커 도형 주변 문자/WALE 대조\n")
        f.write("=" * 150 + "\n\n")
        f.write("판정 기준: 앵커 y군 주변에 2단/3단 앵커 문자가 붙는지, 아니면 WALE/굴착/단면명인지 확인.\n\n")

        for fname in files:
            path = os.path.join(DXF_DIR, fname)
            doc = ezdxf.readfile(path)
            ents = decompose_entities(doc.modelspace())

            anchors = []
            wales = []
            texts = []
            layer_counts = defaultdict(int)

            for e in ents:
                etype = e.dxftype()
                layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""

                if etype in ["LINE", "LWPOLYLINE", "POLYLINE"]:
                    pts = get_points(e)
                    if len(pts) < 2:
                        continue

                    ln = length_2d(pts)
                    if ln < 300:
                        continue

                    x, y = mid_xy(pts)

                    if hit_any(layer, ANCHOR_LAYER_KEYS):
                        layer_counts[layer] += 1
                        anchors.append({
                            "x": x,
                            "y": y,
                            "len": ln,
                            "layer": layer,
                            "type": etype,
                        })

                    if hit_any(layer, WALE_LAYER_KEYS):
                        wales.append({
                            "x": x,
                            "y": y,
                            "len": ln,
                            "layer": layer,
                            "type": etype,
                        })

                elif etype in ["TEXT", "MTEXT"]:
                    txt = get_text(e)
                    if not txt:
                        continue

                    if hit_any(txt, TEXT_KEYS):
                        x, y = get_text_pos(e)
                        texts.append({
                            "x": x,
                            "y": y,
                            "text": txt,
                            "layer": layer,
                        })

            anchor_clusters = cluster_by_y(anchors, tolerance=5000.0)
            wale_clusters = cluster_by_y(wales, tolerance=5000.0)

            f.write("=" * 150 + "\n")
            f.write(f"FILE: {fname}\n\n")

            f.write("[ANCHOR LAYER COUNTS length>=300]\n")
            for k, v in sorted(layer_counts.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {k:35s} {v}\n")

            f.write("\n[ANCHOR Y CLUSTERS]\n")
            f.write(f"  anchor cluster count = {len(anchor_clusters)}\n")
            for i, c in enumerate(anchor_clusters, start=1):
                f.write(
                    f"  A{i} | avg_y={c['avg_y']:.1f} | count={c['count']} | "
                    f"avg_len={c['avg_len']:.1f} | x={c['min_x']:.1f}~{c['max_x']:.1f}\n"
                )

            f.write("\n[WALE Y CLUSTERS]\n")
            f.write(f"  wale cluster count = {len(wale_clusters)}\n")
            for i, c in enumerate(wale_clusters, start=1):
                f.write(
                    f"  W{i} | avg_y={c['avg_y']:.1f} | count={c['count']} | "
                    f"avg_len={c['avg_len']:.1f} | x={c['min_x']:.1f}~{c['max_x']:.1f}\n"
                )

            f.write("\n[ANCHOR CLUSTER 주변 문자]\n")

            for i, c in enumerate(anchor_clusters, start=1):
                cx = (c["min_x"] + c["max_x"]) * 0.5
                cy = c["avg_y"]

                f.write(f"\n  --- A{i} 주변 문자 / anchor avg_y={cy:.1f} ---\n")

                near = near_texts(cx, cy, texts)

                if not near:
                    f.write("    주변 문자 없음\n")
                else:
                    for score, dx, dy, t in near:
                        f.write(
                            f"    dy={dy:8.1f} dx={dx:9.1f} | "
                            f"y={t['y']:.1f} x={t['x']:.1f} | "
                            f"{t['layer']} | {t['text']}\n"
                        )

            f.write("\n[2단/3단 포함 문자 전체]\n")
            found_stage = False
            for t in sorted(texts, key=lambda r: (-r["y"], r["x"])):
                if "2단" in t["text"] or "3단" in t["text"]:
                    found_stage = True
                    f.write(
                        f"  y={t['y']:.1f} x={t['x']:.1f} | "
                        f"{t['layer']} | {t['text']}\n"
                    )

            if not found_stage:
                f.write("  2단/3단 문자 없음\n")

            f.write("\n\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
