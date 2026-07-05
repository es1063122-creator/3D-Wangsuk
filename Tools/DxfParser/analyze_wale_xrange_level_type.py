import os
import re
import math
import json
from pathlib import Path
from collections import defaultdict

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
    "Review"
)

os.makedirs(OUT_DIR, exist_ok=True)

OUT_TXT = os.path.join(OUT_DIR, "wale_xrange_level_type_review.txt")
OUT_JSON = os.path.join(OUT_DIR, "wale_xrange_level_type_review.json")

TARGETS = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

PILE_RANGES = {
    "C-612": "P001~P067",
    "C-613": "P067~P131",
    "C-614": "P131~P196",
    "C-615": "P196~P248",
    "C-616": "P248~P306",
    "C-617": "P306~P365",
    "C-618": "P365~P428",
    "C-619": "P428~P492,P001",
}

def read_pairs(path):
    lines = Path(path).read_text(encoding="cp949", errors="ignore").splitlines()
    pairs = []

    i = 0
    while i < len(lines) - 1:
        try:
            code = int(lines[i].strip())
            val = lines[i + 1].strip()
            pairs.append((code, val))
        except:
            pass
        i += 2

    return pairs

def parse_entities(path):
    pairs = read_pairs(path)
    ents = []
    in_entities = False
    cur = None

    for code, val in pairs:
        if code == 2 and val == "ENTITIES":
            in_entities = True
            continue

        if code == 0 and val == "ENDSEC":
            in_entities = False
            continue

        if not in_entities:
            continue

        if code == 0:
            if cur is not None:
                ents.append(cur)
            cur = {"type": val, "pairs": []}
        else:
            if cur is not None:
                cur["pairs"].append((code, val))

    if cur is not None:
        ents.append(cur)

    result = []

    for e in ents:
        typ = e["type"]
        ps = e["pairs"]

        layer = ""
        for c, v in ps:
            if c == 8:
                layer = v
                break

        obj = {
            "type": typ,
            "layer": layer,
            "points": [],
            "text": "",
            "x": None,
            "y": None
        }

        if typ in ["TEXT", "MTEXT"]:
            txts = []
            for c, v in ps:
                if c in [1, 3]:
                    txts.append(v)
            obj["text"] = "".join(txts)

            for c, v in ps:
                if c == 10 and obj["x"] is None:
                    try: obj["x"] = float(v)
                    except: pass
                if c == 20 and obj["y"] is None:
                    try: obj["y"] = float(v)
                    except: pass

        elif typ == "LINE":
            vals = {}
            for c, v in ps:
                if c in [10, 20, 11, 21]:
                    try: vals[c] = float(v)
                    except: pass
            if all(k in vals for k in [10,20,11,21]):
                obj["points"] = [(vals[10], vals[20]), (vals[11], vals[21])]

        elif typ == "LWPOLYLINE":
            pts = []
            last_x = None
            for c, v in ps:
                if c == 10:
                    try: last_x = float(v)
                    except: last_x = None
                elif c == 20 and last_x is not None:
                    try: pts.append((last_x, float(v)))
                    except: pass
                    last_x = None
            obj["points"] = pts

        result.append(obj)

    return result

def find_files():
    files = []
    for fname in os.listdir(DXF_DIR):
        if not fname.lower().endswith(".dxf"):
            continue
        if any(fname.startswith(t) for t in TARGETS):
            files.append(os.path.join(DXF_DIR, fname))
    return sorted(files)

def length(pts):
    if not pts or len(pts) < 2:
        return 0
    total = 0
    for i in range(len(pts)-1):
        x1, y1 = pts[i]
        x2, y2 = pts[i+1]
        total += math.hypot(x2-x1, y2-y1)
    return total

def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

def broad_cluster_y(rows, tol=650.0):
    # rows: dict with y_mid
    rows = sorted(rows, key=lambda r: r["y_mid"])
    clusters = []

    for r in rows:
        if not clusters:
            clusters.append([r])
            continue

        cur_avg = sum(x["y_mid"] for x in clusters[-1]) / len(clusters[-1])
        if abs(r["y_mid"] - cur_avg) <= tol:
            clusters[-1].append(r)
        else:
            clusters.append([r])

    return clusters

def merge_x_ranges(rows, gap_tol=1600.0):
    ranges = []
    for r in rows:
        ranges.append([r["x_min"], r["x_max"], r["length"], r["layer"]])

    ranges.sort(key=lambda x: x[0])
    merged = []

    for rg in ranges:
        if not merged:
            merged.append(rg)
            continue

        if rg[0] <= merged[-1][1] + gap_tol:
            merged[-1][1] = max(merged[-1][1], rg[1])
            merged[-1][2] += rg[2]
            merged[-1][3] += "," + rg[3]
        else:
            merged.append(rg)

    return merged

