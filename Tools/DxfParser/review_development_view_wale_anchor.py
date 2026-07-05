import os
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

TARGET_FILE_PATTERNS = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619",
    "전개", "굴착계획", "가시설"
]

KEYWORDS = [
    "띠장", "WALE", "Wale", "wale",
    "H-300", "2H", "H=", "H ",
    "1단", "2단", "3단", "4단",
    "앵커", "ANCHOR", "Anchor", "anchor",
    "STRUT", "Strut", "버팀", "코너",
    "EL", "E.L", "GL", "G.L",
    "굴착", "심도", "계획고",
    "P001", "P026", "P066", "P097", "P131", "P196", "P248", "P345", "P365", "P405", "P492"
]

def is_target_file(rel):
    name = rel.replace("\\", "/")
    return any(p in name for p in TARGET_FILE_PATTERNS)

def collect_virtual_entities(insert):
    result = []
    try:
        for ve in insert.virtual_entities():
            result.append(ve)
    except Exception:
        pass
    return result

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

def main():
    rows = []
    layer_summary = {}

    dxf_files = []
    for root, dirs, files in os.walk(DXF_ROOT):
        for f in files:
            if f.lower().endswith(".dxf"):
                path = os.path.join(root, f)
                rel = os.path.relpath(path, DXF_ROOT)
                if is_target_file(rel):
                    dxf_files.append(path)

    print("전개도/가시설 후보 DXF:", len(dxf_files))

    for path in dxf_files:
        rel = os.path.relpath(path, DXF_ROOT)
        print("분석:", rel)

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
                try:
                    layer = str(e.dxf.layer)
                except Exception:
                    layer = ""

                layer_summary.setdefault(rel, {})
                layer_summary[rel][layer] = layer_summary[rel].get(layer, 0) + 1

                if e.dxftype() not in ["TEXT", "MTEXT"]:
                    continue

                txt = get_text(e).strip()
                if not txt:
                    continue

                hit = any(k.lower() in txt.lower() for k in KEYWORDS)
                if not hit:
                    continue

                rows.append({
                    "file": rel,
                    "type": e.dxftype(),
                    "layer": layer,
                    "text": txt,
                    "position": get_pos(e),
                })

        except Exception as ex:
            print("오류:", rel, ex)

    out_json = os.path.join(OUT_DIR, "development_view_wale_anchor_texts.json")
    out_txt = os.path.join(OUT_DIR, "development_view_wale_anchor_texts.txt")
    out_layers = os.path.join(OUT_DIR, "development_view_layer_summary.txt")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        for r in rows:
            f.write("=" * 100 + "\n")
            f.write(f"FILE : {r['file']}\n")
            f.write(f"LAYER: {r['layer']}\n")
            f.write(f"TYPE : {r['type']}\n")
            f.write(f"POS  : {r['position']}\n")
            f.write(f"TEXT : {r['text']}\n")

    with open(out_layers, "w", encoding="utf-8") as f:
        for rel, counts in layer_summary.items():
            f.write("=" * 100 + "\n")
            f.write(f"FILE: {rel}\n")
            for layer, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:80]:
                f.write(f"{layer:45s} {count}\n")

    print("")
    print("완료")
    print("TEXT:", out_txt)
    print("LAYERS:", out_layers)
    print("검색 텍스트 수:", len(rows))

if __name__ == "__main__":
    main()
