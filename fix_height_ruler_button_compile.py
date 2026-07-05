from pathlib import Path
import re

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

# 1) 잘못 삽입된 높이자 버튼 블록 제거
text = re.sub(
    r'\s*CreateButton\s*\(\s*"높이자"[\s\S]*?\}\s*\);\s*',
    '\n',
    text
)

# 2) 잘못 삽입된 ToggleElevationRulerOverlay 메서드 제거
def remove_method(src, signature):
    idx = src.find(signature)
    if idx < 0:
        return src

    brace = src.find("{", idx)
    if brace < 0:
        return src

    depth = 0
    end = -1

    for i in range(brace, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end < 0:
        return src

    # 메서드 앞쪽 public/private 시작 위치 보정
    start = src.rfind("\n", 0, idx)
    if start < 0:
        start = idx

    return src[:start] + "\n" + src[end:]

text = remove_method(text, "public void ToggleElevationRulerOverlay")

# 3) 기존 바닥구분 버튼 블록 뒤에 정상 높이자 버튼 삽입
target = '''        CreateButton("바닥구분", 1495, -70, 90, 36, () =>
        {
            ToggleGroupSmart("BOTTOM_ZONE_LINE");
        });'''

insert = '''        CreateButton("바닥구분", 1495, -70, 90, 36, () =>
        {
            ToggleGroupSmart("BOTTOM_ZONE_LINE");
        });

        CreateButton("높이자", 1595, -70, 80, 36, () =>
        {
            if (builder != null)
                builder.ToggleElevationRuler();
        });'''

if target not in text:
    raise SystemExit("바닥구분 버튼 블록을 찾지 못했습니다. 수동 위치 확인 필요.")

text = text.replace(target, insert, 1)

path.write_text(text, encoding="utf-8")
print("WangsukViewerUI.cs 높이자 버튼 컴파일 오류 복구 완료")
