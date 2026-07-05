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
    "development_anchor_level_review.txt"
)

TARGET_FILES = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

ANCHOR_LAYER_KEYS = [
    "앵커",
    "ANCHOR",
    "ANCH",
    "@토목-앵커",
    "C-ANCH-FREE",
    "C-ANCH-BOND"
]

TEXT_KEYS = [
    "E/ANCHOR",
    "ANCHOR",
    "앵커",
    "제거식",
    "1단",
    "2단",
    "3단",
    "EL",
    "굴착심도",
    "WALE",
    "띠장"
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

def hit_any(value, keys):
    u = str(value).upper()
    return any(k.upper() in u for k in keys)

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
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return math.sqrt(dx * dx + dy * dy)

def mid_xy(pts):
    x = sum(p[0] for p in pts) / len(pts)
    y = sum(p[1] for p in pts) / len(pts)
    return x, y

def cluster_rows(rows, tolerance=5000.0):
    rows = sorted(rows, key=lambda r: r["mid_y"])
    clusters = []

    for r in rows:
        if not clusters:
            clusters.append([r])
            continue

        avg_y = sum(x["mid_y"] for x in clusters[-1]) / len(clusters[-1])

        if abs(r["mid_y"] - avg_y) <= tolerance:
            clusters[-1].append(r)
        else:
            clusters.append([r])

    infos = []
    for c in clusters:
        avg_y = sum(x["mid_y"] for x in c) / len(c)
        avg_len = sum(x["length"] for x in c) / len(c)
        min_x = min(x["mid_x"] for x in c)
        max_x = max(x["mid_x"] for x in c)

        infos.append({
            "avg_y": avg_y,
            "count": len(c),
            "avg_len": avg_len,
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

def main():
    files = []
    for fname in os.listdir(GA_DIR):
        if not fname.lower().endswith(".dxf"):
            continue
        if any(fname.startswith(t) for t in TARGET_FILES):
            files.append(fname)

    files.sort()

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-612~C-619 전개도 ANCHOR 단수/높이군 검토\n")
        f.write("=" * 130 + "\n\n")
        f.write("주의: 앵커 단수는 전개도 @토목-앵커 / E/ANCHOR 텍스트 / WALE 높이와 대조해서 확정해야 함.\n\n")

        for fname in files:
            path = os.path.join(GA_DIR, fname)

            try:
                doc = ezdxf.readfile(path)
                ents = decompose_entities(doc.modelspace())

                anchor_rows = []
                layer_counts = defaultdict(int)
                text_hits = []

                for e in ents:
                    layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""
                    etype = e.dxftype()

                    if hit_any(layer, ANCHOR_LAYER_KEYS):
                        layer_counts[layer] += 1

                        pts = get_points(e)
                        if len(pts) >= 2:
                            mx, my = mid_xy(pts)
                            ln = length_2d(pts)

                            # 너무 짧은 기호선도 많으므로 일단 300 이상만 높이군 분석
                            if ln >= 300:
                                anchor_rows.append({
                                    "layer": layer,
                                    "type": etype,
                                    "mid_x": mx,
                                    "mid_y": my,
                                    "length": ln,
                                })

                    if etype in ["TEXT", "MTEXT"]:
                        txt = get_text(e)
                        if txt and hit_any(txt, TEXT_KEYS):
                            x, y = get_text_pos(e)
                            text_hits.append({
                                "layer": layer,
                                "text": txt,
                                "x": x,
                                "y": y,
                            })

                clusters = cluster_rows(anchor_rows, tolerance=5000.0)

                f.write("=" * 130 + "\n")
                f.write(f"FILE: {fname}\n\n")

                f.write("[ANCHOR LAYER COUNTS]\n")
                for layer, cnt in sorted(layer_counts.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {layer:35s} {cnt}\n")

                f.write("\n[ANCHOR GEOMETRY]\n")
                f.write(f"  분석 대상 anchor rows length>=300: {len(anchor_rows)}\n")
                f.write(f"  y cluster count: {len(clusters)}\n")

                for i, c in enumerate(clusters, start=1):
                    f.write(
                        f"  후보 {i}단 | avg_y={c['avg_y']:.3f} | "
                        f"count={c['count']} | avg_len={c['avg_len']:.1f} | "
                        f"x_range={c['min_x']:.1f} ~ {c['max_x']:.1f}\n"
                    )

                f.write("\n[TEXT HITS - ANCHOR/단수/EL]\n")
                for t in sorted(text_hits, key=lambda x: (-x["y"], x["x"]))[:120]:
                    f.write(
                        f"  y={t['y']:.1f} | x={t['x']:.1f} | "
                        f"{t['layer']} | {t['text']}\n"
                    )

                f.write("\n\n")

            except Exception as ex:
                f.write("=" * 130 + "\n")
                f.write(f"FILE: {fname}\n")
                f.write(f"ERROR: {ex}\n\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
