import json
import os
from pathlib import Path

PROJECT_ROOT = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer")

SEARCH_DIRS = [
    PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "ParsedUnityJson_C605",
    PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review",
]

OUT = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review" / "post_pile_number_points_v1.json"
TXT = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review" / "post_pile_number_points_v1.txt"

def find_pf_json():
    for d in SEARCH_DIRS:
        if not d.exists():
            continue
        for p in d.rglob("*pf*hpile*.json"):
            return p
        for p in d.rglob("*pile*.json"):
            if "c605" in p.name.lower() or "pf" in p.name.lower():
                return p
    return None

def flatten_numbers(obj, prefix=""):
    vals = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            nk = f"{prefix}.{k}" if prefix else k
            vals.update(flatten_numbers(v, nk))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            nk = f"{prefix}[{i}]"
            vals.update(flatten_numbers(v, nk))
    else:
        if isinstance(obj, (int, float)):
            vals[prefix] = float(obj)
    return vals

def get_items(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ["items", "piles", "points", "data", "entities", "pf", "hpiles", "markers"]:
            if key in data and isinstance(data[key], list):
                return data[key]

        # dict 안에 list 중 가장 긴 것 사용
        lists = []
        for k, v in data.items():
            if isinstance(v, list):
                lists.append((k, v))
        if lists:
            lists.sort(key=lambda x: len(x[1]), reverse=True)
            return lists[0][1]

    return []

def pick_no(item, idx):
    if isinstance(item, dict):
        for k in ["no", "No", "number", "pileNo", "pfNo", "pile_no", "id", "index"]:
            if k in item:
                try:
                    n = int(float(item[k]))
                    if 1 <= n <= 999:
                        return n
                except:
                    pass
    return idx + 1

def pick_xy(item):
    nums = flatten_numbers(item)

    # 우선순위 키 조합
    key_candidates = [
        ("x", "z"),
        ("x", "y"),
        ("center.x", "center.z"),
        ("center.x", "center.y"),
        ("position.x", "position.z"),
        ("position.x", "position.y"),
        ("unityX", "unityZ"),
        ("unity_x", "unity_z"),
        ("dxf_x", "dxf_y"),
        ("cx", "cy"),
    ]

    lower_map = {k.lower(): (k, v) for k, v in nums.items()}

    for kx, ky in key_candidates:
        if kx.lower() in lower_map and ky.lower() in lower_map:
            return lower_map[kx.lower()][1], lower_map[ky.lower()][1], lower_map[kx.lower()][0], lower_map[ky.lower()][0]

    # 숫자 필드 중 x/y/z 이름이 들어간 것 찾기
    xs = [(k, v) for k, v in nums.items() if k.lower().endswith("x") or ".x" in k.lower() or "_x" in k.lower()]
    ys = [(k, v) for k, v in nums.items() if k.lower().endswith("y") or ".y" in k.lower() or "_y" in k.lower()]
    zs = [(k, v) for k, v in nums.items() if k.lower().endswith("z") or ".z" in k.lower() or "_z" in k.lower()]

    if xs and zs:
        return xs[0][1], zs[0][1], xs[0][0], zs[0][0]
    if xs and ys:
        return xs[0][1], ys[0][1], xs[0][0], ys[0][0]

    return None, None, "", ""

def main():
    src = find_pf_json()
    if src is None:
        raise FileNotFoundError("c605_pf_hpile.json 또는 PF pile json을 찾지 못했습니다.")

    data = json.loads(src.read_text(encoding="utf-8"))
    items = get_items(data)

    points = []

    for idx, item in enumerate(items):
        x, y, kx, ky = pick_xy(item)
        if x is None or y is None:
            continue

        no = pick_no(item, idx)

        if no < 1 or no > 492:
            continue

        points.append({
            "no": no,
            "x": float(x),
            "y": float(y),
            "key_x": kx,
            "key_y": ky
        })

    # 번호 중복 제거
    dedup = {}
    for p in points:
        dedup[p["no"]] = p

    points = [dedup[k] for k in sorted(dedup.keys())]

    result = {
        "name": "Post Pile Number Points v1",
        "source": str(src),
        "status": "PF 원본 JSON에서 번호마커용 좌표 추출",
        "count": len(points),
        "points": points
    }

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    with TXT.open("w", encoding="utf-8") as f:
        f.write("포스트파일 번호 좌표 추출 결과\n")
        f.write("=" * 100 + "\n")
        f.write(f"source: {src}\n")
        f.write(f"count: {len(points)}\n\n")
        for p in points[:30]:
            f.write(f"P{p['no']:03d} x={p['x']:.3f}, y={p['y']:.3f}, keys=({p['key_x']}, {p['key_y']})\n")
        f.write("\n...\n")
        for p in points[-20:]:
            f.write(f"P{p['no']:03d} x={p['x']:.3f}, y={p['y']:.3f}, keys=({p['key_x']}, {p['key_y']})\n")

    print("완료")
    print(OUT)
    print(TXT)
    print("count:", len(points))

if __name__ == "__main__":
    main()