def classify_type(cluster_rows):
    # 도면에서 2H는 같은 높이군 안에 평행선이 많이 생김.
    # 여기서는 선 개수와 텍스트 표기를 함께 판단할 예정.
    count = len(cluster_rows)
    long_count = len([r for r in cluster_rows if r["length"] >= 2000])

    if count >= 4 or long_count >= 4:
        return "2H 후보"
    if count >= 2:
        return "H 또는 2H 후보"
    return "H 후보"

def nearby_texts(texts, x_min, x_max, y_min, y_max, x_pad=6000, y_pad=4500):
    hits = []
    for t in texts:
        x = t.get("x")
        y = t.get("y")
        if x is None or y is None:
            continue

        if x_min - x_pad <= x <= x_max + x_pad and y_min - y_pad <= y <= y_max + y_pad:
            s = t.get("text", "")
            if any(k in s.upper() for k in ["WALE", "H-300", "2H-300", "ANCHOR", "EL(+", "PILE NO"]):
                hits.append(s)
    return hits

def main():
    result = []

    for path in find_files():
        fname = os.path.basename(path)
        cno = fname.split()[0]
        ents = parse_entities(path)

        texts = [e for e in ents if e["type"] in ["TEXT", "MTEXT"] and e.get("text")]
        wale_rows = []

        for e in ents:
            layer_u = e["layer"].upper()

            if "WALE" not in layer_u:
                continue

            pts = e["points"]
            if not pts or len(pts) < 2:
                continue

            l = length(pts)
            if l < 400:
                continue

            x0, y0, x1, y1 = bbox(pts)
            y_mid = (y0 + y1) * 0.5

            wale_rows.append({
                "layer": e["layer"],
                "type": e["type"],
                "x_min": x0,
                "x_max": x1,
                "y_min": y0,
                "y_max": y1,
                "y_mid": y_mid,
                "length": l
            })

        clusters = broad_cluster_y(wale_rows, tol=650.0)

        file_result = {
            "file": fname,
            "pile_range": PILE_RANGES.get(cno, ""),
            "clusters": []
        }

        for idx, cl in enumerate(clusters, start=1):
            x_min = min(r["x_min"] for r in cl)
            x_max = max(r["x_max"] for r in cl)
            y_min = min(r["y_min"] for r in cl)
            y_max = max(r["y_max"] for r in cl)
            y_avg = sum(r["y_mid"] for r in cl) / len(cl)

            xranges = merge_x_ranges(cl)
            ntexts = nearby_texts(texts, x_min, x_max, y_min, y_max)

            type_guess = classify_type(cl)

            # 주변 텍스트로 보정
            joined = " / ".join(ntexts)
            if "2H-300" in joined:
                type_guess = "2H 더블띠장"
            elif "H-300" in joined and "2H-300" not in joined:
                type_guess = "H 단띠장 후보"

            file_result["clusters"].append({
                "level_index_bottom_to_top": idx,
                "y_avg": y_avg,
                "y_min": y_min,
                "y_max": y_max,
                "x_min": x_min,
                "x_max": x_max,
                "entity_count": len(cl),
                "type_guess": type_guess,
                "x_ranges": [
                    {
                        "x_min": rg[0],
                        "x_max": rg[1],
                        "sum_length": rg[2],
                        "layers": rg[3]
                    } for rg in xranges
                ],
                "near_texts": sorted(set(ntexts))
            })

        result.append(file_result)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-612~C-619 WALE x범위/높이/형식 자동 판독표\n")
        f.write("=" * 120 + "\n\n")
        f.write("주의: 이 표는 코드 수정 전 검토용입니다. 도면 이미지와 반드시 대조해야 합니다.\n\n")

        for item in result:
            f.write("\n" + "=" * 120 + "\n")
            f.write(f"{item['file']} / {item['pile_range']}\n")
            f.write("=" * 120 + "\n")

            if not item["clusters"]:
                f.write("WALE cluster 없음\n")
                continue

            # 위에서 아래 순서로 보기 좋게 출력
            for cl in sorted(item["clusters"], key=lambda x: -x["y_avg"]):
                f.write("\n")
                f.write(f"[HEIGHT GROUP] y_avg={cl['y_avg']:.1f}, y_range={cl['y_min']:.1f}~{cl['y_max']:.1f}, entity_count={cl['entity_count']}\n")
                f.write(f"형식 후보: {cl['type_guess']}\n")
                f.write(f"전체 x범위: {cl['x_min']:.1f} ~ {cl['x_max']:.1f}\n")

                f.write("x-range 분할:\n")
                for rg in cl["x_ranges"]:
                    f.write(f"  - x={rg['x_min']:.1f} ~ {rg['x_max']:.1f}, length_sum={rg['sum_length']:.1f}\n")

                if cl["near_texts"]:
                    f.write("주변 텍스트:\n")
                    for t in cl["near_texts"]:
                        f.write(f"  - {t}\n")

    print("완료")
    print(OUT_TXT)
    print(OUT_JSON)

if __name__ == "__main__":
    main()
