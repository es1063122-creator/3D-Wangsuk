import os
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
    "c605_anchor_length_angle_review.txt"
)

TARGET_LAYERS = [
    "ANCHOR",
    "ANCHOR_1단",
    "Anchor_1단",
    "C-ANCH-FREE",
    "C-ANCH-BOND",
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

def length(a, b):
    return math.sqrt((b[0]-a[0])**2 + (b[1]-a[1])**2)

def angle_deg(a, b):
    return math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))

def main():
    doc = ezdxf.readfile(DXF_PATH)
    ents = decompose_entities(doc.modelspace())

    rows = []
    layer_count = {}

    for e in ents:
        layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""

        if layer.upper() not in [x.upper() for x in TARGET_LAYERS]:
            continue

        layer_count[layer] = layer_count.get(layer, 0) + 1

        pts = get_points(e)
        if len(pts) < 2:
            continue

        a = pts[0]
        b = pts[-1]
        cx = (a[0] + b[0]) / 2
        cy = (a[1] + b[1]) / 2
        ln = length(a, b)
        ang = angle_deg(a, b)

        rows.append({
            "layer": layer,
            "type": e.dxftype(),
            "length": ln,
            "angle": ang,
            "center_x": cx,
            "center_y": cy,
            "start": a,
            "end": b,
        })

    rows.sort(key=lambda r: r["length"], reverse=True)

    long_anchors = [r for r in rows if r["length"] >= 1000]
    short_anchors = [r for r in rows if r["length"] < 1000]

    os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-605 ANCHOR 길이/각도 검토\n")
        f.write("=" * 120 + "\n\n")

        f.write("[레이어 카운트]\n")
        for layer, cnt in sorted(layer_count.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {layer:30s} {cnt}\n")

        f.write("\n")
        f.write(f"도형 변환 가능 ANCHOR count: {len(rows)}\n")
        f.write(f"length >= 1000 후보: {len(long_anchors)}\n")
        f.write(f"length < 1000 후보: {len(short_anchors)}\n\n")

        f.write("[긴 ANCHOR 후보 length >= 1000 상위 100개]\n")
        for i, r in enumerate(long_anchors[:100], start=1):
            f.write(
                f"{i:03d} | layer={r['layer']} | len={r['length']:.1f} | angle={r['angle']:.2f} | "
                f"center=({r['center_x']:.1f}, {r['center_y']:.1f}) | type={r['type']}\n"
            )

        f.write("\n[짧은 ANCHOR 후보 length < 1000 상위 100개]\n")
        for i, r in enumerate(short_anchors[:100], start=1):
            f.write(
                f"{i:03d} | layer={r['layer']} | len={r['length']:.1f} | angle={r['angle']:.2f} | "
                f"center=({r['center_x']:.1f}, {r['center_y']:.1f}) | type={r['type']}\n"
            )

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
