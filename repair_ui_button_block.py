from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

start = text.find('        CreateButton("PILE번호"')
end = text.find('        CreateButton("동자리"', start)

if start < 0:
    raise SystemExit('PILE번호 버튼 시작 위치를 찾지 못했습니다.')

if end < 0:
    raise SystemExit('동자리 버튼 시작 위치를 찾지 못했습니다.')

clean_block = r'''        CreateButton("PILE번호", 1395, -70, 90, 36, () =>
        {
            if (builder != null)
                builder.TogglePostPileNumberMarkers();
        });

        CreateButton("바닥구분", 1495, -70, 90, 36, () =>
        {
            ToggleGroupSmart("BOTTOM_ZONE_LINE");
        });

        CreateButton("높이자", 1595, -70, 80, 36, () =>
        {
            if (builder != null)
                builder.ToggleElevationRuler();
        });

'''

text = text[:start] + clean_block + text[end:]

# 혹시 이전에 잘못 삽입된 메서드가 남아 있으면 제거
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

    line_start = src.rfind("\n", 0, idx)
    if line_start < 0:
        line_start = idx

    return src[:line_start] + "\n" + src[end:]

text = remove_method(text, "public void ToggleElevationRulerOverlay")

path.write_text(text, encoding="utf-8")
print("WangsukViewerUI.cs 버튼 블록 복구 완료")
