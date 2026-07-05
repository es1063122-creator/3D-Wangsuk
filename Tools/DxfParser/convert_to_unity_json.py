import os
import json

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"
SRC_DIR = os.path.join(PROJECT_ROOT, "Assets", "StreamingAssets", "WangsukDXF", "ParsedJson")
DST_DIR = os.path.join(PROJECT_ROOT, "Assets", "StreamingAssets", "WangsukDXF", "ParsedUnityJson")

os.makedirs(DST_DIR, exist_ok=True)

TARGET_FILES = [
    "wangsuk_pf_hpile.json",
    "wangsuk_cip.json",
    "wangsuk_wale.json",
    "wangsuk_anchor.json",
    "wangsuk_corner_strut.json",
    "wangsuk_excavation.json",
    "wangsuk_ground_gl.json",
    "wangsuk_section_lines.json",
    "wangsuk_grid.json",
    "wangsuk_labels.json",
    "wangsuk_building_parking.json",
]

def to_point_obj(p):
    if not isinstance(p, list):
        return {"x": 0.0, "y": 0.0, "z": 0.0}

    x = float(p[0]) if len(p) > 0 else 0.0
    y = float(p[1]) if len(p) > 1 else 0.0
    z = float(p[2]) if len(p) > 2 else 0.0

    return {"x": x, "y": y, "z": z}

def convert_entity(e):
    out = {
        "source_file": e.get("source_file", ""),
        "type": e.get("type", ""),
        "layer": e.get("layer", ""),
        "color": int(e.get("color", 0) or 0),
        "linetype": e.get("linetype", ""),
        "closed": bool(e.get("closed", False)),
        "radius": float(e.get("radius", 0.0) or 0.0),
        "height": float(e.get("height", 0.0) or 0.0),
        "rotation": float(e.get("rotation", 0.0) or 0.0),
        "text": e.get("text", ""),
        "block_name": e.get("block_name", ""),
        "points": [],
        "center": {"x": 0.0, "y": 0.0, "z": 0.0},
        "position": {"x": 0.0, "y": 0.0, "z": 0.0},
        "has_center": False,
        "has_position": False,
        "has_points": False,
    }

    if isinstance(e.get("points"), list):
        out["points"] = [to_point_obj(p) for p in e.get("points", [])]
        out["has_points"] = len(out["points"]) > 0

    if isinstance(e.get("center"), list):
        out["center"] = to_point_obj(e.get("center"))
        out["has_center"] = True

    if isinstance(e.get("position"), list):
        out["position"] = to_point_obj(e.get("position"))
        out["has_position"] = True

    return out

def main():
    print("Unity용 JSON 변환 시작")
    print("SRC:", SRC_DIR)
    print("DST:", DST_DIR)

    for file_name in TARGET_FILES:
        src = os.path.join(SRC_DIR, file_name)
        dst = os.path.join(DST_DIR, file_name)

        if not os.path.exists(src):
            print("없음:", src)
            continue

        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)

        unity_data = {
            "group": data.get("group", ""),
            "entity_count": int(data.get("entity_count", 0) or 0),
            "entities": [convert_entity(e) for e in data.get("entities", [])]
        }

        with open(dst, "w", encoding="utf-8") as f:
            json.dump(unity_data, f, ensure_ascii=False, indent=2)

        print(f"변환 완료: {file_name} / {len(unity_data['entities'])}")

    print("")
    print("완료")
    print(DST_DIR)

if __name__ == "__main__":
    main()
