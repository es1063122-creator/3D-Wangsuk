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
    "c605_beam_bracing_endpoint_angle.txt"
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
        if layer.upper() != "BEAM-BRACING":
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
            "start": a,
            "end": b,
            "center": (cx, cy),
            "length": ln,
            "angle": ang,
            "type": e.dxftype(),
        })

    # 중심 좌표 기준 정렬
    rows.sort(key=lambda r: (r["center"][1], r["center"][0]), reverse=True)

    os.makedirs(os.path.dirname(OUT_TXT), exist_ok=True)

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-605 BEAM-BRACING 시작점/끝점/각도 검토\n")
        f.write("=" * 120 + "\n\n")
        f.write(f"count: {len(rows)}\n\n")

        for i, r in enumerate(rows, start=1):
            f.write("=" * 120 + "\n")
            f.write(f"BEAM-BRACING #{i}\n")
            f.write(f"  type   : {r['type']}\n")
            f.write(f"  length : {r['length']:.1f}\n")
            f.write(f"  angle  : {r['angle']:.2f} deg\n")
            f.write(f"  center : x={r['center'][0]:.1f}, y={r['center'][1]:.1f}\n")
            f.write(f"  start  : x={r['start'][0]:.1f}, y={r['start'][1]:.1f}\n")
            f.write(f"  end    : x={r['end'][0]:.1f}, y={r['end'][1]:.1f}\n")

            if r["length"] > 1000:
                f.write("  판단   : 코너 스트러트 본체 후보\n")
            else:
                f.write("  판단   : 단부/보강선 후보\n")

            f.write("\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
