import json
import math
from pathlib import Path
from statistics import mean, median

root = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer")
json_path = root / "Assets" / "StreamingAssets" / "WangsukDXF" / "ParsedUnityJson_C605" / "c605_anchor_l1.json"

if not json_path.exists():
    print("없음:", json_path)
    raise SystemExit()

data = json.loads(json_path.read_text(encoding="utf-8"))

entities = data.get("entities", [])
lengths = []

for e in entities:
    pts = e.get("points", [])
    if not pts or len(pts) < 2:
        continue

    total = 0.0
    for i in range(len(pts) - 1):
        p0 = pts[i]
        p1 = pts[i + 1]

        x0 = float(p0.get("x", 0))
        y0 = float(p0.get("y", 0))
        z0 = float(p0.get("z", 0))

        x1 = float(p1.get("x", 0))
        y1 = float(p1.get("y", 0))
        z1 = float(p1.get("z", 0))

        total += math.sqrt((x1-x0)**2 + (y1-y0)**2 + (z1-z0)**2)

    if total > 0:
        lengths.append(total)

print("파일:", json_path)
print("entity count:", len(entities))
print("length count:", len(lengths))

if not lengths:
    raise SystemExit()

lengths_sorted = sorted(lengths)

print("min :", min(lengths_sorted))
print("max :", max(lengths_sorted))
print("avg :", mean(lengths_sorted))
print("med :", median(lengths_sorted))

print("\n상위 긴 길이 30개:")
for v in sorted(lengths_sorted, reverse=True)[:30]:
    print(round(v, 4))

# 대표 길이 후보: 4m 이상 30m 이하
candidates = [v for v in lengths_sorted if 4.0 <= v <= 30.0]

print("\n4m~30m 후보 count:", len(candidates))
if candidates:
    print("후보 min :", min(candidates))
    print("후보 max :", max(candidates))
    print("후보 avg :", mean(candidates))
    print("후보 med :", median(candidates))

    # 0.5m 단위 빈도
    bins = {}
    for v in candidates:
        key = round(v * 2) / 2
        bins[key] = bins.get(key, 0) + 1

    print("\n길이 빈도 0.5m 단위:")
    for k, c in sorted(bins.items(), key=lambda x: (-x[1], x[0]))[:20]:
        print(f"{k:6.2f} m : {c}")
