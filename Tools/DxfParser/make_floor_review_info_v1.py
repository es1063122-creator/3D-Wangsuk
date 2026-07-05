import os
import re
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

OUT_JSON = os.path.join(OUT_DIR, "floor_review_info_v1.json")
OUT_TXT = os.path.join(OUT_DIR, "floor_review_info_v1.txt")

TARGET_DXF_HINTS = [
    "C-605",
    "굴착계획",
    "평면"
]

KEYWORDS = [
    "601동", "602동", "603동", "604동", "605동", "606동", "607동", "608동", "609동", "610동", "611동", "612동", "613동", "614동",
    "지하주차장",
    "펌프실",
    "전기실",
    "발전기실",
    "전기계",
    "열교환실",
    "PIT",
    "피트",
    "기계실",
    "EL+",
    "EL(+"
]

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

def parse_text_entities(path):
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

    texts = []

    for e in ents:
        if e["type"] not in ["TEXT", "MTEXT"]:
            continue

        layer = ""
        x = None
        y = None
        raw = []

        for c, v in e["pairs"]:
            if c == 8:
                layer = v
            elif c == 10 and x is None:
                try:
                    x = float(v)
                except:
                    pass
            elif c == 20 and y is None:
                try:
                    y = float(v)
                except:
                    pass
            elif c in [1, 3]:
                raw.append(v)

        text = "".join(raw).strip()
        if not text or x is None or y is None:
            continue

        texts.append({
            "text": text,
            "layer": layer,
            "x": x,
            "y": y
        })

    return texts

def find_c605_file():
    candidates = []
    for root, dirs, files in os.walk(DXF_DIR):
        for f in files:
            if not f.lower().endswith(".dxf"):
                continue

            name = f.upper()
            if "C-605" in name:
                candidates.append(os.path.join(root, f))

    if candidates:
        return sorted(candidates)[0]

    # fallback
    for root, dirs, files in os.walk(DXF_DIR):
        for f in files:
            if not f.lower().endswith(".dxf"):
                continue
            if "평면" in f or "굴착계획" in f:
                return os.path.join(root, f)

    return None

def clean_text(s):
    s = s.replace("\\P", " ")
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\\[A-Za-z0-9;,.+-]+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def category_for(text):
    t = text.upper()

    if re.search(r"60[1-9]동|61[0-4]동", text):
        return "building"

    if "주차장" in text:
        return "parking"

    if "펌프" in text:
        return "pump"

    if "전기" in text or "발전" in text:
        return "electric"

    if "열교환" in text:
        return "heat"

    if "PIT" in t or "피트" in text:
        return "pit"

    if "기계" in text:
        return "machine"

    if "EL" in t:
        return "el"

    return "etc"

def color_for(cat):
    colors = {
        "building": "#45F2B5",
        "parking": "#4DC9FF",
        "pump": "#FF9A3D",
        "electric": "#FFD84D",
        "heat": "#B06CFF",
        "pit": "#FF4D8D",
        "machine": "#40E0D0",
        "el": "#FFFFFF",
        "etc": "#CCCCCC",
    }
    return colors.get(cat, "#CCCCCC")

def should_keep(text):
    if any(k in text for k in KEYWORDS):
        return True
    if re.search(r"60[1-9]동|61[0-4]동", text):
        return True
    if re.search(r"EL\s*[\(\+]*\s*\+?\d", text.upper()):
        return True
    return False

def main():
    dxf = find_c605_file()
    if dxf is None:
        raise FileNotFoundError("C-605 DXF를 찾지 못했습니다.")

    texts = parse_text_entities(dxf)

    markers = []

    for t in texts:
        label = clean_text(t["text"])

        if not should_keep(label):
            continue

        cat = category_for(label)

        # EL만 단독으로 너무 많은 경우는 제외하지 않고 남겨둔다.
        marker = {
            "label": label,
            "category": cat,
            "color": color_for(cat),
            "dxf_x": t["x"],
            "dxf_y": t["y"],
            "layer": t["layer"],
            "source": os.path.basename(dxf)
        }

        markers.append(marker)

    # 너무 가까운 중복 텍스트 제거
    unique = []
    seen = set()

    for m in markers:
        key = (m["label"], round(m["dxf_x"] / 1000), round(m["dxf_y"] / 1000))
        if key in seen:
            continue
        seen.add(key)
        unique.append(m)

    result = {
        "name": "Wangsuk A-6BL Floor Review Info v1",
        "status": "검토용. C-605 바닥/동자리 도면 텍스트 기반 자동 추출.",
        "source_dxf": os.path.basename(dxf),
        "rules": {
            "building": "동자리 / 601~614동",
            "parking": "지하주차장",
            "pump": "펌프실",
            "electric": "전기실/발전기실/전기계",
            "heat": "열교환실",
            "pit": "PIT",
            "machine": "기계실",
            "el": "EL 표기"
        },
        "markers": unique
    }

    Path(OUT_JSON).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("바닥검토 정보 추출 결과\n")
        f.write("=" * 100 + "\n")
        f.write(f"source: {os.path.basename(dxf)}\n")
        f.write(f"count: {len(unique)}\n\n")

        for m in unique:
            f.write(f"[{m['category']}] {m['label']} / x={m['dxf_x']:.1f}, y={m['dxf_y']:.1f}, layer={m['layer']}\n")

    print("완료")
    print(OUT_JSON)
    print(OUT_TXT)
    print("marker count:", len(unique))

if __name__ == "__main__":
    main()
