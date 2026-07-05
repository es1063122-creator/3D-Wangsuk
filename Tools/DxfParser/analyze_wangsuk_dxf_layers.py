import os
import json
import zipfile
from collections import defaultdict, Counter

import ezdxf


PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_CAD_3D"
SOURCE_DIR = os.path.join(PROJECT_ROOT, "Assets", "StreamingAssets", "WangsukDXF", "SourceDXF", "unzipped")
OUT_DIR = os.path.join(PROJECT_ROOT, "Assets", "StreamingAssets", "WangsukDXF", "ParsedJson")

os.makedirs(OUT_DIR, exist_ok=True)


def safe_float(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def entity_points(e):
    points = []

    try:
        t = e.dxftype()

        if t == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            points.append([safe_float(s.x), safe_float(s.y), safe_float(s.z)])
            points.append([safe_float(en.x), safe_float(en.y), safe_float(en.z)])

        elif t in ["LWPOLYLINE", "POLYLINE"]:
            if t == "LWPOLYLINE":
                for p in e.get_points():
                    points.append([safe_float(p[0]), safe_float(p[1]), 0.0])
            else:
                for v in e.vertices:
                    loc = v.dxf.location
                    points.append([safe_float(loc.x), safe_float(loc.y), safe_float(loc.z)])

        elif t in ["CIRCLE", "ARC"]:
            c = e.dxf.center
            points.append([safe_float(c.x), safe_float(c.y), safe_float(c.z)])

        elif t in ["TEXT", "MTEXT"]:
            ins = e.dxf.insert
            points.append([safe_float(ins.x), safe_float(ins.y), safe_float(ins.z)])

        elif t == "INSERT":
            ins = e.dxf.insert
            points.append([safe_float(ins.x), safe_float(ins.y), safe_float(ins.z)])

    except Exception:
        pass

    return points


def update_bounds(bounds, pts):
    for x, y, z in pts:
        bounds["min_x"] = min(bounds["min_x"], x)
        bounds["min_y"] = min(bounds["min_y"], y)
        bounds["min_z"] = min(bounds["min_z"], z)
        bounds["max_x"] = max(bounds["max_x"], x)
        bounds["max_y"] = max(bounds["max_y"], y)
        bounds["max_z"] = max(bounds["max_z"], z)


def analyze_dxf(path):
    result = {
        "file": path,
        "file_name": os.path.basename(path),
        "layer_counts": {},
        "entity_type_counts": {},
        "layer_entity_type_counts": {},
        "bounds": {
            "min_x": 999999999999,
            "min_y": 999999999999,
            "min_z": 999999999999,
            "max_x": -999999999999,
            "max_y": -999999999999,
            "max_z": -999999999999,
        },
        "texts": [],
    }

    try:
        doc = ezdxf.readfile(path)
        msp = doc.modelspace()

        layer_counter = Counter()
        type_counter = Counter()
        layer_type_counter = defaultdict(Counter)

        for e in msp:
            t = e.dxftype()
            layer = getattr(e.dxf, "layer", "NO_LAYER")

            layer_counter[layer] += 1
            type_counter[t] += 1
            layer_type_counter[layer][t] += 1

            pts = entity_points(e)
            update_bounds(result["bounds"], pts)

            if t in ["TEXT", "MTEXT"]:
                try:
                    text_value = e.dxf.text if t == "TEXT" else e.text
                    ins = e.dxf.insert
                    result["texts"].append({
                        "layer": layer,
                        "type": t,
                        "text": str(text_value),
                        "x": safe_float(ins.x),
                        "y": safe_float(ins.y),
                        "z": safe_float(ins.z),
                    })
                except Exception:
                    pass

        result["layer_counts"] = dict(layer_counter.most_common())
        result["entity_type_counts"] = dict(type_counter.most_common())
        result["layer_entity_type_counts"] = {
            layer: dict(counter.most_common())
            for layer, counter in layer_type_counter.items()
        }

    except Exception as ex:
        result["error"] = str(ex)

    return result


def main():
    dxf_files = []
    for root, dirs, files in os.walk(SOURCE_DIR):
        for f in files:
            if f.lower().endswith(".dxf"):
                dxf_files.append(os.path.join(root, f))

    all_results = []
    global_layer_counts = Counter()
    global_entity_counts = Counter()

    for idx, path in enumerate(dxf_files, start=1):
        print(f"[{idx}/{len(dxf_files)}] 분석 중: {path}")
        r = analyze_dxf(path)
        all_results.append(r)

        for layer, count in r.get("layer_counts", {}).items():
            global_layer_counts[layer] += count

        for etype, count in r.get("entity_type_counts", {}).items():
            global_entity_counts[etype] += count

    summary = {
        "total_dxf_files": len(dxf_files),
        "global_layer_counts": dict(global_layer_counts.most_common()),
        "global_entity_type_counts": dict(global_entity_counts.most_common()),
        "files": all_results,
    }

    out_path = os.path.join(OUT_DIR, "wangsuk_dxf_analysis_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("")
    print("완료")
    print(out_path)


if __name__ == "__main__":
    main()
