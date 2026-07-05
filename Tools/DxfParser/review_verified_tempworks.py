import os
import json
import math
import ezdxf
from collections import defaultdict

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
    "C-605",
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619",
    "C-620", "C-621", "C-622", "C-623", "C-624", "C-625"
]

LAYER_KEYS = [
    "STRUT",
    "BEAM-BRACING",
    "C-STRUT",
    "WALE",
    "C-WALE",
    "ANCH",
    "앵커"
]

TEXT_KEYS = [
    "STRUT",
    "CORNER STRUT",
    "WALE",
    "띠장",
    "버팀",
    "버팀대",
    "경사 버팀",
    "코너",
    "H-300",
    "2H-300",
    "H-300x300x10x15",
    "2H-300x300x10x15",
    "H-300X300X10X15",
    "2H-300X300X10X15",
    "E/ANCHOR",
    "ANCHOR",
    "제거식",
    "EL",
    "GL",
    "G.L",
    "굴착심도",
    "시공하한선"
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

def hit_any(value, keys):
    u = str(value).upper()
    return any(k.upper() in u for k in keys)

def get_text(e):
    try:
        if e.dxftype() == "TEXT":
            return str(e.dxf.text).strip()
        if e.dxftype() == "MTEXT":
            return str(e.text).strip()
    except Exception:
        return ""
    return ""

def get_text_pos(e):
    try:
        p = e.dxf.insert
        return float(p.x), float(p.y), float(p.z)
    except Exception:
        return 0.0, 0.0, 0.0

def get_points(e):
    t = e.dxftype()

    try:
        if t == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            return [(float(s.x), float(s.y), float(s.z)), (float(en.x), float(en.y), float(en.z))]

        if t == "LWPOLYLINE":
            return [(float(v[0]), float(v[1]), 0.0) for v in e.get_points()]

        if t == "POLYLINE":
            pts = []
            for v in e.vertices:
                loc = v.dxf.location
                pts.append((float(loc.x), float(loc.y), float(loc.z)))
            return pts
    except Exception:
        return []

    return []

def mid_point(pts):
    if not pts:
        return 0.0, 0.0, 0.0
    x = sum(p[0] for p in pts) / len(pts)
    y = sum(p[1] for p in pts) / len(pts)
    z = sum(p[2] for p in pts) / len(pts)
    return x, y, z

def length_2d(pts):
    if len(pts) < 2:
        return 0.0
    a = pts[0]
    b = pts[-1]
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return math.sqrt(dx * dx + dy * dy)

def cluster_y(rows, tolerance=5000.0):
    valid = [r for r in rows if r.get("mid_y") is not None]
    valid.sort(key=lambda r: r["mid_y"])

    clusters = []
    for r in valid:
        if not clusters:
            clusters.append([r])
            continue

        avg_y = sum(x["mid_y"] for x in clusters[-1]) / len(clusters[-1])

        if abs(r["mid_y"] - avg_y) <= tolerance:
            clusters[-1].append(r)
        else:
            clusters.append([r])

    infos = []
    for c in clusters:
        avg_y = sum(x["mid_y"] for x in c) / len(c)
        avg_len = sum(x.get("length", 0.0) for x in c) / len(c)
        min_x = min(x["mid_x"] for x in c)
        max_x = max(x["mid_x"] for x in c)
        infos.append({
            "avg_y": avg_y,
            "count": len(c),
            "avg_len": avg_len,
            "min_x": min_x,
            "max_x": max_x
        })

    infos.sort(key=lambda x: x["avg_y"], reverse=True)
    return infos

def main():
    files = []
    for fname in os.listdir(GA_DIR):
        if not fname.lower().endswith(".dxf"):
            continue
        if any(fname.startswith(t) for t in TARGET_FILES):
            files.append(fname)

    files.sort()

    report = {
        "files": {},
        "texts": [],
        "geometry": []
    }

    for fname in files:
        path = os.path.join(GA_DIR, fname)
        print("분석:", fname)

        try:
            doc = ezdxf.readfile(path)
            ents = decompose_entities(doc.modelspace())

            layer_counts = defaultdict(int)
            layer_geometry = defaultdict(list)
            text_hits = []

            for e in ents:
                try:
                    layer = str(e.dxf.layer).strip()
                except Exception:
                    layer = ""

                etype = e.dxftype()

                if hit_any(layer, LAYER_KEYS):
                    layer_counts[layer] += 1

                    pts = get_points(e)
                    if len(pts) >= 2:
                        mx, my, mz = mid_point(pts)
                        item = {
                            "file": fname,
                            "layer": layer,
                            "type": etype,
                            "mid_x": mx,
                            "mid_y": my,
                            "mid_z": mz,
                            "length": length_2d(pts),
                            "point_count": len(pts)
                        }
                        report["geometry"].append(item)
                        layer_geometry[layer.upper()].append(item)

                if etype in ["TEXT", "MTEXT"]:
                    txt = get_text(e)
                    if txt and hit_any(txt, TEXT_KEYS):
                        x, y, z = get_text_pos(e)
                        titem = {
                            "file": fname,
                            "layer": layer,
                            "text": txt,
                            "x": x,
                            "y": y,
                            "z": z
                        }
                        report["texts"].append(titem)
                        text_hits.append(titem)

            file_info = {
                "layer_counts": dict(sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)),
                "clusters": {}
            }

            for key in ["STRUT", "BEAM-BRACING", "C-STRUT", "WALE", "C-WALE"]:
                rows = []
                for layer_name, arr in layer_geometry.items():
                    if key.upper() == layer_name.upper():
                        rows.extend(arr)

                file_info["clusters"][key] = cluster_y(rows, tolerance=5000.0)

            report["files"][fname] = file_info

        except Exception as ex:
            print("오류:", fname, ex)

    out_json = os.path.join(OUT_DIR, "temporary_works_verified_review.json")
    out_txt = os.path.join(OUT_DIR, "temporary_works_verified_review.txt")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("가시설 CAD 검토표 - STRUT / CORNER STRUT / WALE / 상세 규격\n")
        f.write("=" * 140 + "\n\n")

        f.write("[1] 파일별 관련 레이어 수 및 높이군\n")
        for fname, info in report["files"].items():
            f.write("=" * 140 + "\n")
            f.write(f"FILE: {fname}\n")
            f.write("LAYER COUNTS:\n")
            for layer, cnt in info["layer_counts"].items():
                f.write(f"  {layer:35s} {cnt}\n")

            f.write("\nY CLUSTERS:\n")
            for key, clusters in info["clusters"].items():
                f.write(f"  [{key}] cluster_count={len(clusters)}\n")
                for idx, c in enumerate(clusters, start=1):
                    f.write(
                        f"    후보 {idx}단 | avg_y={c['avg_y']:.3f} | "
                        f"count={c['count']} | avg_len={c['avg_len']:.1f} | "
                        f"x_range={c['min_x']:.1f} ~ {c['max_x']:.1f}\n"
                    )
            f.write("\n")

        f.write("\n\n[2] 핵심 텍스트 위치\n")
        for t in sorted(report["texts"], key=lambda x: (x["file"], -x["y"], x["x"])):
            if any(k.upper() in t["text"].upper() for k in ["CORNER STRUT", "WALE", "H-300", "2H-300", "버팀", "띠장"]):
                f.write("=" * 140 + "\n")
                f.write(f"FILE : {t['file']}\n")
                f.write(f"LAYER: {t['layer']}\n")
                f.write(f"POS  : x={t['x']:.1f}, y={t['y']:.1f}\n")
                f.write(f"TEXT : {t['text']}\n")

    print("")
    print("완료")
    print(out_txt)

if __name__ == "__main__":
    main()
