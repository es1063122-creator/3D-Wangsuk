import os
import json

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

SRC_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "ParsedUnityJson"
)

DST_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "ParsedUnityJson_MainPlan"
)

os.makedirs(DST_DIR, exist_ok=True)

# 1차 정리 모델에 사용할 핵심 도면만 지정
MAIN_FILES = [
    r"dxf\가시설합본.dxf",
    r"dxf\0.공통\BASE.dxf",
    r"dxf\0.공통\AG-109 단지배치도.dxf",
]

TARGET_FILES = [
    "wangsuk_pf_hpile.json",
    "wangsuk_cip.json",
    "wangsuk_wale.json",
    "wangsuk_anchor.json",
    "wangsuk_corner_strut.json",
    "wangsuk_excavation.json",
    "wangsuk_ground_gl.json",
    "wangsuk_grid.json",
    "wangsuk_building_parking.json",
]

def norm_path(p):
    return str(p).replace("/", "\\").lower()

def is_main_file(source_file):
    s = norm_path(source_file)
    for mf in MAIN_FILES:
        if s == norm_path(mf):
            return True
    return False

def main():
    print("메인 평면용 JSON 필터링 시작")
    print("SRC:", SRC_DIR)
    print("DST:", DST_DIR)
    print("")

    summary = []

    for file_name in TARGET_FILES:
        src = os.path.join(SRC_DIR, file_name)
        dst = os.path.join(DST_DIR, file_name)

        if not os.path.exists(src):
            print("없음:", file_name)
            continue

        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)

        entities = data.get("entities", [])
        filtered = []

        for e in entities:
            source_file = e.get("source_file", "")
            if is_main_file(source_file):
                filtered.append(e)

        out = {
            "group": data.get("group", ""),
            "entity_count": len(filtered),
            "entities": filtered
        }

        with open(dst, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        summary.append({
            "file": file_name,
            "group": out["group"],
            "before": len(entities),
            "after": len(filtered),
        })

        print(f"{file_name:35s} {len(entities):6d} -> {len(filtered):6d}")

    summary_path = os.path.join(DST_DIR, "main_plan_filter_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("")
    print("완료")
    print(summary_path)

if __name__ == "__main__":
    main()
