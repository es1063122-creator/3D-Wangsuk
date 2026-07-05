import os
import json
import ezdxf

try:
    from ezdxf.disassemble import recursive_decompose
    HAS_RECURSIVE = True
except Exception:
    HAS_RECURSIVE = False

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

GA_DIR = os.path.join(
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
    "Review"
)

os.makedirs(OUT_DIR, exist_ok=True)

TARGET_FILES = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

TARGET_LAYERS = ["STRUT", "C-STRUT", "BEAM-BRACING"]

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

def pnt(x, y, z=0):
    return {"x": float(x), "y": float(y), "z": float(z)}

def get_points(e):
    t = e.dxftype()

    try:
        if t == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            return [pnt(s.x, s.y, s.z), pnt(en.x, en.y, en.z)]

        if t == "LWPOLYLINE":
            return [pnt(v[0], v[1], 0) for v in e.get_points()]

        if t == "POLYLINE":
            pts = []
            for v in e.vertices:
                loc = v.dxf.location
                pts.append(pnt(loc.x, loc.y, loc.z))
            return pts
    except Exception:
        return []

    return []

def main():
    result = {
        "files": {},
        "entities": []
    }

    for fname in os.listdir(GA_DIR):
        if not fname.lower().endswith(".dxf"):
            continue

        if not any(fname.startswith(t) for t in TARGET_FILES):
            continue

        path = os.path.join(GA_DIR, fname)
        print("분석:", fname)

        try:
            doc = ezdxf.readfile(path)
            ents = decompose_entities(doc.modelspace())

            file_count = 0
            layer_count = {}

            for e in ents:
                try:
                    layer = str(e.dxf.layer).strip()
                except Exception:
                    continue

                if layer.upper() not in [x.upper() for x in TARGET_LAYERS]:
                    continue

                pts = get_points(e)
                if len(pts) < 2:
                    continue

                item = {
                    "file": fname,
                    "layer": layer,
                    "type": e.dxftype(),
                    "points": pts
                }

                result["entities"].append(item)
                file_count += 1
                layer_count[layer] = layer_count.get(layer, 0) + 1

            result["files"][fname] = {
                "count": file_count,
                "layers": layer_count
            }

        except Exception as ex:
            print("오류:", fname, ex)

    out_json = os.path.join(OUT_DIR, "development_strut_entities.json")
    out_txt = os.path.join(OUT_DIR, "development_strut_entities_summary.txt")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("굴착계획 전개도 STRUT 도형 추출 요약\n")
        f.write("=" * 100 + "\n\n")

        for fname, info in result["files"].items():
            f.write(f"{fname}\n")
            f.write(f"  count: {info['count']}\n")
            for layer, count in info["layers"].items():
                f.write(f"  {layer}: {count}\n")
            f.write("\n")

        f.write("=" * 100 + "\n")
        f.write(f"TOTAL: {len(result['entities'])}\n")

    print("")
    print("완료")
    print("TOTAL:", len(result["entities"]))
    print(out_txt)

if __name__ == "__main__":
    main()
