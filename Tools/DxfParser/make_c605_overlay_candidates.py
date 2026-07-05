import os
import math
import ezdxf
from PIL import Image, ImageDraw

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

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Overlay",
    "candidates"
)

os.makedirs(OUT_DIR, exist_ok=True)

IMAGE_W = 1800
IMAGE_H = 1400

TARGET_PREFIX = "C-605"

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

def find_c605_dxf():
    files = []
    for fname in os.listdir(DXF_DIR):
        if fname.lower().endswith(".dxf") and fname.startswith(TARGET_PREFIX):
            files.append(fname)

    files.sort()

    for f in files:
        if "굴착계획" in f and "평면" in f:
            return os.path.join(DXF_DIR, f)

    if not files:
        raise RuntimeError("C-605 DXF 없음")

    return os.path.join(DXF_DIR, files[0])

def get_points(e):
    try:
        if e.dxftype() == "LINE":
            s = e.dxf.start
            t = e.dxf.end
            return [(float(s.x), float(s.y)), (float(t.x), float(t.y))]

        if e.dxftype() == "LWPOLYLINE":
            return [(float(p[0]), float(p[1])) for p in e.get_points()]

        if e.dxftype() == "POLYLINE":
            pts = []
            for v in e.vertices:
                p = v.dxf.location
                pts.append((float(p.x), float(p.y)))
            return pts

        if e.dxftype() == "CIRCLE":
            c = e.dxf.center
            r = float(e.dxf.radius)
            pts = []
            for i in range(49):
                a = math.pi * 2 * i / 48
                pts.append((float(c.x) + math.cos(a) * r, float(c.y) + math.sin(a) * r))
            return pts

        if e.dxftype() == "ARC":
            c = e.dxf.center
            r = float(e.dxf.radius)
            a0 = math.radians(float(e.dxf.start_angle))
            a1 = math.radians(float(e.dxf.end_angle))
            if a1 < a0:
                a1 += math.pi * 2

            pts = []
            for i in range(33):
                a = a0 + (a1 - a0) * i / 32
                pts.append((float(c.x) + math.cos(a) * r, float(c.y) + math.sin(a) * r))
            return pts
    except Exception:
        return []

    return []

def bbox_of_points(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)

def expand_bbox(b, pad_ratio):
    minx, maxx, miny, maxy = b
    px = (maxx - minx) * pad_ratio
    py = (maxy - miny) * pad_ratio
    return minx - px, maxx + px, miny - py, maxy + py

def overlap_or_near(b1, b2, gap):
    return not (
        b1[1] + gap < b2[0] or
        b2[1] + gap < b1[0] or
        b1[3] + gap < b2[2] or
        b2[3] + gap < b1[2]
    )

def merge_bbox(b1, b2):
    return (
        min(b1[0], b2[0]),
        max(b1[1], b2[1]),
        min(b1[2], b2[2]),
        max(b1[3], b2[3])
    )

def render_candidate(rows, bbox, out_path):
    bbox = expand_bbox(bbox, 0.04)

    minx, maxx, miny, maxy = bbox

    img = Image.new("RGBA", (IMAGE_W, IMAGE_H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    def to_px(x, y):
        u = (x - minx) / (maxx - minx)
        v = (y - miny) / (maxy - miny)
        px = int(u * (IMAGE_W - 1))
        py = int((1.0 - v) * (IMAGE_H - 1))
        return px, py

    count = 0

    for r in rows:
        pts = r["pts"]
        b = r["bbox"]

        if not overlap_or_near(b, bbox, 0):
            continue

        pix = [to_px(x, y) for x, y in pts]

        layer = r["layer"].upper()

        if "PILE" in layer or "CIP" in layer or "ANCH" in layer or "WALE" in layer or "STRUT" in layer:
            color = (0, 0, 0, 255)
            width = 2
        else:
            color = (80, 80, 80, 190)
            width = 1

        try:
            draw.line(pix, fill=color, width=width)
            count += 1
        except Exception:
            pass

    draw.rectangle([0, 0, IMAGE_W - 1, IMAGE_H - 1], outline=(255, 0, 0, 255), width=4)
    img.save(out_path)
    return count

def main():
    dxf_path = find_c605_dxf()
    print("DXF:", dxf_path)

    doc = ezdxf.readfile(dxf_path)
    ents = decompose_entities(doc.modelspace())

    rows = []

    for e in ents:
        if e.dxftype() not in ["LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC"]:
            continue

        pts = get_points(e)
        if len(pts) < 2:
            continue

        b = bbox_of_points(pts)
        w = b[1] - b[0]
        h = b[3] - b[2]

        # 너무 긴 단일 외곽선/도면틀은 군집 기준에서 제외
        if w > 500000 or h > 500000:
            continue

        cx = (b[0] + b[1]) * 0.5
        cy = (b[2] + b[3]) * 0.5

        rows.append({
            "entity": e,
            "pts": pts,
            "bbox": b,
            "cx": cx,
            "cy": cy,
            "layer": str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""
        })

    print("대상 엔티티:", len(rows))

    # 간단 군집화
    clusters = []

    for r in rows:
        b = r["bbox"]
        added = False

        for c in clusters:
            if overlap_or_near(c["bbox"], b, 35000):
                c["bbox"] = merge_bbox(c["bbox"], b)
                c["items"].append(r)
                added = True
                break

        if not added:
            clusters.append({
                "bbox": b,
                "items": [r]
            })

    # 다시 한번 병합
    changed = True
    while changed:
        changed = False
        merged = []
        used = [False] * len(clusters)

        for i in range(len(clusters)):
            if used[i]:
                continue

            base = clusters[i]
            used[i] = True

            for j in range(i + 1, len(clusters)):
                if used[j]:
                    continue

                if overlap_or_near(base["bbox"], clusters[j]["bbox"], 35000):
                    base["bbox"] = merge_bbox(base["bbox"], clusters[j]["bbox"])
                    base["items"].extend(clusters[j]["items"])
                    used[j] = True
                    changed = True

            merged.append(base)

        clusters = merged

    # 너무 작은 군집 제외
    clusters = [c for c in clusters if len(c["items"]) >= 80]

    # 큰 군집/많은 선 우선
    clusters.sort(key=lambda c: len(c["items"]), reverse=True)

    print("후보 군집 수:", len(clusters))

    for i, c in enumerate(clusters[:12], start=1):
        out = os.path.join(OUT_DIR, f"candidate_{i:02d}.png")
        cnt = render_candidate(rows, c["bbox"], out)

        meta = os.path.join(OUT_DIR, f"candidate_{i:02d}.txt")
        b = expand_bbox(c["bbox"], 0.04)

        with open(meta, "w", encoding="utf-8") as f:
            f.write(f"candidate={i}\n")
            f.write(f"items={len(c['items'])}\n")
            f.write(f"rendered_lines={cnt}\n")
            f.write(f"bbox={b}\n")

        print(f"candidate_{i:02d}.png / items={len(c['items'])} / rendered={cnt} / bbox={b}")

    print("완료:", OUT_DIR)

if __name__ == "__main__":
    main()
