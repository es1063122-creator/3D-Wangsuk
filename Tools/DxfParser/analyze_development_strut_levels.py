import os
import json
from collections import defaultdict

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

IN_JSON = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "development_strut_entities.json"
)

OUT_TXT = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "development_strut_level_clusters.txt"
)

def get_mid_y(entity):
    pts = entity.get("points", [])
    if len(pts) < 2:
        return None

    ys = [float(p["y"]) for p in pts]
    return sum(ys) / len(ys)

def get_mid_x(entity):
    pts = entity.get("points", [])
    if len(pts) < 2:
        return None

    xs = [float(p["x"]) for p in pts]
    return sum(xs) / len(xs)

def get_length(entity):
    pts = entity.get("points", [])
    if len(pts) < 2:
        return 0.0

    # 첫점-끝점 기준 길이
    a = pts[0]
    b = pts[-1]
    dx = float(b["x"]) - float(a["x"])
    dy = float(b["y"]) - float(a["y"])
    return (dx * dx + dy * dy) ** 0.5

def cluster_values(values, tolerance):
    values = sorted(values)
    clusters = []

    for v in values:
        if not clusters:
            clusters.append([v])
            continue

        current = clusters[-1]
        avg = sum(current) / len(current)

        if abs(v - avg) <= tolerance:
            current.append(v)
        else:
            clusters.append([v])

    return clusters

def main():
    if not os.path.exists(IN_JSON):
        print("입력 JSON 없음:", IN_JSON)
        return

    data = json.load(open(IN_JSON, "r", encoding="utf-8"))
    entities = data.get("entities", [])

    by_file = defaultdict(list)

    for e in entities:
        file = e.get("file", "")
        mid_y = get_mid_y(e)
        mid_x = get_mid_x(e)
        length = get_length(e)

        if mid_y is None:
            continue

        by_file[file].append({
            "mid_y": mid_y,
            "mid_x": mid_x,
            "length": length,
            "layer": e.get("layer", ""),
            "type": e.get("type", ""),
        })

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("굴착계획 전개도 STRUT 높이군 분석\n")
        f.write("=" * 120 + "\n\n")
        f.write("주의: Y좌표 군집은 전개도 도형 기준입니다. 실제 EL/심도는 다음 단계에서 텍스트와 대조해야 합니다.\n\n")

        for file in sorted(by_file.keys()):
            rows = by_file[file]

            if not rows:
                continue

            ys = [r["mid_y"] for r in rows]

            # DXF 전개도 좌표 단위가 크므로 우선 5,000 단위로 군집
            clusters = cluster_values(ys, tolerance=5000.0)

            # 위쪽/아래쪽 순서 확인을 위해 Y 큰 값부터 정렬
            cluster_infos = []
            for c in clusters:
                avg_y = sum(c) / len(c)
                count = len(c)

                # 해당 군집에 속한 도형 길이 평균
                members = []
                for r in rows:
                    if abs(r["mid_y"] - avg_y) <= 5000.0:
                        members.append(r)

                avg_len = sum([m["length"] for m in members]) / max(len(members), 1)
                min_x = min([m["mid_x"] for m in members]) if members else 0
                max_x = max([m["mid_x"] for m in members]) if members else 0

                cluster_infos.append({
                    "avg_y": avg_y,
                    "count": count,
                    "avg_len": avg_len,
                    "min_x": min_x,
                    "max_x": max_x,
                })

            cluster_infos.sort(key=lambda x: x["avg_y"], reverse=True)

            f.write("=" * 120 + "\n")
            f.write(f"FILE: {file}\n")
            f.write(f"STRUT entity count: {len(rows)}\n")
            f.write(f"Y cluster count: {len(cluster_infos)}\n\n")

            for idx, info in enumerate(cluster_infos, start=1):
                f.write(
                    f"  후보 {idx}단 | "
                    f"avg_y={info['avg_y']:.3f} | "
                    f"count={info['count']} | "
                    f"avg_len={info['avg_len']:.1f} | "
                    f"x_range={info['min_x']:.1f} ~ {info['max_x']:.1f}\n"
                )

            f.write("\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
