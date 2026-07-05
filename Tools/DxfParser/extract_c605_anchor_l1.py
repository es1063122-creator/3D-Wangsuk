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

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "ParsedUnityJson_C605"
)

os.makedirs(OUT_DIR, exist_ok=True)

TARGET_LAYERS = [
    "ANCHOR",
    "Anchor_1단",
    "ANCHOR_1단",
]

MIN_BODY_LENGTH = 1000.0

def pnt(x, y, z=0):
    return {"x": float(x), "y": float(y), "z": float(z)}

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
            return [pnt(s.x, s.y, s.z), pnt(en.x, en.y, en.z)]

        if e.dxftype() == "LWPOLYLINE":
            return [pnt(v[0], v[1], 0) for v in e.get_points()]

        if e.dxftype() == "POLYLINE":
            pts = []
            for v in e.vertices:
                loc = v.dxf.location
                pts.append(pnt(loc.x, loc.y, loc.z))
            return pts
    except Exception:
        return []

    return []

def dist2d(a, b):
    dx = float(b["x"]) - float(a["x"])
    dy = float(b["y"]) - float(a["y"])
    return math.sqrt(dx * dx + dy * dy)

def entity_length(pts):
    if len(pts) < 2:
        return 0.0
    return dist2d(pts[0], pts[-1])

def base_entity(entity_type, layer, pts):
    return {
        "source_file": r"dxf\6.가시설공사\C-605 굴착계획 평면도.dxf",
        "type": entity_type,
        "layer": layer,
        "color": 0,
        "linetype": "",
        "closed": False,
        "radius": 0.0,
        "height": 0.0,
        "rotation": 0.0,
        "text": "",
        "block_name": "",
        "points": pts,
        "center": pnt(0, 0, 0),
        "position": pnt(0, 0, 0),
        "has_center": False,
        "has_position": False,
        "has_points": True,
    }

def main():
    print("C-605 ANCHOR_L1 본체 추출 시작")
    print(DXF_PATH)

    doc = ezdxf.readfile(DXF_PATH)
    ents = decompose_entities(doc.modelspace())

    out_entities = []
    skipped_short = 0
    layer_count = {}

    for e in ents:
        try:
            layer = str(e.dxf.layer).strip()
        except Exception:
            continue

        if layer.upper() not in [x.upper() for x in TARGET_LAYERS]:
            continue

        layer_count[layer] = layer_count.get(layer, 0) + 1

        pts = get_points(e)
        if len(pts) < 2:
            continue

        length = entity_length(pts)
        if length < MIN_BODY_LENGTH:
            skipped_short += 1
            continue

        item = base_entity(e.dxftype(), layer, pts)
        item["length"] = length
        out_entities.append(item)

    result = {
        "group": "C605_ANCHOR_L1",
        "entity_count": len(out_entities),
        "entities": out_entities,
    }

    out_json = os.path.join(OUT_DIR, "c605_anchor_l1.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    summary = {
        "source": DXF_PATH,
        "layer_count": layer_count,
        "min_body_length": MIN_BODY_LENGTH,
        "body_count": len(out_entities),
        "skipped_short": skipped_short,
        "out_json": out_json,
    }

    out_summary = os.path.join(OUT_DIR, "c605_anchor_l1_summary.json")
    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("")
    print("완료")
    print("ANCHOR_L1 body =", len(out_entities))
    print("skipped short =", skipped_short)
    print("OUT =", out_json)

if __name__ == "__main__":
    main()
