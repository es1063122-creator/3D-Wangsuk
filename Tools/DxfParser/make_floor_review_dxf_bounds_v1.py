import os
import json
from pathlib import Path

PROJECT_ROOT = r"C:\UnityProjects\SafeAR_Wangsuk_Viewer"

DXF_PATH = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "SourceDXF",
    "unzipped",
    "dxf",
    "6.가시설공사",
    "C-605 굴착계획 평면도.dxf"
)

OUT_PATH = os.path.join(
    PROJECT_ROOT,
    "Assets",
    "StreamingAssets",
    "WangsukDXF",
    "Review",
    "floor_review_dxf_bounds_v1.json"
)

def main():
    import ezdxf

    doc = ezdxf.readfile(DXF_PATH)
    msp = doc.modelspace()

    xs = []
    ys = []

    def add_point(x, y):
        # 도면 제목란/범례/우측 주기 영역이 너무 넓게 잡히는 것 방지
        # 실제 굴착계획 평면 영역은 x=-16040000~-15700000, y=3300000~3518000 부근
        if x < -16050000 or x > -15700000:
            return
        if y < 3300000 or y > 3520000:
            return
        xs.append(float(x))
        ys.append(float(y))

    for e in msp:
        typ = e.dxftype()

        try:
            if typ == "LINE":
                add_point(e.dxf.start.x, e.dxf.start.y)
                add_point(e.dxf.end.x, e.dxf.end.y)

            elif typ in ["LWPOLYLINE", "POLYLINE"]:
                for p in e.get_points():
                    add_point(p[0], p[1])

            elif typ == "CIRCLE":
                c = e.dxf.center
                r = e.dxf.radius
                add_point(c.x - r, c.y - r)
                add_point(c.x + r, c.y + r)

            elif typ == "ARC":
                c = e.dxf.center
                r = e.dxf.radius
                add_point(c.x - r, c.y - r)
                add_point(c.x + r, c.y + r)

            elif typ in ["TEXT", "MTEXT"]:
                p = e.dxf.insert
                add_point(p.x, p.y)

            elif typ == "INSERT":
                try:
                    for ve in e.virtual_entities():
                        vtyp = ve.dxftype()

                        if vtyp == "LINE":
                            add_point(ve.dxf.start.x, ve.dxf.start.y)
                            add_point(ve.dxf.end.x, ve.dxf.end.y)

                        elif vtyp in ["LWPOLYLINE", "POLYLINE"]:
                            for p in ve.get_points():
                                add_point(p[0], p[1])

                        elif vtyp == "CIRCLE":
                            c = ve.dxf.center
                            r = ve.dxf.radius
                            add_point(c.x - r, c.y - r)
                            add_point(c.x + r, c.y + r)

                        elif vtyp == "ARC":
                            c = ve.dxf.center
                            r = ve.dxf.radius
                            add_point(c.x - r, c.y - r)
                            add_point(c.x + r, c.y + r)

                        elif vtyp in ["TEXT", "MTEXT"]:
                            p = ve.dxf.insert
                            add_point(p.x, p.y)
                except:
                    pass
        except:
            pass

    if not xs or not ys:
        raise RuntimeError("좌표를 추출하지 못했습니다.")

    result = {
        "name": "C-605 Floor Review DXF Bounds v1",
        "source": "C-605 굴착계획 평면도.dxf",
        "note": "바닥검토 라벨 위치 보정용. 제목란/주기 제외한 평면도 영역 기준.",
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "count": len(xs)
    }

    Path(OUT_PATH).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("완료")
    print(OUT_PATH)
    print(result)

if __name__ == "__main__":
    main()
