import json
from pathlib import Path

review_dir = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\StreamingAssets\WangsukDXF\Review")
src = review_dir / "wale_band_final_review.json"
out = review_dir / "wale_spec_review_v1.json"

data = json.loads(src.read_text(encoding="utf-8"))

spec = {
    "name": "Wangsuk A-6BL C-612~C-619 WALE Spec Review v1",
    "status": "검토용. Unity 반영 전 도면 이미지와 최종 대조 필요.",
    "rules": {
        "H": "단띠장, 한 단에 H빔 1본",
        "2H": "더블띠장, 한 단에 H빔 2본. 단수는 1단으로 계산",
        "band_order": "top_index 1이 최상단. top_index가 커질수록 하부 띠장",
        "important": "P248~P428 전체 4단으로 처리하면 안 됨. 구간별 band 적용 필요."
    },
    "sections": []
}

for item in data:
    section = {
        "file": item["file"],
        "pile_range": item["pile_range"],
        "pile_count_detected": item.get("pile_count_detected"),
        "bands": []
    }

    for b in item["bands"]:
        band = {
            "band_top_index": b["top_index"],
            "y_avg_dxf": b["y_avg"],
            "y_min_dxf": b["y_min"],
            "y_max_dxf": b["y_max"],
            "type_guess": b["type_guess"],
            "x_ranges": [
                {
                    "pile_range_guess": r["pile_range_guess"],
                    "x_min": r["x_min"],
                    "x_max": r["x_max"],
                    "length_sum": r["sum_length"]
                }
                for r in b["x_ranges"]
            ],
            "near_texts": b.get("near_texts", [])
        }
        section["bands"].append(band)

    spec["sections"].append(section)

out.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
print("완료:", out)
