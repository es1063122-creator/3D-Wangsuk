import os
import math
import json
import ezdxf
from collections import defaultdict

try:
    from PIL import Image, ImageDraw
except Exception:
    raise SystemExit("Pillow가 필요합니다. 실행: python -m pip install pillow")

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
    "Overlay"
)

os.makedirs(OUT_DIR, exist_ok=True)

OUT_PNG = os.path.join(OUT_DIR, "c605_plan_overlay.png")
OUT_META = os.path.join(OUT_DIR, "c605_plan_overlay_meta.json")

IMAGE_W = 4096
IMAGE_H = 4096

TARGET_PREFIX = "C-605"

IMPORTANT_LAYER_KEYS = [
    "PILE", "H-PILE", "CIP", "C.I.P", "WALE",
    "ANCH", "ANCHOR", "STRUT", "BEAM", "BRACING",
    "굴착", "토목"
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

def find_c605_dxf():
    candidates = []
    for fname in os.listdir(DXF_DIR):
        if fname.lower().endswith(".dxf") and fname.startswith(TARGET_PREFIX):
            candidates.append(fname)

    candidates.sort()

    for f in candidates:
        if "굴착계획" in f and "평면" in f:
            return os.path.join(DXF_DIR, f)

    if candidates:
        return os.path.join(DXF_DIR, candidates[0])

    raise RuntimeError("C-605 DXF를 찾지 못했습니다.")

def hit_layer(layer):
    u = str(layer).upper()
    return any(k.upper() in u for k in IMPORTANT_LAYER_KEYS)

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

def bbox_of_points(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), max(xs), min(ys), max(ys)

def bbox_area(b):
    return max(0.0, b[1] - b[0]) * max(0.0, b[3] - b[2])

def bbox_center(b):
    return ((b[0] + b[1]) * 0.5, (b[2] + b[3]) * 0.5)

def main():
    dxf_path = find_c605_dxf()
    print("C-605 DXF:", dxf_path)

    doc = ezdxf.readfile(dxf_path)
    ents = decompose_entities(doc.modelspace())

    rows = []

    for e in ents:
        etype = e.dxftype()
        if etype not in ["LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC"]:
            continue

        layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""
        pts = get_points(e)

        if len(pts) < 2:
            continue

        b = bbox_of_points(pts)
        w = b[1] - b[0]
        h = b[3] - b[2]
        area = bbox_area(b)

        if w <= 0 or h <= 0:
            continue

        cx, cy = bbox_center(b)

        rows.append({
            "entity": e,
            "layer": layer,
            "pts": pts,
            "bbox": b,
            "cx": cx,
            "cy": cy,
            "w": w,
            "h": h,
            "area": area,
            "important": hit_layer(layer)
        })

    if not rows:
        raise RuntimeError("렌더링할 라인이 없습니다.")

    # 실제 굴착 평면도는 같은 좌표군에 선들이 매우 많이 몰려 있음.
    # 제목표/주기/키플랜/외곽 배치 등은 좌표가 멀거나 군집이 작음.
    # 주요 레이어 우선으로 bbox 후보를 만들고, 너무 큰 제목표 영역은 제외.
    important = [r for r in rows if r["important"]]

    if len(important) < 50:
        important = rows

    xs = []
    ys = []

    for r in important:
        # 지나치게 긴 도면 외곽선/타이틀 영역은 bbox 결정에서 제외
        if r["w"] > 250000 or r["h"] > 250000:
            continue

        for x, y in r["pts"]:
            xs.append(x)
            ys.append(y)

    if len(xs) < 100:
        xs = []
        ys = []
        for r in rows:
            if r["w"] > 250000 or r["h"] > 250000:
                continue
            for x, y in r["pts"]:
                xs.append(x)
                ys.append(y)

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    pad_x = (max_x - min_x) * 0.045
    pad_y = (max_y - min_y) * 0.045

    bbox = (min_x - pad_x, max_x + pad_x, min_y - pad_y, max_y + pad_y)

    print("새 bbox:", bbox)

    def in_bbox_any(pts):
        for x, y in pts:
            if bbox[0] <= x <= bbox[1] and bbox[2] <= y <= bbox[3]:
                return True
        return False

    def world_to_px(x, y):
        u = (x - bbox[0]) / (bbox[1] - bbox[0])
        v = (y - bbox[2]) / (bbox[3] - bbox[2])

        px = int(u * (IMAGE_W - 1))
        py = int((1.0 - v) * (IMAGE_H - 1))
        return px, py

    img = Image.new("RGBA", (IMAGE_W, IMAGE_H), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    line_count = 0
    layer_count = defaultdict(int)

    for r in rows:
        pts = r["pts"]

        if not in_bbox_any(pts):
            continue

        pix = [world_to_px(x, y) for x, y in pts]

        layer = r["layer"]
        u = layer.upper()

        if "PILE" in u or "CIP" in u or "C.I.P" in u:
            color = (0, 0, 0, 210)
            width = 3
        elif "WALE" in u or "STRUT" in u or "ANCH" in u or "BEAM" in u:
            color = (20, 20, 20, 175)
            width = 2
        else:
            color = (40, 40, 40, 105)
            width = 1

        try:
            draw.line(pix, fill=color, width=width)
            line_count += 1
            layer_count[layer] += 1
        except Exception:
            pass

    img.save(OUT_PNG)

    meta = {
        "source_dxf": os.path.basename(dxf_path),
        "image": os.path.basename(OUT_PNG),
        "bbox_raw": {
            "min_x": bbox[0],
            "max_x": bbox[1],
            "min_y": bbox[2],
            "max_y": bbox[3]
        },
        "image_width": IMAGE_W,
        "image_height": IMAGE_H,
        "line_count": line_count,
        "top_layers": sorted(layer_count.items(), key=lambda x: x[1], reverse=True)[:30],
        "note": "C-605 굴착평면 실제 주요 레이어 군집 bbox 기준 재생성"
    }

    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("저장 PNG:", OUT_PNG)
    print("저장 META:", OUT_META)
    print("line_count:", line_count)

if __name__ == "__main__":
    main()
