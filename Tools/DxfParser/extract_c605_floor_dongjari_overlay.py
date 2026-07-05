import os
import re
import json
import math
import ezdxf

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
    "ParsedUnityJson_C605"
)

REVIEW_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review"
)

CANDIDATE_TXT = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Overlay",
    "candidates",
    "candidate_01.txt"
)

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(REVIEW_DIR, exist_ok=True)

OUT_JSON = os.path.join(OUT_DIR, "c605_floor_dongjari_overlay.json")
OUT_REVIEW = os.path.join(REVIEW_DIR, "c605_floor_dongjari_overlay_review.txt")

EXCLUDE_LAYER_KEYS = [
    "ANCH", "ANCHOR", "앵커", "E/ANCHOR",
    "STRUT", "버팀",
    "WALE", "띠장",
    "BEAM", "BRACING",
    "H-PILE", "HPILE", "PILE", "CIP", "C.I.P",
    "계측", "계측기",
    "DIM", "치수",
    "TEXT", "문자",
    "TITLE", "표제", "도곽", "FRAME",
]

# 너무 세부적인 심볼/해치류 제거용
EXCLUDE_LAYER_EXACT_HINTS = [
    "HATCH",
    "해치",
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
    files = []
    for fname in os.listdir(DXF_DIR):
        if fname.lower().endswith(".dxf") and fname.startswith("C-605"):
            files.append(fname)

    files.sort()

    for f in files:
        if "굴착계획" in f and "평면" in f:
            return os.path.join(DXF_DIR, f)

    if files:
        return os.path.join(DXF_DIR, files[0])

    raise RuntimeError("C-605 DXF 파일을 찾지 못했습니다.")

def parse_candidate_bbox():
    if not os.path.exists(CANDIDATE_TXT):
        print("candidate_01.txt 없음. 전체 bbox 필터 없이 진행")
        return None

    txt = open(CANDIDATE_TXT, "r", encoding="utf-8").read()
    m = re.search(r"bbox=\(([^)]+)\)", txt)
    if not m:
        print("candidate_01 bbox 파싱 실패")
        return None

    vals = [float(x.strip()) for x in m.group(1).split(",")]
    if len(vals) != 4:
        return None

    min_x, max_x, min_y, max_y = vals

    # candidate_01 이미지에서 실제 C-605 굴착계획 평면도는 하단 영역.
    # 상단 동자리 스케치는 같은 시트 안의 별도 축척/위치이므로 제외.
    # 다만 현재 목적은 바닥 동자리/건물선이므로 하단 평면도 안의 건물/기초선만 가져온다.
    # 이미지 crop 기준 44%~94% 영역을 raw bbox로 환산.
    crop_top_ratio = 0.44
    crop_bottom_ratio = 0.94
    crop_left_ratio = 0.04
    crop_right_ratio = 0.94

    w = max_x - min_x
    h = max_y - min_y

    crop_min_x = min_x + w * crop_left_ratio
    crop_max_x = min_x + w * crop_right_ratio

    # 이미지 y는 위가 max_y, 아래가 min_y
    crop_max_y = max_y - h * crop_top_ratio
    crop_min_y = max_y - h * crop_bottom_ratio

    return crop_min_x, crop_max_x, crop_min_y, crop_max_y

def layer_excluded(layer):
    u = str(layer).upper()

    for k in EXCLUDE_LAYER_KEYS:
        if k.upper() in u:
            return True

    for k in EXCLUDE_LAYER_EXACT_HINTS:
        if k.upper() in u:
            return True

    return False

def get_points(e):
    try:
        if e.dxftype() == "LINE":
            s = e.dxf.start
            t = e.dxf.end
            return [{"x": float(s.x), "y": float(s.y)}, {"x": float(t.x), "y": float(t.y)}]

        if e.dxftype() == "LWPOLYLINE":
            return [{"x": float(p[0]), "y": float(p[1])} for p in e.get_points()]

        if e.dxftype() == "POLYLINE":
            pts = []
            for v in e.vertices:
                p = v.dxf.location
                pts.append({"x": float(p.x), "y": float(p.y)})
            return pts

        if e.dxftype() == "CIRCLE":
            c = e.dxf.center
            r = float(e.dxf.radius)
            pts = []
            for i in range(49):
                a = math.pi * 2 * i / 48
                pts.append({"x": float(c.x) + math.cos(a) * r, "y": float(c.y) + math.sin(a) * r})
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
                pts.append({"x": float(c.x) + math.cos(a) * r, "y": float(c.y) + math.sin(a) * r})
            return pts

    except Exception:
        return []

    return []

def bbox_of_pts(pts):
    xs = [p["x"] for p in pts]
    ys = [p["y"] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)

def in_bbox_any(pts, bbox):
    if bbox is None:
        return True

    min_x, max_x, min_y, max_y = bbox

    for p in pts:
        x = p["x"]
        y = p["y"]

        if min_x <= x <= max_x and min_y <= y <= max_y:
            return True

    return False

def main():
    dxf_path = find_c605_dxf()
    bbox = parse_candidate_bbox()

    print("DXF:", dxf_path)
    print("하단 평면도 crop bbox:", bbox)

    doc = ezdxf.readfile(dxf_path)
    ents = decompose_entities(doc.modelspace())

    out_entities = []
    layer_counts = {}
    excluded_counts = {}
    total = 0

    for e in ents:
        etype = e.dxftype()
        if etype not in ["LINE", "LWPOLYLINE", "POLYLINE", "CIRCLE", "ARC"]:
            continue

        total += 1
        layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""

        pts = get_points(e)
        if len(pts) < 2:
            continue

        if not in_bbox_any(pts, bbox):
            continue

        if layer_excluded(layer):
            excluded_counts[layer] = excluded_counts.get(layer, 0) + 1
            continue

        bx = bbox_of_pts(pts)
        bw = bx[1] - bx[0]
        bh = bx[3] - bx[2]

        # 너무 긴 도곽/시트 선 제외
        if bw > 250000 or bh > 250000:
            excluded_counts[layer] = excluded_counts.get(layer, 0) + 1
            continue

        # 너무 작은 점/해치성 선은 일부 제외
        if bw < 5 and bh < 5:
            continue

        out_entities.append({
            "type": etype,
            "layer": layer,
            "points": pts
        })

        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    data = {
        "name": "C605_FLOOR_DONGJARI_OVERLAY",
        "groupName": "C605_FLOOR_DONGJARI_OVERLAY",
        "entities": out_entities
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(OUT_REVIEW, "w", encoding="utf-8") as f:
        f.write("C-605 바닥 동자리/건물선 오버레이 추출 검토\n")
        f.write("=" * 100 + "\n")
        f.write(f"DXF: {os.path.basename(dxf_path)}\n")
        f.write(f"crop bbox: {bbox}\n")
        f.write(f"total geometry entities: {total}\n")
        f.write(f"kept entities: {len(out_entities)}\n\n")

        f.write("[포함 레이어 TOP]\n")
        for layer, count in sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)[:50]:
            f.write(f"{count:6d} | {layer}\n")

        f.write("\n[제외 레이어 TOP]\n")
        for layer, count in sorted(excluded_counts.items(), key=lambda x: x[1], reverse=True)[:50]:
            f.write(f"{count:6d} | {layer}\n")

    print("저장 JSON:", OUT_JSON)
    print("검토 TXT:", OUT_REVIEW)
    print("kept entities:", len(out_entities))

if __name__ == "__main__":
    main()
