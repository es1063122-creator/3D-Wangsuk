import json
import re
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer")

SRC = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review" / "soil_section_text_precise.json"
OUT_JSON = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review" / "soil_layer_levels_from_section_v1.json"
OUT_TXT = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review" / "soil_layer_levels_from_section_v1.txt"

ORDER = ["매립층", "퇴적층", "풍화토", "풍화암", "보통암"]

COLORS = {
    "매립층": [0.62, 0.36, 0.14, 0.20],
    "퇴적층": [0.86, 0.55, 0.18, 0.18],
    "풍화토": [0.95, 0.76, 0.18, 0.16],
    "풍화암": [0.46, 0.46, 0.46, 0.20],
    "보통암": [0.28, 0.28, 0.28, 0.22],
}

def parse_el(text):
    m = re.search(r"EL\.?\s*\(?\+?\)?\s*([0-9]+\.[0-9]+)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"EL\s*[\+\-]?\s*([0-9]+\.[0-9]+)", text, re.IGNORECASE)
    if not m:
        return None
    return float(m.group(1))

def has_layer(text):
    for layer in ORDER:
        if layer in text:
            return layer
    return None

data = json.loads(SRC.read_text(encoding="utf-8"))
rows = data.get("kept", [])

el_rows = []
layer_rows = []

for r in rows:
    text = r.get("text", "")
    x = float(r.get("x", 0))
    y = float(r.get("y", 0))

    el = parse_el(text)
    if el is not None:
        el_rows.append({
            "text": text,
            "el": el,
            "x": x,
            "y": y,
            "file": r.get("file", "")
        })

    layer = has_layer(text)
    if layer:
        layer_rows.append({
            "layer": layer,
            "text": text,
            "x": x,
            "y": y,
            "file": r.get("file", "")
        })

samples = []

# 각 지층명 텍스트를 가장 가까운 EL 텍스트와 연결
for lr in layer_rows:
    candidates = []
    for er in el_rows:
        if er["file"] != lr["file"]:
            continue

        dx = abs(er["x"] - lr["x"])
        dy = er["y"] - lr["y"]

        # 같은 주상도 블록: x가 가깝고, 지층명이 EL 아래에 있어야 함
        if dx <= 3.0 and 0 <= dy <= 16.0:
            candidates.append((dx + dy * 0.15, er, dy))

    if not candidates:
        continue

    candidates.sort(key=lambda v: v[0])
    _, er, dy = candidates[0]

    # 단면도 주상도는 도면 y 차이가 EL 차이에 거의 대응하는 형태로 보임.
    # 따라서 EL = 상단EL - y차 로 1차 추정.
    estimated_el = er["el"] - dy

    samples.append({
        "layer": lr["layer"],
        "estimated_el": estimated_el,
        "source_el": er["el"],
        "source_el_text": er["text"],
        "layer_text": lr["text"],
        "x": lr["x"],
        "y": lr["y"],
        "dy": dy,
        "file": lr["file"]
    })

by_layer = {k: [] for k in ORDER}
for s in samples:
    by_layer[s["layer"]].append(s["estimated_el"])

centers = {}
for layer in ORDER:
    vals = by_layer[layer]
    if vals:
        centers[layer] = mean(vals)

# 누락 방어
# 보통암이 없거나 일부 층이 약하면 주변값으로 보정
if "매립층" not in centers:
    centers["매립층"] = 38.5
if "퇴적층" not in centers:
    centers["퇴적층"] = centers["매립층"] - 2.5
if "풍화토" not in centers:
    centers["풍화토"] = centers["퇴적층"] - 3.0
if "풍화암" not in centers:
    centers["풍화암"] = centers["풍화토"] - 2.0
if "보통암" not in centers:
    centers["보통암"] = centers["풍화암"] - 2.5

# 위에서 아래 순서가 흐트러질 경우 강제 정렬용 평균값 보정
# 중심 EL이 높은 순서대로 있어야 함
center_list = []
prev = None
for layer in ORDER:
    c = centers[layer]
    if prev is not None and c >= prev:
        c = prev - 1.0
    centers[layer] = c
    prev = c
    center_list.append((layer, c))

# 경계는 인접 층 중심의 중간값으로 추정
levels = []

top_el = centers["매립층"] + 1.2

for i, layer in enumerate(ORDER):
    center_el = centers[layer]

    if i == 0:
        layer_top = top_el
    else:
        prev_layer = ORDER[i - 1]
        layer_top = (centers[prev_layer] + center_el) * 0.5

    if i == len(ORDER) - 1:
        layer_bottom = center_el - 2.5
    else:
        next_layer = ORDER[i + 1]
        layer_bottom = (center_el + centers[next_layer]) * 0.5

    levels.append({
        "name": layer,
        "topEL": round(layer_top, 3),
        "bottomEL": round(layer_bottom, 3),
        "centerEL": round(center_el, 3),
        "sampleCount": len(by_layer[layer]),
        "color": COLORS[layer]
    })

result = {
    "name": "Soil Layer Levels From Section v1",
    "source": str(SRC),
    "status": "C-106~110 단지횡단면도 주상도 텍스트 위치 기반 1차 추정. 최종 검토 필요.",
    "method": "EL 텍스트와 같은 x좌표 인근 지층명 텍스트를 연결하고, 도면 y차를 EL차로 환산하여 지층 중심 EL을 추정한 뒤 인접 중심의 중간값을 경계로 사용",
    "levels": levels,
    "samples": samples[:300]
}

OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

with OUT_TXT.open("w", encoding="utf-8") as f:
    f.write("도면 기반 지층 레벨 1차 추정 결과\n")
    f.write("=" * 100 + "\n")
    f.write(result["status"] + "\n\n")

    f.write("[추정 레벨]\n")
    for lv in levels:
        f.write(f"{lv['name']}: EL {lv['topEL']} ~ EL {lv['bottomEL']} / center={lv['centerEL']} / samples={lv['sampleCount']}\n")

    f.write("\n[층별 중심 EL 샘플]\n")
    for layer in ORDER:
        vals = by_layer[layer]
        if vals:
            f.write(f"{layer}: count={len(vals)}, avg={mean(vals):.3f}, min={min(vals):.3f}, max={max(vals):.3f}\n")
        else:
            f.write(f"{layer}: count=0\n")

    f.write("\n[샘플 일부]\n")
    for s in samples[:80]:
        f.write(f"{s['layer']} / estimatedEL={s['estimated_el']:.3f} / sourceEL={s['source_el']} / dy={s['dy']:.3f} / x={s['x']:.1f}, y={s['y']:.1f}\n")

print("완료")
print(OUT_JSON)
print(OUT_TXT)
print("levels:")
for lv in levels:
    print(lv)
