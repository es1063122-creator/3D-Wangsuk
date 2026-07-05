import json
import math
from pathlib import Path

PROJECT_ROOT = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer")
REVIEW_DIR = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review"

SRC = REVIEW_DIR / "floor_review_candidates_v2.json"
OUT_JSON = REVIEW_DIR / "floor_review_info_matched_v2.json"
OUT_TXT = REVIEW_DIR / "floor_review_info_matched_v2.txt"

data = json.loads(SRC.read_text(encoding="utf-8"))
markers = data.get("markers", [])

FACILITY_CATS = {
    "building",
    "parking",
    "pump",
    "electric",
    "heat",
    "pit",
    "machine",
}

facilities = [m for m in markers if m.get("category") in FACILITY_CATS]
els = [m for m in markers if m.get("category") == "el" and "EL" in m.get("label", "").upper()]

def dist(a, b):
    return math.hypot(a["dxf_x"] - b["dxf_x"], a["dxf_y"] - b["dxf_y"])

def find_nearest_el(f):
    if not els:
        return None, None

    best = None
    best_d = 10**18

    for e in els:
        d = dist(f, e)
        if d < best_d:
            best = e
            best_d = d

    return best, best_d

def style_for(cat):
    # 검은 배경 + 파란 도면선 위에서 잘 보이는 색상
    styles = {
        "building": {
            "fill": "#45F2B5",
            "outline": "#00A676",
            "labelBg": "#123D32",
            "label": "동자리"
        },
        "parking": {
            "fill": "#4DC9FF",
            "outline": "#0077B6",
            "labelBg": "#10394D",
            "label": "주차장"
        },
        "pump": {
            "fill": "#FF9A3D",
            "outline": "#D45A00",
            "labelBg": "#4A260B",
            "label": "펌프실"
        },
        "electric": {
            "fill": "#FFD84D",
            "outline": "#B88600",
            "labelBg": "#4A3D05",
            "label": "전기실"
        },
        "heat": {
            "fill": "#B06CFF",
            "outline": "#6B22B8",
            "labelBg": "#30164D",
            "label": "열교환실"
        },
        "pit": {
            "fill": "#FF4D8D",
            "outline": "#B00045",
            "labelBg": "#4D1028",
            "label": "PIT"
        },
        "machine": {
            "fill": "#40E0D0",
            "outline": "#008B83",
            "labelBg": "#0E403D",
            "label": "기계실"
        },
    }
    return styles.get(cat, {
        "fill": "#FFFFFF",
        "outline": "#CCCCCC",
        "labelBg": "#222222",
        "label": "기타"
    })

matched = []

for f in facilities:
    nearest, d = find_nearest_el(f)
    st = style_for(f["category"])

    # 시설명과 EL이 가까운 경우만 자동 연결.
    # C-605 도면 좌표 기준 10000 정도면 같은 라벨 박스 근처.
    el_label = ""
    el_distance = None

    if nearest is not None and d <= 12000:
        el_label = nearest["label"]
        el_distance = d

    display = f["label"]
    if el_label:
        display = f"{f['label']}\n{el_label}"

    matched.append({
        "label": f["label"],
        "display_label": display,
        "category": f["category"],
        "category_name": st["label"],
        "el": el_label,
        "el_distance": el_distance,
        "dxf_x": f["dxf_x"],
        "dxf_y": f["dxf_y"],
        "fill_color": st["fill"],
        "outline_color": st["outline"],
        "label_bg_color": st["labelBg"],
        "source_layer": f.get("layer", ""),
        "source_entity_type": f.get("entity_type", "")
    })

# 보기 좋게 y 내림차순, x 오름차순
matched.sort(key=lambda m: (-m["dxf_y"], m["dxf_x"]))

result = {
    "name": "Wangsuk A-6BL Floor Review Matched Info v2",
    "status": "C-605 텍스트 좌표 기반 시설명 + 근접 EL 자동 매칭",
    "source": "floor_review_candidates_v2.json",
    "display_mode": {
        "floor_review_group": "FLOOR_REVIEW_INFO",
        "background": "black",
        "base_drawing_lines": "blue/cyan",
        "facility_style": "semi-transparent colored plate + label box",
        "label_text": "white, EL included"
    },
    "items": matched
}

OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

with OUT_TXT.open("w", encoding="utf-8") as f:
    f.write("바닥검토 시설명 + EL 자동 매칭 결과\n")
    f.write("=" * 100 + "\n")
    f.write(f"facility count: {len(facilities)}\n")
    f.write(f"EL count: {len(els)}\n")
    f.write(f"matched count: {len(matched)}\n\n")

    for m in matched:
        f.write(f"[{m['category_name']}] {m['label']}")
        if m["el"]:
            f.write(f" / {m['el']} / distance={m['el_distance']:.1f}")
        else:
            f.write(" / EL 매칭 없음")
        f.write(f" / x={m['dxf_x']:.1f}, y={m['dxf_y']:.1f}\n")

print("완료")
print(OUT_JSON)
print(OUT_TXT)
print("matched count:", len(matched))
