import os
import json
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

TARGET_LAYERS = {
    "STRUT",
    "BEAM-BRACING",
}

def pnt(x, y, z=0):
    return {"x": float(x), "y": float(y), "z": float(z)}

def base_entity(entity_type, layer):
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
        "points": [],
        "center": pnt(0, 0, 0),
        "position": pnt(0, 0, 0),
        "has_center": False,
        "has_position": False,
        "has_points": False,
    }

def entity_to_data(e):
    layer = str(e.dxf.layer).strip()
    t = e.dxftype()

    try:
        if t == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            out = base_entity("LINE", layer)
            out["points"] = [pnt(s.x, s.y, s.z), pnt(en.x, en.y, en.z)]
            out["has_points"] = True
            return out

        if t == "LWPOLYLINE":
            out = base_entity("LWPOLYLINE", layer)
            pts = []
            for v in e.get_points():
                pts.append(pnt(v[0], v[1], 0))
            out["points"] = pts
            out["has_points"] = len(pts) > 0
            try:
                out["closed"] = bool(e.closed)
            except Exception:
                out["closed"] = False
            return out

        if t == "POLYLINE":
            out = base_entity("POLYLINE", layer)
            pts = []
            for v in e.vertices:
                loc = v.dxf.location
                pts.append(pnt(loc.x, loc.y, loc.z))
            out["points"] = pts
            out["has_points"] = len(pts) > 0
            try:
                out["closed"] = bool(e.is_closed)
            except Exception:
                out["closed"] = False
            return out

    except Exception as ex:
        print("변환 오류:", t, layer, ex)

    return None

def decompose_entities(msp):
    if HAS_RECURSIVE:
        try:
            return list(recursive_decompose(msp))
        except Exception as ex:
            print("recursive_decompose 실패, virtual_entities 방식 사용:", ex)

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

def main():
    print("C-605 STRUT / BEAM-BRACING 추출 시작")
    print(DXF_PATH)

    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()
    raw_entities = decompose_entities(msp)

    strut_entities = []
    bracing_entities = []
    layer_count = {}

    for e in raw_entities:
        try:
            layer = str(e.dxf.layer).strip()
        except Exception:
            continue

        layer_count[layer] = layer_count.get(layer, 0) + 1

        if layer.upper() not in {x.upper() for x in TARGET_LAYERS}:
            continue

        data = entity_to_data(e)
        if not data or not data.get("has_points"):
            continue

        if layer.upper() == "STRUT":
            strut_entities.append(data)
        elif layer.upper() == "BEAM-BRACING":
            bracing_entities.append(data)

    all_entities = strut_entities + bracing_entities

    out = {
        "group": "C605_STRUT_PLAN",
        "entity_count": len(all_entities),
        "entities": all_entities,
    }

    with open(os.path.join(OUT_DIR, "c605_strut_plan.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    summary = {
        "source": DXF_PATH,
        "strut_count": len(strut_entities),
        "beam_bracing_count": len(bracing_entities),
        "total": len(all_entities),
        "layer_count": dict(sorted(layer_count.items(), key=lambda x: x[1], reverse=True)),
    }

    with open(os.path.join(OUT_DIR, "c605_strut_plan_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("")
    print("완료")
    print("STRUT =", len(strut_entities))
    print("BEAM-BRACING =", len(bracing_entities))
    print("TOTAL =", len(all_entities))
    print("OUT =", os.path.join(OUT_DIR, "c605_strut_plan.json"))

if __name__ == "__main__":
    main()
