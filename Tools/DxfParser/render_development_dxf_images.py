import os
import math
import ezdxf
import matplotlib.pyplot as plt

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

OUT_DIR = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "dxf_development_images"
)

TARGET_PREFIXES = [
    "C-612", "C-613", "C-614", "C-615",
    "C-616", "C-617", "C-618", "C-619"
]

# 전개도에서 보고 싶은 주요 레이어/문자
IMPORTANT_LAYER_KEYS = [
    "앵커",
    "ANCHOR",
    "ANCH",
    "@토목-앵커",
    "WALE",
    "STRUT",
    "C-WALE",
    "굴착",
    "TEXT",
    "DIM",
    "HATCH",
]

IMPORTANT_TEXT_KEYS = [
    "E/ANCHOR",
    "ANCHOR",
    "앵커",
    "제거식",
    "WALE",
    "띠장",
    "1단",
    "2단",
    "3단",
    "굴착심도",
    "시공하한선",
    "EL",
    "단면",
]

os.makedirs(OUT_DIR, exist_ok=True)

def hit_any(value, keys):
    u = str(value).upper()
    return any(k.upper() in u for k in keys)

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

def get_points(e):
    try:
        if e.dxftype() == "LINE":
            s = e.dxf.start
            en = e.dxf.end
            return [(float(s.x), float(s.y)), (float(en.x), float(en.y))]

        if e.dxftype() == "LWPOLYLINE":
            return [(float(v[0]), float(v[1])) for v in e.get_points()]

        if e.dxftype() == "POLYLINE":
            pts = []
            for v in e.vertices:
                p = v.dxf.location
                pts.append((float(p.x), float(p.y)))
            return pts
    except Exception:
        return []

    return []

def get_text(e):
    try:
        if e.dxftype() == "TEXT":
            return str(e.dxf.text).strip()
        if e.dxftype() == "MTEXT":
            return str(e.text).strip()
    except Exception:
        return ""
    return ""

def get_text_pos(e):
    try:
        p = e.dxf.insert
        return float(p.x), float(p.y)
    except Exception:
        return None

def draw_file(fname):
    path = os.path.join(DXF_DIR, fname)
    print("렌더링:", fname)

    doc = ezdxf.readfile(path)
    ents = decompose_entities(doc.modelspace())

    lines = []
    texts = []

    for e in ents:
        etype = e.dxftype()
        layer = str(e.dxf.layer).strip() if hasattr(e, "dxf") else ""

        if etype in ["LINE", "LWPOLYLINE", "POLYLINE"]:
            pts = get_points(e)
            if len(pts) < 2:
                continue

            # 주요 레이어 우선, 그래도 전개도 전체가 보이도록 일정 길이 이상 선도 포함
            if hit_any(layer, IMPORTANT_LAYER_KEYS):
                lines.append((pts, layer, etype))

        elif etype in ["TEXT", "MTEXT"]:
            txt = get_text(e)
            if not txt:
                continue

            pos = get_text_pos(e)
            if pos is None:
                continue

            if hit_any(txt, IMPORTANT_TEXT_KEYS) or hit_any(layer, IMPORTANT_LAYER_KEYS):
                texts.append((pos[0], pos[1], txt, layer))

    if not lines and not texts:
        print("  표시할 선/문자가 없습니다:", fname)
        return

    xs = []
    ys = []

    for pts, layer, etype in lines:
        for x, y in pts:
            xs.append(x)
            ys.append(y)

    for x, y, txt, layer in texts:
        xs.append(x)
        ys.append(y)

    if not xs or not ys:
        print("  좌표 없음:", fname)
        return

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    pad_x = (max_x - min_x) * 0.05
    pad_y = (max_y - min_y) * 0.10

    fig = plt.figure(figsize=(22, 10))
    ax = fig.add_subplot(111)

    for pts, layer, etype in lines:
        xlist = [p[0] for p in pts]
        ylist = [p[1] for p in pts]

        # 색상 지정은 도면 확인용 최소 구분
        # 앵커 계열은 굵게, 나머지는 얇게
        if hit_any(layer, ["앵커", "ANCHOR", "ANCH"]):
            ax.plot(xlist, ylist, linewidth=1.2)
        else:
            ax.plot(xlist, ylist, linewidth=0.5)

    for x, y, txt, layer in texts:
        show_txt = txt
        if len(show_txt) > 45:
            show_txt = show_txt[:45] + "..."
        ax.text(x, y, show_txt, fontsize=6)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min_y - pad_y, max_y + pad_y)
    ax.set_title(fname, fontsize=14)
    ax.grid(True, linewidth=0.3)

    safe_name = fname.replace(".dxf", "").replace(" ", "_").replace("(", "").replace(")", "")
    out_png = os.path.join(OUT_DIR, safe_name + ".png")

    plt.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close(fig)

    print("  저장:", out_png)

def main():
    files = []
    for fname in os.listdir(DXF_DIR):
        if not fname.lower().endswith(".dxf"):
            continue
        if any(fname.startswith(p) for p in TARGET_PREFIXES):
            files.append(fname)

    files.sort()

    print("대상 DXF 수:", len(files))
    for f in files:
        draw_file(f)

    print("")
    print("완료")
    print(OUT_DIR)

if __name__ == "__main__":
    main()
