import os
import json
import ezdxf

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

WALE_LAYERS = {
    "WALE",
    "C-WALE",
    "-$$WALE",
    "__WALE",
    "00-WALE",
    "00-C-WALE",
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
        print("entity 변환 오류:", t, layer, ex)

    return None

def collect_virtual_entities(insert):
    result = []
    try:
        for ve in insert.virtual_entities():
            result.append(ve)
    except Exception as ex:
        print("INSERT virtual_entities 실패:", insert.dxf.name, ex)
    return result

def main():
    print("C-605 WALE 전용 추출 시작")
    print(DXF_PATH)

    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()

    raw_entities = []

    for e in msp:
        if e.dxftype() == "INSERT":
            raw_entities.extend(collect_virtual_entities(e))
        else:
            raw_entities.append(e)

    wale_entities = []
    layer_count = {}

    for e in raw_entities:
        layer = str(e.dxf.layer).strip()
        layer_count[layer] = layer_count.get(layer, 0) + 1

        if layer.upper() in {x.upper() for x in WALE_LAYERS}:
            data = entity_to_data(e)
            if data:
                wale_entities.append(data)

    wale_out = {
        "group": "C605_WALE",
        "entity_count": len(wale_entities),
        "entities": wale_entities,
    }

    with open(os.path.join(OUT_DIR, "c605_wale.json"), "w", encoding="utf-8") as f:
        json.dump(wale_out, f, ensure_ascii=False, indent=2)

    summary = {
        "dxf": DXF_PATH,
        "wale_count": len(wale_entities),
        "layer_count": dict(sorted(layer_count.items(), key=lambda x: x[1], reverse=True)),
    }

    with open(os.path.join(OUT_DIR, "c605_wale_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("")
    print("완료")
    print("WALE:", len(wale_entities))
    print("OUT:", OUT_DIR)

    print("")
    print("주요 레이어:")
    for k, v in list(summary["layer_count"].items())[:40]:
        print(f"{k:35s} {v}")

if __name__ == "__main__":
    main()
