import os
import re
import math
import json
from pathlib import Path

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

OUT_TXT = os.path.join(OUT_DIR, "wale_band_final_review.txt")
OUT_JSON = os.path.join(OUT_DIR, "wale_band_final_review.json")

TARGETS = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

PILE_RANGE_TEXT = {
    "C-612": "P001~P067",
    "C-613": "P067~P131",
    "C-614": "P131~P196",
    "C-615": "P196~P248",
    "C-616": "P248~P306",
    "C-617": "P306~P365",
    "C-618": "P365~P428",
    "C-619": "P428~P492,P001",
}

PILE_RANGE_NUMS = {
    "C-612": list(range(1, 68)),
    "C-613": list(range(67, 132)),
    "C-614": list(range(131, 197)),
    "C-615": list(range(196, 249)),
    "C-616": list(range(248, 307)),
    "C-617": list(range(306, 366)),
    "C-618": list(range(365, 429)),
    "C-619": list(range(428, 493)) + [1],
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
                    try:
                        obj["x"] = float(v)
                    except:
                        pass
                if c == 20 and obj["y"] is None:
                    try:
                        obj["y"] = float(v)
                    except:
                        pass

        elif typ == "LINE":
            vals = {}
            for c, v in ps:
                if c in [10, 20, 11, 21]:
                    try:
                        vals[c] = float(v)
                    except:
                        pass

            if all(k in vals for k in [10, 20, 11, 21]):
                obj["points"] = [
                    (vals[10], vals[20]),
                    (vals[11], vals[21])
                ]

        elif typ == "LWPOLYLINE":
            pts = []
            last_x = None
            for c, v in ps:
                if c == 10:
                    try:
                        last_x = float(v)
                    except:
                        last_x = None
                elif c == 20 and last_x is not None:
                    try:
                        pts.append((last_x, float(v)))
                    except:
                        pass
                    last_x = None
            obj["points"] = pts

        result.append(obj)

    return result

def length(pts):
    if not pts or len(pts) < 2:
        return 0.0
    total = 0.0
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        total += math.hypot(x2 - x1, y2 - y1)
    return total

def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

def find_files():
    files = []
    for fname in os.listdir(DXF_DIR):
        if not fname.lower().endswith(".dxf"):
            continue
        if any(fname.startswith(t) for t in TARGETS):
            files.append(os.path.join(DXF_DIR, fname))
    return sorted(files)

def cluster_y(rows, tol=180.0):
    rows = sorted(rows, key=lambda r: r["y_mid"])
    clusters = []

    for r in rows:
        if not clusters:
            clusters.append([r])
            continue

        avg = sum(x["y_mid"] for x in clusters[-1]) / len(clusters[-1])
        if abs(r["y_mid"] - avg) <= tol:
            clusters[-1].append(r)
        else:
            clusters.append([r])

    out = []
    for cl in clusters:
        out.append({
            "rows": cl,
            "y_avg": sum(r["y_mid"] for r in cl) / len(cl),
            "y_min": min(r["y_min"] for r in cl),
            "y_max": max(r["y_max"] for r in cl),
            "x_min": min(r["x_min"] for r in cl),
            "x_max": max(r["x_max"] for r in cl),
            "count": len(cl),
        })
    return out

def collapse_to_bands(micro_clusters, gap_tol=1200.0, max_band_height=1800.0):
    micro_clusters = sorted(micro_clusters, key=lambda c: c["y_avg"])
    bands = []

    for mc in micro_clusters:
        if not bands:
            bands.append([mc])
            continue

        cur = bands[-1]
        cur_min = min(x["y_avg"] for x in cur)
        cur_max = max(x["y_avg"] for x in cur)
        gap = mc["y_avg"] - cur_max
        new_height = mc["y_avg"] - cur_min

        if gap <= gap_tol and new_height <= max_band_height:
            cur.append(mc)
        else:
            bands.append([mc])

    out = []
    for band in bands:
        all_rows = []
        for mc in band:
            all_rows.extend(mc["rows"])

        out.append({
            "micro_count": len(band),
            "entity_count": len(all_rows),
            "y_avg": sum(r["y_mid"] for r in all_rows) / len(all_rows),
            "y_min": min(r["y_min"] for r in all_rows),
            "y_max": max(r["y_max"] for r in all_rows),
            "x_min": min(r["x_min"] for r in all_rows),
            "x_max": max(r["x_max"] for r in all_rows),
            "rows": all_rows
        })

    return out

def merge_x_ranges(rows, gap_tol=1800.0):
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

def extract_pile_xs(ents):
    xs = []

    for e in ents:
        layer_u = e["layer"].upper()
        if "PILE" not in layer_u and "CIP" not in layer_u:
            continue

        pts = e["points"]
        if not pts or len(pts) < 2:
            continue

        x0, y0, x1, y1 = bbox(pts)
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        if dx <= 150 and dy >= 1000:
            xs.append((x0 + x1) * 0.5)

    xs = sorted(xs)

    uniq = []
    for x in xs:
        if not uniq or abs(x - uniq[-1]) > 250:
            uniq.append(x)

    return uniq

def nearest_index(xs, x):
    if not xs:
        return None
    best_i = 0
    best_d = abs(xs[0] - x)
    for i, xx in enumerate(xs):
        d = abs(xx - x)
        if d < best_d:
            best_d = d
            best_i = i
    return best_i

def fmt_pile(n):
    if n is None:
        return "P???"
    return "P" + str(n).zfill(3)

def x_to_pile_range(cno, pile_xs, x0, x1):
    nums = PILE_RANGE_NUMS.get(cno)
    if not nums:
        return "P???"

    if len(pile_xs) < 5:
        return "P???"

    i0 = nearest_index(pile_xs, x0)
    i1 = nearest_index(pile_xs, x1)

    if i0 is None or i1 is None:
        return "P???"

    i0 = max(0, min(i0, len(nums) - 1))
    i1 = max(0, min(i1, len(nums) - 1))

    n0 = nums[min(i0, len(nums)-1)]
    n1 = nums[min(i1, len(nums)-1)]

    return fmt_pile(n0) + "~" + fmt_pile(n1)

def nearby_texts(texts, x_min, x_max, y_min, y_max, x_pad=7000, y_pad=5000):
    hits = []
    for t in texts:
        x = t.get("x")
        y = t.get("y")
        if x is None or y is None:
            continue

        if x_min - x_pad <= x <= x_max + x_pad and y_min - y_pad <= y <= y_max + y_pad:
            s = t.get("text", "")
            if any(k in s.upper() for k in ["WALE", "H-300", "2H-300", "ANCHOR", "EL(+", "PILE NO", "CORNER STRUT"]):
                hits.append(s)

    return sorted(set(hits))

def guess_type(rows, near_texts):
    joined = " / ".join(near_texts).upper()
    layers = ",".join(r["layer"] for r in rows).upper()
    count = len(rows)

    if "2H-300" in joined:
        return "2H 더블띠장"
    if "H-300" in joined and "2H-300" not in joined:
        return "H 단띠장 후보"
    if count >= 4:
        return "2H 후보"
    return "H 또는 2H 후보"

def main():
    final = []

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-612~C-619 WALE 실제 BAND 후보 판독표\n")
        f.write("=" * 120 + "\n")
        f.write("HEIGHT GROUP을 실제 띠장 BAND 후보로 다시 묶은 검토용 자료입니다.\n")
        f.write("코드 수정 전 반드시 도면 이미지와 대조하세요.\n\n")

        for path in find_files():
            fname = os.path.basename(path)
            cno = fname.split()[0]
            ents = parse_entities(path)
            pile_xs = extract_pile_xs(ents)

            texts = [
                e for e in ents
                if e["type"] in ["TEXT", "MTEXT"] and e.get("text")
            ]

            wale_rows = []
            for e in ents:
                if "WALE" not in e["layer"].upper():
                    continue

                pts = e["points"]
                if not pts or len(pts) < 2:
                    continue

                l = length(pts)
                if l < 400:
                    continue

                x0, y0, x1, y1 = bbox(pts)

                wale_rows.append({
                    "layer": e["layer"],
                    "x_min": x0,
                    "x_max": x1,
                    "y_min": y0,
                    "y_max": y1,
                    "y_mid": (y0 + y1) * 0.5,
                    "length": l
                })

            micro = cluster_y(wale_rows, tol=180.0)
            bands = collapse_to_bands(micro, gap_tol=1200.0, max_band_height=1800.0)

            item = {
                "file": fname,
                "pile_range": PILE_RANGE_TEXT.get(cno, ""),
                "pile_count_detected": len(pile_xs),
                "bands": []
            }

            f.write("\n" + "=" * 120 + "\n")
            f.write(f"{fname} / {PILE_RANGE_TEXT.get(cno, '')}\n")
            f.write(f"감지 PILE x 개수: {len(pile_xs)}\n")
            f.write("=" * 120 + "\n")

            # 보기 쉽게 위에서 아래 순서
            sorted_bands = sorted(bands, key=lambda b: -b["y_avg"])

            for top_i, b in enumerate(sorted_bands, start=1):
                xranges = merge_x_ranges(b["rows"])
                ntexts = nearby_texts(texts, b["x_min"], b["x_max"], b["y_min"], b["y_max"])
                typ = guess_type(b["rows"], ntexts)

                f.write("\n")
                f.write(f"[BAND {top_i}] y_avg={b['y_avg']:.1f}, y_range={b['y_min']:.1f}~{b['y_max']:.1f}, micro={b['micro_count']}, entity={b['entity_count']}\n")
                f.write(f"형식 후보: {typ}\n")
                f.write(f"전체 x범위: {b['x_min']:.1f} ~ {b['x_max']:.1f}\n")
                f.write("x-range / 추정 PILE 범위:\n")

                band_ranges = []
                for rg in xranges:
                    pr = x_to_pile_range(cno, pile_xs, rg[0], rg[1])
                    band_ranges.append({
                        "x_min": rg[0],
                        "x_max": rg[1],
                        "pile_range_guess": pr,
                        "sum_length": rg[2]
                    })
                    f.write(f"  - x={rg[0]:.1f} ~ {rg[1]:.1f} / {pr} / length_sum={rg[2]:.1f}\n")

                if ntexts:
                    f.write("주변 텍스트:\n")
                    for t in ntexts:
                        f.write(f"  - {t}\n")

                item["bands"].append({
                    "top_index": top_i,
                    "y_avg": b["y_avg"],
                    "y_min": b["y_min"],
                    "y_max": b["y_max"],
                    "micro_count": b["micro_count"],
                    "entity_count": b["entity_count"],
                    "type_guess": typ,
                    "x_ranges": band_ranges,
                    "near_texts": ntexts
                })

            final.append(item)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print("완료")
    print(OUT_TXT)
    print(OUT_JSON)

if __name__ == "__main__":
    main()
