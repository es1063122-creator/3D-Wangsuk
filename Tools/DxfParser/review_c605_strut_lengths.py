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
    "c605_strut_length_review.txt"
)

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

    for e in ents:
        layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""
        if layer.upper() != "STRUT":
            continue

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
            "type": e.dxftype(),
            "length": ln,
            "angle": ang,
            "center_x": cx,
            "center_y": cy,
            "start": a,
            "end": b,
        })

    rows.sort(key=lambda r: r["length"], reverse=True)

    os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-605 STRUT 길이/각도 검토\n")
        f.write("=" * 120 + "\n\n")
        f.write(f"STRUT count: {len(rows)}\n\n")

        over_1000 = [r for r in rows if r["length"] >= 1000]
        under_1000 = [r for r in rows if r["length"] < 1000]

        f.write(f"length >= 1000 후보: {len(over_1000)}\n")
        f.write(f"length < 1000 후보: {len(under_1000)}\n\n")

        f.write("[긴 STRUT 후보 length >= 1000]\n")
        for i, r in enumerate(over_1000, start=1):
            f.write(
                f"{i:03d} | len={r['length']:.1f} | angle={r['angle']:.2f} | "
                f"center=({r['center_x']:.1f}, {r['center_y']:.1f}) | "
                f"type={r['type']}\n"
            )

        f.write("\n[짧은 STRUT 후보 length < 1000]\n")
        for i, r in enumerate(under_1000, start=1):
            f.write(
                f"{i:03d} | len={r['length']:.1f} | angle={r['angle']:.2f} | "
                f"center=({r['center_x']:.1f}, {r['center_y']:.1f}) | "
                f"type={r['type']}\n"
            )

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
