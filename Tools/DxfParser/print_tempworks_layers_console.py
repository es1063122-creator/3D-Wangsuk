import os
import ezdxf
from collections import Counter

try:
    from ezdxf.disassemble import recursive_decompose
    HAS_RECURSIVE = True
except Exception:
    HAS_RECURSIVE = False

ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"
GA_PATH = os.path.join(
    ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "SourceDXF",
    "unzipped",
    "dxf",
    "6.가시설공사"
)

TARGET_PREFIXES = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619",
    "C-620", "C-621", "C-622", "C-623", "C-624", "C-625"
]

IMPORTANT = [
    "STRUT", "C-STRUT", "BEAM", "BRACING", "버팀",
    "WALE", "C-WALE", "ANCH", "앵커",
    "RAKER", "굴착심도", "GL", "LEVEL", "PILE", "CIP"
]

def decompose(msp):
    if HAS_RECURSIVE:
        try:
            return list(recursive_decompose(msp))
        except Exception:
            pass

    ents = []
    for e in msp:
        if e.dxftype() == "INSERT":
            try:
                ents.extend(list(e.virtual_entities()))
            except Exception:
                pass
        else:
            ents.append(e)
    return ents

def main():
    files = []
    for name in os.listdir(GA_PATH):
        if not name.lower().endswith(".dxf"):
            continue
        if any(name.startswith(p) for p in TARGET_PREFIXES):
            files.append(os.path.join(GA_PATH, name))

    files.sort()

    print("대상 파일 수:", len(files))
    for p in files:
        print(" -", os.path.basename(p))

    print("\n\n===== 파일별 중요 레이어 =====")

    for path in files:
        print("\n" + "=" * 120)
        print(os.path.basename(path))

        try:
            doc = ezdxf.readfile(path)
            ents = decompose(doc.modelspace())

            layers = Counter()
            types = Counter()

            for e in ents:
                try:
                    layer = str(e.dxf.layer).strip()
                except Exception:
                    layer = "<NO_LAYER>"

                layers[layer] += 1
                types[e.dxftype()] += 1

            print("entity:", len(ents))
            print("types :", dict(types.most_common(8)))

            printed = 0
            for layer, cnt in layers.most_common():
                upper = layer.upper()
                if any(k.upper() in upper for k in IMPORTANT):
                    print(f"  {layer:45s} {cnt}")
                    printed += 1

            if printed == 0:
                print("  중요 레이어 없음")

        except Exception as ex:
            print("ERROR:", ex)

if __name__ == "__main__":
    main()
