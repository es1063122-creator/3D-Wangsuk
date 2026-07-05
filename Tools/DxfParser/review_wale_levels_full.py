import os
import re
import math
from pathlib import Path
from collections import Counter, defaultdict

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

OUT_TXT = os.path.join(OUT_DIR, "wale_level_full_review.txt")

TARGETS = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

def read_pairs(path):
    # DXF codepage가 ANSI_949인 경우가 많아서 cp949 우선 사용
    lines = Path(path).read_text(encoding="cp949", errors="ignore").splitlines()
    pairs = []

    i = 0
    while i < len(lines) - 1:
        try:
            code = int(lines[i].strip())
            val = lines[i + 1].strip()
            pairs.append((code, val))
        except Exception:
            pass
        i += 2

    return pairs

def parse_entities(path):
    pairs = read_pairs(path)

    ents = []
    in_entities = False
    section = None
    cur = None

    for code, val in pairs:
        if code == 0 and val == "SECTION":
            section = None
            continue

        if code == 2:
            section = val
            if val == "ENTITIES":
                in_entities = True
            continue

        if code == 0 and val == "ENDSEC":
            if in_entities:
                in_entities = False
            continue

        if not in_entities:
            continue

        if code == 0:
            if cur is not None:
                ents.append(cur)
            cur = {
                "type": val,
                "pairs": []
            }
        else:
            if cur is not None:
                cur["pairs"].append((code, val))

    if cur is not None:
        ents.append(cur)

    result = []

    for e in ents:
        ps = e["pairs"]
        typ = e["type"]

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

        elif typ == "CIRCLE":
            vals = {}
            for c, v in ps:
                if c in [10, 20, 40]:
                    try:
                        vals[c] = float(v)
                    except:
                        pass

            if all(k in vals for k in [10, 20, 40]):
                cx = vals[10]
                cy = vals[20]
                r = vals[40]
                pts = []
                for i in range(32):
                    a = math.pi * 2 * i / 32
                    pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
                obj["points"] = pts

        elif typ == "ARC":
            vals = {}
            for c, v in ps:
                if c in [10, 20, 40, 50, 51]:
                    try:
                        vals[c] = float(v)
                    except:
                        pass

            if all(k in vals for k in [10, 20, 40, 50, 51]):
                cx = vals[10]
                cy = vals[20]
                r = vals[40]
                a0 = math.radians(vals[50])
                a1 = math.radians(vals[51])
                if a1 < a0:
                    a1 += math.pi * 2

                pts = []
                for i in range(24):
                    a = a0 + (a1 - a0) * i / 23
                    pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
                obj["points"] = pts

        result.append(obj)

    return result

def length_of_points(pts):
    if not pts or len(pts) < 2:
        return 0.0

    total = 0.0
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        total += math.hypot(x2 - x1, y2 - y1)

    return total

def mid_y(pts):
    if not pts:
        return None
    return sum(p[1] for p in pts) / len(pts)

def mid_x(pts):
    if not pts:
        return None
    return sum(p[0] for p in pts) / len(pts)

def cluster_values(values, tol):
    values = sorted(values)
    clusters = []

    for v in values:
        if not clusters:
            clusters.append([v])
            continue

        if abs(v - clusters[-1][-1]) <= tol:
            clusters[-1].append(v)
        else:
            clusters.append([v])

    result = []
    for c in clusters:
        result.append({
            "count": len(c),
            "avg": sum(c) / len(c),
            "min": min(c),
            "max": max(c)
        })

    return result

def find_files():
    files = []
    for fname in os.listdir(DXF_DIR):
        if not fname.lower().endswith(".dxf"):
            continue

        if any(fname.startswith(t) for t in TARGETS):
            files.append(os.path.join(DXF_DIR, fname))

    return sorted(files)

def text_hit(txt):
    u = txt.upper()
    keys = [
        "PILE NO",
        "WALE",
        "E/ANCHOR",
        "ANCHOR",
        "H-300",
        "2H-300",
        "EL(+",
        "CORNER STRUT"
    ]

    return any(k in u for k in keys)

