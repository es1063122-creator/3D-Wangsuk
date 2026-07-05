import os
import json
import math

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

SRC_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "ParsedUnityJson_C605"
)

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "ParsedUnityJson_C605_Outer"
)

os.makedirs(OUT_DIR, exist_ok=True)


def point_xy(p):
    return float(p["x"]), float(p["y"])


def polygon_area(points):
    if len(points) < 3:
        return 0.0

    area = 0.0
    n = len(points)

    for i in range(n):
        x1, y1 = point_xy(points[i])
        x2, y2 = point_xy(points[(i + 1) % n])
        area += x1 * y2 - x2 * y1

    return abs(area) * 0.5


def dist_point_to_segment(px, py, ax, ay, bx, by):
    vx = bx - ax
    vy = by - ay
    wx = px - ax
    wy = py - ay

    c1 = vx * wx + vy * wy
    if c1 <= 0:
        return math.hypot(px - ax, py - ay)

    c2 = vx * vx + vy * vy
    if c2 <= c1:
        return math.hypot(px - bx, py - by)

    t = c1 / c2
    proj_x = ax + t * vx
    proj_y = ay + t * vy

    return math.hypot(px - proj_x, py - proj_y)


def dist_point_to_polyline(px, py, points, closed=True):
    if len(points) < 2:
        return 999999999999.0

    min_d = 999999999999.0
    n = len(points)

    last = n if closed else n - 1

    for i in range(last):
        a = points[i]
        b = points[(i + 1) % n]

        ax, ay = point_xy(a)
        bx, by = point_xy(b)

        d = dist_point_to_segment(px, py, ax, ay, bx, by)
        if d < min_d:
            min_d = d

    return min_d


def bounds_of_points(points):
    xs = [float(p["x"]) for p in points]
    ys = [float(p["y"]) for p in points]

    return {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys),
        "diag": math.hypot(max(xs) - min(xs), max(ys) - min(ys)),
    }


def load_json(name):
    path = os.path.join(SRC_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name, data):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("C-605 외곽 PF/CIP 필터 시작")
    print("SRC:", SRC_DIR)
    print("OUT:", OUT_DIR)
    print("")

    pf_data = load_json("c605_pf_hpile.json")
    cip_data = load_json("c605_cip.json")

    pf_entities = pf_data.get("entities", [])
    cip_entities = cip_data.get("entities", [])

    # 1) PF 후보 중 면적이 큰 닫힌 폴리라인을 외곽 후보로 판단
    pf_candidates = []

    for e in pf_entities:
        pts = e.get("points", [])
        if len(pts) < 3:
            continue

        area = polygon_area(pts)
        if area <= 0:
            continue

        b = bounds_of_points(pts)

        pf_candidates.append({
            "entity": e,
            "area": area,
            "bounds": b,
        })

    pf_candidates.sort(key=lambda x: x["area"], reverse=True)

    if not pf_candidates:
        print("PF 외곽 후보 없음")
        return

    max_area = pf_candidates[0]["area"]

    # 너무 작은 H파일 개별 사각형은 제외하고, 큰 외곽 폴리라인만 남김
    # 1차 기준: 최대 면적의 5% 이상
    outer_pf_candidates = [
        c for c in pf_candidates
        if c["area"] >= max_area * 0.05
    ]

    # 너무 많이 남으면 상위 5개까지만
    outer_pf_candidates = outer_pf_candidates[:5]

    outer_pf_entities = [c["entity"] for c in outer_pf_candidates]

    print("PF 전체:", len(pf_entities))
    print("PF 면적 후보:", len(pf_candidates))
    print("PF 외곽 선택:", len(outer_pf_entities))
    print("PF 최대 면적:", max_area)

    # 대표 외곽 폴리라인은 제일 큰 것
    main_pf = outer_pf_candidates[0]["entity"]
    main_points = main_pf.get("points", [])
    main_bounds = bounds_of_points(main_points)

    # 2) CIP는 외곽 PF 라인 근처에 있는 원형 파일만 남김
    # 도면 단위 기준 자동 거리: 외곽 대각선의 1.5%
    # 너무 좁거나 넓으면 나중에 조정 가능
    distance_threshold = main_bounds["diag"] * 0.015

    outer_cip_entities = []

    for e in cip_entities:
        if not e.get("has_center"):
            continue

        c = e.get("center", {})
        px = float(c.get("x", 0.0))
        py = float(c.get("y", 0.0))

        d = dist_point_to_polyline(px, py, main_points, closed=True)

        if d <= distance_threshold:
            outer_cip_entities.append(e)

    print("CIP 전체:", len(cip_entities))
    print("CIP 외곽 선택:", len(outer_cip_entities))
    print("CIP 거리 기준:", distance_threshold)

    pf_out = {
        "group": "C605_OUTER_PF_HPILE",
        "entity_count": len(outer_pf_entities),
        "entities": outer_pf_entities,
    }

    cip_out = {
        "group": "C605_OUTER_CIP",
        "entity_count": len(outer_cip_entities),
        "entities": outer_cip_entities,
    }

    summary = {
        "pf_total": len(pf_entities),
        "pf_candidates": len(pf_candidates),
        "pf_outer": len(outer_pf_entities),
        "cip_total": len(cip_entities),
        "cip_outer": len(outer_cip_entities),
        "pf_max_area": max_area,
        "main_bounds": main_bounds,
        "cip_distance_threshold": distance_threshold,
    }

    save_json("c605_outer_pf_hpile.json", pf_out)
    save_json("c605_outer_cip.json", cip_out)
    save_json("c605_outer_summary.json", summary)

    print("")
    print("완료")
    print(os.path.join(OUT_DIR, "c605_outer_summary.json"))


if __name__ == "__main__":
    main()
