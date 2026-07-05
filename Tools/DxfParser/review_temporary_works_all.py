import os
import re
import json
import ezdxf
from collections import defaultdict

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

TARGET_FILE_KEYS = [
    "가시설",
    "C-605", "C-606", "C-607", "C-608", "C-609", "C-610", "C-611",
    "C-612", "C-613", "C-614", "C-615", "C-616", "C-617", "C-618", "C-619",
    "C-620", "C-621", "C-622", "C-623", "C-624", "C-625", "C-626", "C-627", "C-628",
]

LAYER_KEYS = [
    "WALE", "C-WALE", "-$$WALE", "__WALE",
    "STRUT", "C-STRUT", "BEAM-BRACING",
    "ANCHOR", "C-ANCH", "@토목-앵커",
    "H-PILE", "00-H-PILE", "__PILE",
    "CIP", "00-CIP", "__CIP",
    "굴착심도", "GL", "LEVEL",
]

TEXT_KEYS = [
    "WALE", "띠장",
    "STRUT", "버팀", "버팀대",
    "CORNER STRUT", "코너", "경사 버팀",
    "ANCHOR", "앵커", "E/ANCHOR", "제거식",
    "H-300", "2H-300", "H-300x300x10x15", "2H-300x300x10x15",
    "H-300X300X10X15", "2H-300X300X10X15",
    "EL", "E.L", "GL", "G.L",
    "시공하한선", "굴착", "심도",
    "1단", "2단", "3단", "4단",
    "PILE", "NO", "NO.",
]

def is_target_file(rel):
    r = rel.replace("\\", "/")
    return any(k in r for k in TARGET_FILE_KEYS)

def collect_virtual_entities(e):
    out = []
    try:
        for ve in e.virtual_entities():
            out.append(ve)
    except Exception:
        pass
    return out

def get_text(e):
    try:
        if e.dxftype() == "TEXT":
            return str(e.dxf.text).strip()
        if e.dxftype() == "MTEXT":
            return str(e.text).strip()
    except Exception:
        return ""
    return ""

def get_pos(e):
    try:
        if e.dxftype() in ["TEXT", "MTEXT"]:
            p = e.dxf.insert
            return [float(p.x), float(p.y), float(p.z)]
    except Exception:
        pass

    try:
        if e.dxftype() == "LINE":
            p = e.dxf.start
            return [float(p.x), float(p.y), float(p.z)]
    except Exception:
        pass

    return [0, 0, 0]

def hit_any(value, keys):
    u = str(value).upper()
    return any(k.upper() in u for k in keys)

def main():
    report = {
        "files": {},
        "text_hits": [],
        "layer_hits": [],
    }

    dxf_files = []
    for root, dirs, files in os.walk(DXF_ROOT):
        for fname in files:
            if not fname.lower().endswith(".dxf"):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, DXF_ROOT)
            if is_target_file(rel):
                dxf_files.append(path)

    print("검토 대상 DXF 수:", len(dxf_files))

    for path in dxf_files:
        rel = os.path.relpath(path, DXF_ROOT)
        print("분석:", rel)

        try:
            doc = ezdxf.readfile(path)
            msp = doc.modelspace()

            ents = []
            for e in msp:
                if e.dxftype() == "INSERT":
                    ents.extend(collect_virtual_entities(e))
                else:
                    ents.append(e)

            layer_counts = defaultdict(int)
            type_counts = defaultdict(int)
            member_layer_counts = defaultdict(int)

            for e in ents:
                etype = e.dxftype()
                type_counts[etype] += 1

                try:
                    layer = str(e.dxf.layer).strip()
                except Exception:
                    layer = ""

                layer_counts[layer] += 1

                if hit_any(layer, LAYER_KEYS):
                    member_layer_counts[layer] += 1
                    report["layer_hits"].append({
                        "file": rel,
                        "layer": layer,
                        "type": etype,
                        "pos": get_pos(e),
                    })

                if etype in ["TEXT", "MTEXT"]:
                    txt = get_text(e)
                    if txt and hit_any(txt, TEXT_KEYS):
                        report["text_hits"].append({
                            "file": rel,
                            "layer": layer,
                            "type": etype,
                            "text": txt,
                            "pos": get_pos(e),
                        })

            report["files"][rel] = {
                "entity_count": len(ents),
                "type_counts": dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)),
                "member_layer_counts": dict(sorted(member_layer_counts.items(), key=lambda x: x[1], reverse=True)),
                "top_layers": dict(sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)[:120]),
            }

        except Exception as ex:
            print("오류:", rel, ex)

    out_json = os.path.join(OUT_DIR, "temporary_works_full_review.json")
    out_txt = os.path.join(OUT_DIR, "temporary_works_full_review.txt")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("가시설 도면 전체 검토 리포트\n")
        f.write("=" * 120 + "\n\n")

        f.write("[1] 파일별 부재 관련 레이어 수\n")
        for file, info in report["files"].items():
            f.write("=" * 120 + "\n")
            f.write(f"FILE: {file}\n")
            f.write(f"ENTITY COUNT: {info['entity_count']}\n")
            f.write("MEMBER LAYERS:\n")
            for layer, cnt in info["member_layer_counts"].items():
                f.write(f"  {layer:40s} {cnt}\n")

        f.write("\n\n[2] 관련 텍스트 전체\n")
        for t in report["text_hits"]:
            f.write("=" * 120 + "\n")
            f.write(f"FILE : {t['file']}\n")
            f.write(f"LAYER: {t['layer']}\n")
            f.write(f"POS  : {t['pos']}\n")
            f.write(f"TEXT : {t['text']}\n")

    print("")
    print("완료")
    print("텍스트 히트:", len(report["text_hits"]))
    print("레이어 히트:", len(report["layer_hits"]))
    print(out_txt)

if __name__ == "__main__":
    main()
