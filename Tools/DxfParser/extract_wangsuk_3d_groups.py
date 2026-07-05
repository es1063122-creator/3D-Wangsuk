import os
import json
import math
from collections import defaultdict

import ezdxf


PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_CAD_3D"
SOURCE_DIR = os.path.join(PROJECT_ROOT, "Assets", "StreamingAssets", "WangsukDXF", "SourceDXF", "unzipped")
OUT_DIR = os.path.join(PROJECT_ROOT, "Assets", "StreamingAssets", "WangsukDXF", "ParsedJson")

os.makedirs(OUT_DIR, exist_ok=True)


GROUP_RULES = {
    "PF_HPILE": [
        "__PILE", "H-PILE", "C-PILE", "HPILE", "HPILE1", "PW1"
    ],
    "CIP": [
        "CIP", "__CIP"
    ],
    "WALE": [
        "WALE", "C-WALE", "__WALE", "-$$WALE"
    ],
    "ANCHOR": [
        "ANCHOR", "C-ANCH-FREE", "C-ANCH-BOND"
    ],
    "CORNER_STRUT": [
        "STRUT", "C-STRUT"
    ],
    "EXCAVATION": [
        "-$$굴착심도", "-$$굴착선"
    ],
    "GROUND_GL": [
        "GL", "@원지반"
    ],
    "SECTION_LINES": [
        "횡단면도-표시선", "@SECTION", "단면위치", "단면", "$ 단면", "_CQ_공사-단면선", "$$단면체인"
    ],
    "GRID": [
        "그리드선", "_CR_수직그리드", "_CR_수평그리드", "A-FLOR-GRID", "BASE$0$A-FLOR-GRID"
    ],
    "LABELS": [
        "TEXT", "Text", "-$$TEXT", "-$$범례TEXT", "FTEXT", "TEXT-ER", "ZM_TEXT",
        "XR-TEXT", "00-TEXT", "배치-Text-Dong", "A-TEXT03", "BASE$0$TEXT",
        "TEXT1", "TEXT-6", "0-TEXT", "dp-text", "FORM-TEXT", "$EL-text",
        "dtext", "TEXT-2", "상수text", "TEXT02", "CH-TEXT"
    ],
    "BUILDING_PARKING": [
        "동딱지PD", "동딱지OUTLINE", "동딱지OUTLINE_코어", "동딱지SERVICE",
        "지하주차장 OUTLINE", "BASE$0$지하주차장 OUTLINE",
        "!S_7.FooT", "1.공사-계획 사면", "-bs-[PLAN]조경선"
    ],
}


def normalize_layer(layer):
    return str(layer).strip()


def layer_to_group(layer):
    l = normalize_layer(layer)
    lu = l.upper()

    for group, names in GROUP_RULES.items():
        for n in names:
            if lu == n.upper():
                return group

    return None


def safe_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def get_color(e):
    try:
        return int(e.dxf.color)
    except Exception:
        return 256


def get_linetype(e):
    try:
        return str(e.dxf.linetype)
    except Exception:
        return ""


def point3(p):
    return [safe_float(p[0]), safe_float(p[1]), safe_float(p[2]) if len(p) > 2 else 0.0]


def extract_entity(e, source_file):
    t = e.dxftype()
    layer = normalize_layer(getattr(e.dxf, "layer", "NO_LAYER"))

    base = {
        "source_file": source_file,
        "type": t,
        "layer": layer,
        "color": get_color(e),
        "linetype": get_linetype(e),
    }

    try:
        if t == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            base["points"] = [
                [safe_float(s.x), safe_float(s.y), safe_float(s.z)],
                [safe_float(en.x), safe_float(en.y), safe_float(en.z)],
            ]
            return base

        if t == "LWPOLYLINE":
            pts = []
            for p in e.get_points():
                pts.append([safe_float(p[0]), safe_float(p[1]), 0.0])
            base["points"] = pts
            try:
                base["closed"] = bool(e.closed)
            except Exception:
                base["closed"] = False
            return base

        if t == "POLYLINE":
            pts = []
            for v in e.vertices:
                loc = v.dxf.location
                pts.append([safe_float(loc.x), safe_float(loc.y), safe_float(loc.z)])
            base["points"] = pts
            try:
                base["closed"] = bool(e.is_closed)
            except Exception:
                base["closed"] = False
            return base

        if t == "CIRCLE":
            c = e.dxf.center
            base["center"] = [safe_float(c.x), safe_float(c.y), safe_float(c.z)]
            base["radius"] = safe_float(e.dxf.radius)
            return base

        if t == "ARC":
            c = e.dxf.center
            base["center"] = [safe_float(c.x), safe_float(c.y), safe_float(c.z)]
            base["radius"] = safe_float(e.dxf.radius)
            base["start_angle"] = safe_float(e.dxf.start_angle)
            base["end_angle"] = safe_float(e.dxf.end_angle)
            return base

        if t == "TEXT":
            ins = e.dxf.insert
            base["position"] = [safe_float(ins.x), safe_float(ins.y), safe_float(ins.z)]
            base["text"] = str(e.dxf.text)
            base["height"] = safe_float(e.dxf.height)
            try:
                base["rotation"] = safe_float(e.dxf.rotation)
            except Exception:
                base["rotation"] = 0.0
            return base

        if t == "MTEXT":
            ins = e.dxf.insert
            base["position"] = [safe_float(ins.x), safe_float(ins.y), safe_float(ins.z)]
            base["text"] = str(e.text)
            try:
                base["height"] = safe_float(e.dxf.char_height)
            except Exception:
                base["height"] = 0.0
            try:
                base["rotation"] = safe_float(e.dxf.rotation)
            except Exception:
                base["rotation"] = 0.0
            return base

        if t == "INSERT":
            ins = e.dxf.insert
            base["position"] = [safe_float(ins.x), safe_float(ins.y), safe_float(ins.z)]
            base["block_name"] = str(e.dxf.name)
            try:
                base["rotation"] = safe_float(e.dxf.rotation)
            except Exception:
                base["rotation"] = 0.0
            try:
                base["xscale"] = safe_float(e.dxf.xscale)
                base["yscale"] = safe_float(e.dxf.yscale)
                base["zscale"] = safe_float(e.dxf.zscale)
            except Exception:
                pass
            return base

    except Exception as ex:
        base["error"] = str(ex)
        return base

    return None


