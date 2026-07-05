import os
import re
import json
import ezdxf

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

DXF_ROOT = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "SourceDXF",
    "unzipped"
)

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review"
)

os.makedirs(OUT_DIR, exist_ok=True)

KEYWORDS = [
    "띠장", "WALE", "Wale", "wale",
    "1단", "2단", "3단", "4단", "5단", "6단",
    "EL", "E.L", "GL", "G.L",
    "H-", "H ", "H=", "설치", "지보", "버팀", "STRUT", "ANCHOR"
]

def get_text(e):
    try:
        if e.dxftype() == "TEXT":
            return str(e.dxf.text)
        if e.dxftype() == "MTEXT":
            return str(e.text)
    except Exception:
        return ""
    return ""

def get_pos(e):
    try:
        if e.dxftype() == "TEXT":
            p = e.dxf.insert
            return [float(p.x), float(p.y), float(p.z)]
        if e.dxftype() == "MTEXT":
            p = e.dxf.insert
            return [float(p.x), float(p.y), float(p.z)]
    except Exception:
        pass
    return [0, 0, 0]

def collect_virtual_entities(insert):
    result = []
    try:
        for ve in insert.virtual_entities():
            result.append(ve)
    except Exception:
        pass
    return result

def main():
    results = []

    dxf_files = []
    for root, dirs, files in os.walk(DXF_ROOT):
        for f in files:
            if f.lower().endswith(".dxf"):
                dxf_files.append(os.path.join(root, f))

    print("DXF 검색 파일 수:", len(dxf_files))

    for idx, path in enumerate(dxf_files, start=1):
        rel = os.path.relpath(path, DXF_ROOT)

        # 우선 단면도/가시설/C-605 쪽에 집중
        if not (
            "C-605" in rel
            or "단면" in rel
            or "가시설" in rel
            or "6.가시설공사" in rel
        ):
            continue

        try:
            doc = ezdxf.readfile(path)
            msp = doc.modelspace()

            entities = []
            for e in msp:
                if e.dxftype() == "INSERT":
                    entities.extend(collect_virtual_entities(e))
                else:
                    entities.append(e)

            for e in entities:
                if e.dxftype() not in ["TEXT", "MTEXT"]:
                    continue

                txt = get_text(e).strip()
                if not txt:
                    continue

                hit = False
                for kw in KEYWORDS:
                    if kw.lower() in txt.lower():
                        hit = True
                        break

                if not hit:
                    continue

                layer = str(e.dxf.layer)
                pos = get_pos(e)

                results.append({
                    "file": rel,
                    "layer": layer,
                    "type": e.dxftype(),
                    "text": txt,
                    "position": pos,
                })

        except Exception as ex:
            print("오류:", rel, ex)

    out_json = os.path.join(OUT_DIR, "wale_level_text_candidates.json")
    out_txt = os.path.join(OUT_DIR, "wale_level_text_candidates.txt")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        for r in results:
            f.write("=" * 80 + "\n")
            f.write(f"FILE : {r['file']}\n")
            f.write(f"LAYER: {r['layer']}\n")
            f.write(f"TYPE : {r['type']}\n")
            f.write(f"POS  : {r['position']}\n")
            f.write(f"TEXT : {r['text']}\n")

    print("")
    print("완료")
    print("검색 결과:", len(results))
    print(out_txt)

if __name__ == "__main__":
    main()
