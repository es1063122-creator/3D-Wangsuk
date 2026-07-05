import os
import json
import math
import ezdxf

try:
    from PIL import Image, ImageDraw
except Exception:
    raise SystemExit("Pillow가 필요합니다. 먼저 실행하세요: python -m pip install pillow")

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

JSON_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "ParsedUnityJson_C605"
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

PF_JSON = os.path.join(JSON_DIR, "c605_pf_hpile.json")

TARGET_DXF_PREFIX = "C-605"

IMAGE_W = 4096
IMAGE_H = 4096
PAD_RATIO = 0.035

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

def collect_xy_from_json(obj, out):
    if isinstance(obj, dict):
        if "x" in obj and "y" in obj:
            try:
                out.append((float(obj["x"]), float(obj["y"])))
            except Exception:
                pass

        if "start" in obj and isinstance(obj["start"], dict):
            collect_xy_from_json(obj["start"], out)

        if "end" in obj and isinstance(obj["end"], dict):
            collect_xy_from_json(obj["end"], out)

        for v in obj.values():
            collect_xy_from_json(v, out)

    elif isinstance(obj, list):
        if len(obj) >= 2:
            try:
                a = float(obj[0])
                b = float(obj[1])
                # 너무 작은 일반 배열값이 섞이는 것을 줄이기 위한 기준
                if abs(a) > 1000 and abs(b) > 1000:
                    out.append((a, b))
            except Exception:
                pass

        for v in obj:
            collect_xy_from_json(v, out)

def get_pf_bbox():
    with open(PF_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    pts = []
    collect_xy_from_json(data, pts)

    if len(pts) < 10:
        raise RuntimeError("PF JSON에서 좌표를 충분히 찾지 못했습니다.")

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    pad_x = (max_x - min_x) * PAD_RATIO
    pad_y = (max_y - min_y) * PAD_RATIO

    return min_x - pad_x, max_x + pad_x, min_y - pad_y, max_y + pad_y

def find_c605_dxf():
    files = []
    for fname in os.listdir(DXF_DIR):
        if fname.lower().endswith(".dxf") and fname.startswith(TARGET_DXF_PREFIX):
            files.append(fname)

    if not files:
        raise RuntimeError("C-605 DXF 파일을 찾지 못했습니다.")

    # 굴착계획 평면도 우선
    for f in files:
        if "평면" in f or "굴착계획" in f:
            return os.path.join(DXF_DIR, f)

    return os.path.join(DXF_DIR, files[0])

def world_to_px(x, y, bbox):
    min_x, max_x, min_y, max_y = bbox

    u = (x - min_x) / (max_x - min_x)
    v = (y - min_y) / (max_y - min_y)

    px = int(u * (IMAGE_W - 1))
    py = int((1.0 - v) * (IMAGE_H - 1))
    return px, py

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

        if e.dxftype() == "CIRCLE":
            c = e.dxf.center
            r = float(e.dxf.radius)
            pts = []
            for i in range(49):
                ang = math.pi * 2 * i / 48
                pts.append((float(c.x) + math.cos(ang) * r, float(c.y) + math.sin(ang) * r))
            return pts

        if e.dxftype() == "ARC":
            c = e.dxf.center
            r = float(e.dxf.radius)
            a0 = math.radians(float(e.dxf.start_angle))
            a1 = math.radians(float(e.dxf.end_angle))
            if a1 < a0:
                a1 += math.pi * 2
            pts = []
            steps = 32
            for i in range(steps + 1):
                ang = a0 + (a1 - a0) * i / steps
                pts.append((float(c.x) + math.cos(ang) * r, float(c.y) + math.sin(ang) * r))
            return pts
    except Exception:
        return []

    return []

def in_bbox_any(pts, bbox):
    min_x, max_x, min_y, max_y = bbox
    for x, y in pts:
        if min_x <= x <= max_x and min_y <= y <= max_y:
            return True
    return False

def main():
    bbox = get_pf_bbox()
    dxf_path = find_c605_dxf()

    print("C-605 DXF:", dxf_path)
    print("PF 기준 bbox:", bbox)

    doc = ezdxf.readfile(dxf_path)
    ents = decompose_entities(doc.modelspace())

    img = Image.new("RGBA", (IMAGE_W, IMAGE_H), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    line_count = 0

    for e in ents:
        etype = e.dxftype()
        layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""

        if etype not in ["LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC"]:
            continue

        pts = get_points(e)
        if len(pts) < 2:
            continue

        if not in_bbox_any(pts, bbox):
            continue

        pix = [world_to_px(x, y, bbox) for x, y in pts]

        # 흙막이/앵커/구조 관련 레이어는 조금 진하게
        u = layer.upper()
        if "PILE" in u or "CIP" in u or "WALE" in u or "ANCH" in u or "STRUT" in u:
            color = (20, 20, 20, 175)
            width = 2
        else:
            color = (45, 45, 45, 120)
            width = 1

        try:
            draw.line(pix, fill=color, width=width)
            line_count += 1
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
        "note": "PF/H-PILE JSON bbox 기준으로 C-605 평면도 라인워크를 투명 PNG로 렌더링"
    }

    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("저장 PNG:", OUT_PNG)
    print("저장 META:", OUT_META)
    print("line_count:", line_count)

if __name__ == "__main__":
    main()