def update_bounds(bounds, entity):
    pts = []

    if "points" in entity:
        pts.extend(entity["points"])
    if "center" in entity:
        pts.append(entity["center"])
    if "position" in entity:
        pts.append(entity["position"])

    for p in pts:
        x, y, z = p[0], p[1], p[2]
        bounds["min_x"] = min(bounds["min_x"], x)
        bounds["min_y"] = min(bounds["min_y"], y)
        bounds["min_z"] = min(bounds["min_z"], z)
        bounds["max_x"] = max(bounds["max_x"], x)
        bounds["max_y"] = max(bounds["max_y"], y)
        bounds["max_z"] = max(bounds["max_z"], z)


def new_bounds():
    return {
        "min_x": 999999999999,
        "min_y": 999999999999,
        "min_z": 999999999999,
        "max_x": -999999999999,
        "max_y": -999999999999,
        "max_z": -999999999999,
    }


def main():
    groups = {}
    for g in GROUP_RULES.keys():
        groups[g] = {
            "group": g,
            "entities": [],
            "bounds": new_bounds(),
            "entity_count": 0,
            "layer_counts": defaultdict(int),
            "type_counts": defaultdict(int),
        }

    dxf_files = []
    for root, dirs, files in os.walk(SOURCE_DIR):
        for f in files:
            if f.lower().endswith(".dxf"):
                dxf_files.append(os.path.join(root, f))

    print(f"DXF 파일 수: {len(dxf_files)}")
    print("3D 생성용 그룹 추출 시작")

    for idx, path in enumerate(dxf_files, start=1):
        source_file = os.path.relpath(path, SOURCE_DIR)
        print(f"[{idx}/{len(dxf_files)}] {source_file}")

        try:
            doc = ezdxf.readfile(path)
            msp = doc.modelspace()

            for e in msp:
                layer = normalize_layer(getattr(e.dxf, "layer", "NO_LAYER"))
                group = layer_to_group(layer)

                if not group:
                    continue

                entity = extract_entity(e, source_file)
                if not entity:
                    continue

                groups[group]["entities"].append(entity)
                groups[group]["entity_count"] += 1
                groups[group]["layer_counts"][entity["layer"]] += 1
                groups[group]["type_counts"][entity["type"]] += 1
                update_bounds(groups[group]["bounds"], entity)

        except Exception as ex:
            print(f"  오류: {source_file} / {ex}")

    summary = {
        "project": "Wangsuk A-6BL CAD/DXF 3D",
        "source_dir": SOURCE_DIR,
        "groups": []
    }

    for group_name, data in groups.items():
        data["layer_counts"] = dict(sorted(data["layer_counts"].items(), key=lambda x: x[1], reverse=True))
        data["type_counts"] = dict(sorted(data["type_counts"].items(), key=lambda x: x[1], reverse=True))

        out_path = os.path.join(OUT_DIR, f"wangsuk_{group_name.lower()}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        summary["groups"].append({
            "group": group_name,
            "entity_count": data["entity_count"],
            "bounds": data["bounds"],
            "layer_counts": data["layer_counts"],
            "type_counts": data["type_counts"],
            "file": os.path.basename(out_path)
        })

    summary_path = os.path.join(OUT_DIR, "wangsuk_3d_groups_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("")
    print("완료")
    print(summary_path)

    print("")
    print("===== 그룹별 추출 수량 =====")
    for g in summary["groups"]:
        print(f"{g['group']:20s} {g['entity_count']:8d}  -> {g['file']}")


if __name__ == "__main__":
    main()
