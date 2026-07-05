import os
import json
import math
import re
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

ANCHOR_TEXT_KEYS = [
    "ANCHOR", "E/ANCHOR", "EANCHOR", "E.A", "E/A",
    "앵커", "앙카", "제거식"
]

def clean_text(s):
    s = str(s or "")
    s = s.replace("\\P", " ")
    s = re.sub(r"\\[A-Za-z0-9;,.+\-/]+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def decompose_entities(msp):
    if HAS_RECURSIVE:
        try:
            return list(recursive_decompose(msp))
        except Exception:
            pass

    out = []
    for e in msp:
        if e.dxftype() == "INSERT":
            try:
                out.extend(list(e.virtual_entities()))
            except Exception:
                pass
        else:
            out.append(e)
    return out

def get_insert_xy(e):
    try:
        p = e.dxf.insert
        return float(p.x), float(p.y)
    except Exception:
        try:
            p = e.dxf.location
            return float(p.x), float(p.y)
        except Exception:
            return None

def get_points(e):
    t = e.dxftype()
    pts = []

    try:
        if t == "LINE":
            pts = [
                (float(e.dxf.start.x), float(e.dxf.start.y)),
                (float(e.dxf.end.x), float(e.dxf.end.y)),
            ]

        elif t == "LWPOLYLINE":
            pts = [(float(p[0]), float(p[1])) for p in e.get_points("xy")]

        elif t == "POLYLINE":
            pts = [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in e.vertices]

        elif t in ["ARC", "CIRCLE"]:
            cx = float(e.dxf.center.x)
            cy = float(e.dxf.center.y)
            r = float(e.dxf.radius)
            pts = [(cx-r, cy), (cx+r, cy), (cx, cy-r), (cx, cy+r)]
    except Exception:
        return []

    return pts

def entity_info(e):
    pts = get_points(e)
    if len(pts) < 2:
        return None

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    length = 0.0
    for i in range(len(pts) - 1):
        length += math.hypot(pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1])

    if length <= 0:
        return None

    return {
        "type": e.dxftype(),
        "layer": str(getattr(e.dxf, "layer", "")),
        "x": sum(xs) / len(xs),
        "y": sum(ys) / len(ys),
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys),
        "length": length
    }

def cluster_by_y(items, tol=350.0):
    if not items:
        return []

    items = sorted(items, key=lambda x: x["y"])
    clusters = []
    cur = [items[0]]

    for item in items[1:]:
        avg_y = sum(v["y"] for v in cur) / len(cur)
        if abs(item["y"] - avg_y) <= tol:
            cur.append(item)
        else:
            clusters.append(cur)
            cur = [item]

    clusters.append(cur)
    return clusters

def is_anchor_text(text):
    u = text.upper()
    return any(k.upper() in u for k in ANCHOR_TEXT_KEYS)

def main():
    result = {"files": []}

    print("전개도 앙카 단수 재분석 - 텍스트 주변 긴 도형 기준")
    print("=" * 120)

    for file_name in TARGET_FILES:
        path = os.path.join(DXF_DIR, file_name)
        if not os.path.exists(path):
            print("[없음]", file_name)
            continue

        doc = ezdxf.readfile(path)
        ents = decompose_entities(doc.modelspace())

        texts = []
        geom = []
        layers = Counter()

        for e in ents:
            layer = str(getattr(e.dxf, "layer", ""))
            layers[layer] += 1

            if e.dxftype() in ["TEXT", "MTEXT"]:
                txt = ""
                try:
                    txt = e.dxf.text if e.dxftype() == "TEXT" else e.text
                except Exception:
                    txt = ""

                txt = clean_text(txt)
                xy = get_insert_xy(e)

                if xy:
                    texts.append({
                        "text": txt,
                        "x": xy[0],
                        "y": xy[1],
                        "layer": layer
                    })

            info = entity_info(e)
            if info:
                geom.append(info)

        anchor_texts = [t for t in texts if is_anchor_text(t["text"])]

        # 앙카 텍스트가 있는 y 근처 긴 도형을 후보로 잡음
        candidates = []

        for g in geom:
            if g["length"] < 500:
                continue

            near = False

            for t in anchor_texts:
                dx = abs(g["x"] - t["x"])
                dy = abs(g["y"] - t["y"])

                # 전개도 문자와 같은 패널 안에 있는 긴 선/폴리라인 후보
                if dx < 80000 and dy < 12000:
                    near = True
                    break

            if near:
                candidates.append(g)

        clusters = cluster_by_y(candidates, tol=500.0)

        print("\n" + "=" * 120)
        print(file_name)
        print("anchor text count:", len(anchor_texts))
        for t in anchor_texts[:12]:
            print(f"  TEXT y={t['y']:.1f}, x={t['x']:.1f}, layer={t['layer']} | {t['text']}")

        print("near long geom count:", len(candidates))
        print("y cluster count:", len(clusters))

        file_out = {
            "file": file_name,
            "anchor_texts": anchor_texts[:100],
            "candidate_count": len(candidates),
            "cluster_count": len(clusters),
            "clusters": [],
            "top_layers": layers.most_common(80)
        }

        for i, cl in enumerate(clusters, 1):
            ys = [v["y"] for v in cl]
            xs = [v["x"] for v in cl]
            lens = [v["length"] for v in cl]
            layer_count = Counter(v["layer"] for v in cl)

            print(
                f"  후보 {i}단 | avg_y={sum(ys)/len(ys):.1f} | "
                f"count={len(cl)} | x={min(xs):.1f}~{max(xs):.1f} | "
                f"len_avg={sum(lens)/len(lens):.1f} | layers={layer_count.most_common(5)}"
            )

            file_out["clusters"].append({
                "index": i,
                "avg_y": sum(ys)/len(ys),
                "count": len(cl),
                "x_min": min(xs),
                "x_max": max(xs),
                "avg_len": sum(lens)/len(lens),
                "layers": layer_count.most_common(10)
            })

        result["files"].append(file_out)

    out_path = os.path.join(ROOT, "anchor_level_review_text_near_geom.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 120)
    print("결과 저장:", out_path)

if __name__ == "__main__":
    main()
