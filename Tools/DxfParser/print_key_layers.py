import json
import re

path = r"C:\UnityProjects\SafeAR_Wangsuk_CAD_3D\Assets\StreamingAssets\WangsukDXF\ParsedJson\wangsuk_dxf_analysis_summary.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

pattern = re.compile(r"PILE|H-PILE|CIP|WALE|ANCH|STRUT|굴착|GL|TEXT|GRID|그리드|SECTION|단면", re.I)

items = []
for name, value in data["global_layer_counts"].items():
    if pattern.search(name):
        items.append((name, value))

items.sort(key=lambda x: x[1], reverse=True)

print("")
print("===== 왕숙 A-6BL 주요 DXF 레이어 =====")
print("")

for name, value in items[:150]:
    print(f"{name:45s} {value}")

print("")
print("완료")
