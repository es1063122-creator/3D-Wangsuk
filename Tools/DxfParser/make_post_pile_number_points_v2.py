import json
from pathlib import Path

PROJECT_ROOT = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer")

SRC = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "ParsedUnityJson_C605" / "c605_pf_hpile.json"

OUT_JSON = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review" / "post_pile_number_points_v1.json"
OUT_TXT = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review" / "post_pile_number_points_v1.txt"

data = json.loads(SRC.read_text(encoding="utf-8"))
entities = data.get("entities", [])

points = []

for idx, e in enumerate(entities):
    pts = e.get("points", [])
    if not pts:
        continue

    xs = [float(p["x"]) for p in pts if "x" in p]
    ys = [float(p["y"]) for p in pts if "y" in p]

    if not xs or not ys:
        continue

    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)

    no = idx + 1

    if no < 1 or no > 492:
        continue

    points.append({
        "no": no,
        "x": cx,
        "y": cy,
        "source": "points_average",
        "layer": e.get("layer", ""),
        "point_count": len(pts)
    })

result = {
    "name": "Post Pile Number Points v2",
    "source": str(SRC),
    "status": "PF LWPOLYLINE points[] 평균좌표 기준",
    "count": len(points),
    "points": points
}

OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

with OUT_TXT.open("w", encoding="utf-8") as f:
    f.write("포스트파일 번호 좌표 추출 결과 - points[] 평균좌표 기준\n")
    f.write("=" * 100 + "\n")
    f.write(f"source: {SRC}\n")
    f.write(f"count: {len(points)}\n\n")

    for p in points[:40]:
        f.write(f"P{p['no']:03d} x={p['x']:.3f}, y={p['y']:.3f}, source={p['source']}, point_count={p['point_count']}\n")

    f.write("\n...\n")

    for p in points[-20:]:
        f.write(f"P{p['no']:03d} x={p['x']:.3f}, y={p['y']:.3f}, source={p['source']}, point_count={p['point_count']}\n")

print("완료")
print(OUT_JSON)
print(OUT_TXT)
print("count:", len(points))