def main():
    files = find_files()

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("C-612~C-619 WALE 높이/단수 전체 재검토\n")
        f.write("=" * 120 + "\n\n")
        f.write("주의: 이 리포트는 CAD 전개도에서 WALE/C-WALE 레이어와 관련 문자 위치를 추출한 검토 자료입니다.\n")
        f.write("최종 Unity 반영 전, 각 전개도 그림과 대조해서 단수 구간을 확정해야 합니다.\n\n")

        for path in files:
            fname = os.path.basename(path)
            ents = parse_entities(path)

            f.write("\n" + "=" * 120 + "\n")
            f.write(f"FILE: {fname}\n")
            f.write("=" * 120 + "\n\n")

            layer_counts = Counter(e["layer"] for e in ents)
            f.write("[주요 레이어 카운트]\n")
            for layer, count in layer_counts.most_common(25):
                if any(k.upper() in layer.upper() for k in ["WALE", "ANCHOR", "STRUT", "PILE", "CIP", "GRID", "TEXT", "DIM"]):
                    f.write(f"{count:6d} | {layer}\n")

            f.write("\n[PILE / WALE / ANCHOR / EL 문자]\n")
            texts = []
            for e in ents:
                if e["type"] not in ["TEXT", "MTEXT"]:
                    continue

                txt = e.get("text", "")
                if not txt:
                    continue

                if text_hit(txt):
                    texts.append(e)

            texts.sort(key=lambda e: (-(e["y"] or 0), e["x"] or 0))

            for e in texts:
                f.write(
                    f"x={e['x'] if e['x'] is not None else 0:.1f}, "
                    f"y={e['y'] if e['y'] is not None else 0:.1f} | "
                    f"{e['layer']} | {e['text']}\n"
                )

            f.write("\n[WALE / C-WALE geometry y micro-cluster]\n")
            wale_ys = []
            wale_rows = []

            for e in ents:
                layer_u = e["layer"].upper()

                if "WALE" not in layer_u:
                    continue

                pts = e["points"]
                if not pts or len(pts) < 2:
                    continue

                l = length_of_points(pts)
                y = mid_y(pts)
                x = mid_x(pts)

                # 너무 작은 조각도 일단 보고서에 포함
                if y is not None:
                    wale_ys.append(y)
                    wale_rows.append((x, y, l, e["layer"], e["type"]))

            clusters = cluster_values(wale_ys, 80.0)

            for i, c in enumerate(clusters, start=1):
                f.write(
                    f"cluster {i:02d}: count={c['count']:3d}, "
                    f"avg_y={c['avg']:.1f}, min={c['min']:.1f}, max={c['max']:.1f}\n"
                )

            f.write("\n[WALE long member candidates: length >= 500]\n")
            long_rows = [r for r in wale_rows if r[2] >= 500]
            long_rows.sort(key=lambda r: (-r[1], r[0] or 0))

            for x, y, l, layer, typ in long_rows[:120]:
                f.write(f"x={x:.1f}, y={y:.1f}, len={l:.1f} | {layer} | {typ}\n")

            f.write("\n[ANCHOR geometry y cluster]\n")
            anchor_ys = []

            for e in ents:
                layer_u = e["layer"].upper()

                if "ANCH" not in layer_u:
                    continue

                pts = e["points"]
                if not pts or len(pts) < 2:
                    continue

                y = mid_y(pts)
                if y is not None:
                    anchor_ys.append(y)

            anchor_clusters = cluster_values(anchor_ys, 120.0)

            for i, c in enumerate(anchor_clusters, start=1):
                f.write(
                    f"anchor cluster {i:02d}: count={c['count']:3d}, "
                    f"avg_y={c['avg']:.1f}, min={c['min']:.1f}, max={c['max']:.1f}\n"
                )

            f.write("\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
