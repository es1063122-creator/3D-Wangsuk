import json
import re
from pathlib import Path

PROJECT_ROOT = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer")

TARGETS = [
    PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "SourceDXF" / "unzipped" / "dxf" / "1.토공사" / "C-106~110 단지횡단면도(1)~(5).dxf",
    PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "SourceDXF" / "unzipped" / "dxf" / "6.가시설공사" / "C-648 흙막이시공 및 해체 순서도 (1).dxf",
    PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "SourceDXF" / "unzipped" / "dxf" / "단면도 모음.dxf",
    PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "SourceDXF" / "unzipped" / "dxf" / "가시설 상세도 합본.dxf",
]

OUT_DIR = PROJECT_ROOT / "Assets" / "StreamingAssets" / "WangsukDXF" / "Review"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_TXT = OUT_DIR / "soil_section_text_precise.txt"
OUT_JSON = OUT_DIR / "soil_section_text_precise.json"

KEYWORDS = [
    "매립", "매립층",
    "퇴적", "퇴적층",
    "풍화토", "풍화암",
    "연암", "보통암", "경암",
    "토사", "사질", "점토", "실트", "자갈",
    "지층", "지질", "토층",
    "BH", "GH", "EL", "굴착", "저면", "최종", "계획고"
]

def clean_text(s):
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\\P", " ")
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\\[A-Za-z0-9;,.+\-/]+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def keep(label):
    if not label:
        return False
    u = label.upper()
    for k in KEYWORDS:
        if k.upper() in u:
            return True
    if re.search(r"EL\s*[\+\-]?\s*\d+\.\d+", u):
        return True
    if re.search(r"GH\s*[\+\-]?\s*\d+\.\d+", u):
        return True
    if re.search(r"BH[-\s]*\d+", u):
        return True
    return False

def add_row(rows, file_name, text, x, y, layer, typ, source):
    label = clean_text(text)
    if not label:
        return
    rows.append({
        "file": file_name,
        "text": label,
        "x": float(x),
        "y": float(y),
        "layer": layer or "",
        "type": typ,
        "source": source,
        "keep": keep(label)
    })

def extract_file(path):
    import ezdxf

    rows = []
    layers = {}

    if not path.exists():
        return rows, layers

    doc = ezdxf.readfile(path)
    msp = doc.modelspace()

    def count_layer(layer):
        layers[layer] = layers.get(layer, 0) + 1

    for e in msp:
        typ = e.dxftype()
        layer = getattr(e.dxf, "layer", "")
        count_layer(layer)

        try:
            if typ == "TEXT":
                p = e.dxf.insert
                add_row(rows, path.name, e.dxf.text, p.x, p.y, layer, typ, "modelspace")

            elif typ == "MTEXT":
                p = e.dxf.insert
                add_row(rows, path.name, e.text, p.x, p.y, layer, typ, "modelspace")

            elif typ == "ATTRIB":
                p = e.dxf.insert
                add_row(rows, path.name, e.dxf.text, p.x, p.y, layer, typ, "modelspace")

            elif typ == "INSERT":
                if hasattr(e, "attribs"):
                    for a in e.attribs:
                        p = a.dxf.insert
                        add_row(rows, path.name, a.dxf.text, p.x, p.y, a.dxf.layer, "ATTRIB", "insert_attrib")

                try:
                    for ve in e.virtual_entities():
                        vtyp = ve.dxftype()
                        vlayer = getattr(ve.dxf, "layer", "")
                        count_layer(vlayer)

                        if vtyp == "TEXT":
                            p = ve.dxf.insert
                            add_row(rows, path.name, ve.dxf.text, p.x, p.y, vlayer, "BLOCK_TEXT", "virtual_block")

                        elif vtyp == "MTEXT":
                            p = ve.dxf.insert
                            add_row(rows, path.name, ve.text, p.x, p.y, vlayer, "BLOCK_MTEXT", "virtual_block")
                except:
                    pass
        except:
            pass

    return rows, layers

all_rows = []
all_layers = {}

for target in TARGETS:
    rows, layers = extract_file(target)
    all_rows.extend(rows)
    all_layers[target.name] = layers

kept = [r for r in all_rows if r["keep"]]

with OUT_TXT.open("w", encoding="utf-8") as f:
    f.write("지층/토사 후보 도면 정밀 텍스트 추출 결과\n")
    f.write("=" * 120 + "\n\n")

    f.write("[대상 파일]\n")
    for t in TARGETS:
        f.write(str(t) + "\n")

    f.write("\n[키워드 후보 텍스트]\n")
    f.write("-" * 120 + "\n")
    for r in kept:
        f.write(f"{r['file']} | {r['text']} | x={r['x']:.1f}, y={r['y']:.1f}, layer={r['layer']}, type={r['type']}, source={r['source']}\n")

    f.write("\n\n[레이어 목록 상위]\n")
    f.write("-" * 120 + "\n")
    for file_name, layers in all_layers.items():
        f.write(f"\n## {file_name}\n")
        for layer, cnt in sorted(layers.items(), key=lambda x: x[1], reverse=True)[:80]:
            f.write(f"{layer}: {cnt}\n")

    f.write("\n\n[전체 텍스트 일부]\n")
    f.write("-" * 120 + "\n")
    for r in all_rows[:500]:
        f.write(f"{r['file']} | {r['text']} | x={r['x']:.1f}, y={r['y']:.1f}, layer={r['layer']}, type={r['type']}\n")

OUT_JSON.write_text(json.dumps({
    "targets": [str(t) for t in TARGETS],
    "kept_count": len(kept),
    "all_text_count": len(all_rows),
    "kept": kept,
    "layers": all_layers
}, ensure_ascii=False, indent=2), encoding="utf-8")

print("완료")
print(OUT_TXT)
print(OUT_JSON)
print("kept:", len(kept))
print("all:", len(all_rows))
