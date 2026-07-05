import os
import ezdxf

try:
    from ezdxf.disassemble import recursive_decompose
    HAS_RECURSIVE = True
except Exception:
    HAS_RECURSIVE = False

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

OUT_TXT = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "geology_soil_rock_text_review.txt"
)

# 굴착계획 전개도 + 단면도 + 상세도 전체에서 토질/암질 관련 문자 검색
TARGET_PREFIXES = [
    "C-610", "C-611",
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619",
    "C-620", "C-621"
]

KEYS = [
    "매립", "매립층",
    "퇴적", "퇴적층",
    "풍화토",
    "풍화암",
    "연암",
    "경암",
    "토사",
    "암반",
    "실트",
    "점토",
    "모래",
    "자갈",
    "주상도",
    "지층",
    "지반",
    "굴착심도",
    "시공하한선",
    "EL",
    "N치",
    "표준관입"
]

def decompose_entities(msp):
    if HAS_RECURSIVE:
        try:
            return list(recursive_decompose(msp))
        except Exception:
            pass

    result = []
    for e in msp:
        if e.dxftype() == "INSERT":
            try:
                result.extend(list(e.virtual_entities()))
            except Exception:
                pass
        else:
            result.append(e)
    return result

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
        p = e.dxf.insert
        return float(p.x), float(p.y)
    except Exception:
        return 0.0, 0.0

def hit(txt):
    u = txt.upper()
    return any(k.upper() in u for k in KEYS)

def main():
    files = []
    for fname in os.listdir(DXF_DIR):
        if not fname.lower().endswith(".dxf"):
            continue
        if any(fname.startswith(p) for p in TARGET_PREFIXES):
            files.append(fname)

    files.sort()

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write("토질/암질/굴착심도/EL CAD 문자 검토\n")
        f.write("=" * 140 + "\n\n")

        for fname in files:
            path = os.path.join(DXF_DIR, fname)

            try:
                doc = ezdxf.readfile(path)
                ents = decompose_entities(doc.modelspace())

                rows = []

                for e in ents:
                    if e.dxftype() not in ["TEXT", "MTEXT"]:
                        continue

                    txt = get_text(e)
                    if not txt:
                        continue

                    if not hit(txt):
                        continue

                    x, y = get_pos(e)
                    layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""

                    rows.append({
                        "x": x,
                        "y": y,
                        "layer": layer,
                        "text": txt
                    })

                rows.sort(key=lambda r: (-r["y"], r["x"]))

                f.write("=" * 140 + "\n")
                f.write(f"FILE: {fname}\n")
                f.write(f"hit count: {len(rows)}\n\n")

                for r in rows:
                    f.write(
                        f"y={r['y']:.1f} | x={r['x']:.1f} | "
                        f"layer={r['layer']} | text={r['text']}\n"
                    )

                f.write("\n\n")

            except Exception as ex:
                f.write("=" * 140 + "\n")
                f.write(f"FILE: {fname}\n")
                f.write(f"ERROR: {ex}\n\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
