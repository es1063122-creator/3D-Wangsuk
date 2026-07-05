import os
import json
import math
from collections import Counter

import ezdxf

try:
    from ezdxf.disassemble import recursive_decompose
    HAS_RECURSIVE = True
except Exception:
    HAS_RECURSIVE = False

ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"
DXF_DIR = os.path.join(
    ROOT,
    "Assets", "StreamingAssets", "WangsukDXF", "SourceDXF", "unzipped",
    "dxf", "6.가시설공사"
)

TARGET_FILES = [
    "C-612 굴착계획 전개도 (1).dxf",
    "C-613 굴착계획 전개도 (2).dxf",
    "C-614 굴착계획 전개도 (3).dxf",
    "C-615 굴착계획 전개도 (4).dxf",
    "C-616 굴착계획 전개도 (5).dxf",
    "C-617 굴착계획 전개도 (6).dxf",
    "C-618 굴착계획 전개도 (7).dxf",
    "C-619 굴착계획 전개도 (8).dxf",
]

LAYER_KEYS = [
    "ANCH", "ANCHOR", "EANCH", "E_ANCH", "EA",
    "그라우팅", "부상방지앙카", "GROUT"
]

TEXT_TYPES = {"TEXT", "MTEXT"}

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

def layer_match(layer_name):
    u = (layer_name or "").upper()
    for k in LAYER_KEYS:
        if k.upper() in u:
            return True
    return False

def get_points_2d(e):
    t = e.dxftype()
    pts = []

    try:
        if t == "LINE":
            pts = [
                (float(e.dxf.start.x), float(e.dxf.start.y)),
                (float(e.dxf.end.x), float(e.dxf.end.y)),
            ]

        elif t == "LWPOLYLINE":
            for p in e.get_points("xy"):
                pts.append((float(p[0]), float(p[1])))

        elif t == "POLYLINE":
            for v in e.vertices:
                pts.append((float(v.dxf.location.x), float(v.dxf.location.y)))

        elif t == "CIRCLE":
            cx = float(e.dxf.center.x)
            cy = float(e.dxf.center.y)
            r = float(e.dxf.radius)
            pts = [(cx - r, cy), (cx + r, cy), (cx, cy - r), (cx, cy + r)]

        elif t == "ARC":
            cx = float(e.dxf.center.x)
            cy = float(e.dxf.center.y)
            r = float(e.dxf.radius)
            pts = [(cx - r, cy), (cx + r, cy), (cx, cy - r), (cx, cy + r)]

        elif t in TEXT_TYPES:
            if hasattr(e.dxf, "insert"):
                pts = [(float(e.dxf.insert.x), float(e.dxf.insert.y))]
            elif hasattr(e.dxf, "location"):
                pts = [(float(e.dxf.location.x), float(e.dxf.location.y))]
    except Exception:
        return []

    return pts

def get_center_and_length(e):
    pts = get_points_2d(e)
    if not pts:
        return None

    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)

    length = 0.0
    if len(pts) >= 2:
        for i in range(len(pts) - 1):
            dx = pts[i + 1][0] - pts[i][0]
            dy = pts[i + 1][1] - pts[i][1]
            length += math.hypot(dx, dy)

    return {
        "x": cx,
        "y": cy,
        "length": length,
        "type": e.dxftype(),
        "layer": str(getattr(e.dxf, "layer", ""))
    }

def cluster_by_y(items, tol=250.0):
    if not items:
        return []

    items = sorted(items, key=lambda x: x["y"])
    clusters = []
    current = [items[0]]

    for it in items[1:]:
        avg_y = sum(v["y"] for v in current) / len(current)
        if abs(it["y"] - avg_y) <= tol:
            current.append(it)
        else:
            clusters.append(current)
            current = [it]

    clusters.append(current)
    return clusters

def main():
    out = {
        "files": []
    }

    print("굴착계획 전개도 앙카 단수 분석")
    print("=" * 120)

    for name in TARGET_FILES:
        path = os.path.join(DXF_DIR, name)
        if not os.path.exists(path):
            print(f"[없음] {name}")
            out["files"].append({
                "file": name,
                "exists": False
            })
            continue

        doc = ezdxf.readfile(path)
        ents = decompose_entities(doc.modelspace())

        layers = Counter()
        anchor_items = []
        texts = []

        for e in ents:
            layer = str(getattr(e.dxf, "layer", "")).strip()
            layers[layer] += 1

            info = get_center_and_length(e)
            if info is None:
                continue

            if e.dxftype() in TEXT_TYPES:
                txt = ""
                try:
                    txt = e.dxf.text if e.dxftype() == "TEXT" else e.text
                except Exception:
                    txt = ""
                texts.append({
                    "x": info["x"],
                    "y": info["y"],
                    "text": str(txt).strip(),
                    "layer": layer
                })

            if layer_match(layer):
                anchor_items.append(info)

        clusters = cluster_by_y(anchor_items, tol=250.0)

        print("\n" + "=" * 120)
        print(name)
        print(f"anchor candidate count: {len(anchor_items)}")
        print(f"y cluster count       : {len(clusters)}")

        file_result = {
            "file": name,
            "exists": True,
            "anchor_count": len(anchor_items),
            "cluster_count": len(clusters),
            "clusters": [],
            "layer_top": layers.most_common(40)
        }

        for idx, cluster in enumerate(clusters, 1):
            avg_y = sum(v["y"] for v in cluster) / len(cluster)
            xs = [v["x"] for v in cluster]
            lens = [v["length"] for v in cluster if v["length"] > 0]
            avg_len = (sum(lens) / len(lens)) if lens else 0.0

            near_texts = []
            for t in texts:
                if abs(t["y"] - avg_y) <= 600:
                    near_texts.append(t)

            near_texts = sorted(near_texts, key=lambda z: abs(z["y"] - avg_y))[:10]

            print(f"  후보 {idx}단 | avg_y={avg_y:.3f} | count={len(cluster)} | avg_len={avg_len:.1f} | x_range={min(xs):.1f} ~ {max(xs):.1f}")

            if near_texts:
                print("    주변 텍스트:")
                for t in near_texts[:6]:
                    print(f"      y={t['y']:.1f} | {t['layer']} | {t['text']}")

            file_result["clusters"].append({
                "index": idx,
                "avg_y": avg_y,
                "count": len(cluster),
                "avg_len": avg_len,
                "x_min": min(xs),
                "x_max": max(xs),
                "near_texts": near_texts[:10]
            })

        out["files"].append(file_result)

    out_path = os.path.join(ROOT, "anchor_level_review.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 120)
    print("결과 저장:", out_path)

if __name__ == "__main__":
    main()
