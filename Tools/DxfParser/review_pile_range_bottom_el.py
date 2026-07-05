import os
import re
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
    "pile_range_bottom_el_review.txt"
)

TARGET_PREFIXES = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

KEYS = [
    "PILE",
    "PILE NO",
    "NO.",
    "시공하한선",
    "EL(+",
    "기반암층",
    "굴착심도",
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
        f.write("C-612~C-619 PILE NO 범위 + 시공하한선 EL 검토\n")
        f.write("=" * 120 + "\n\n")

        for fname in files:
            path = os.path.join(DXF_DIR, fname)
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

            f.write("=" * 120 + "\n")
            f.write(f"FILE: {fname}\n\n")

            f.write("[PILE NO 후보]\n")
            found_pile = False
            for r in rows:
                t = r["text"].upper()
                if "PILE" in t or "NO." in t or "NO " in t:
                    found_pile = True
                    f.write(
                        f"  y={r['y']:.1f} | x={r['x']:.1f} | "
                        f"{r['layer']} | {r['text']}\n"
                    )
            if not found_pile:
                f.write("  PILE NO 문자 후보 없음\n")

            f.write("\n[시공하한선 / 굴착심도 / EL 후보]\n")
            for r in rows:
                txt = r["text"]
                if "시공하한선" in txt or "굴착심도" in r["layer"] or "EL(" in txt or "기반암층" in txt:
                    f.write(
                        f"  y={r['y']:.1f} | x={r['x']:.1f} | "
                        f"{r['layer']} | {txt}\n"
                    )

            f.write("\n\n")

    print("완료")
    print(OUT_TXT)

if __name__ == "__main__":
    main()
