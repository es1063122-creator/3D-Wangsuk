from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

if 'ToggleGroup("ANCHOR_L1")' in text:
    print("앵커 버튼 이미 있음")
else:
    old = '''        CreateButton("코너버팀", 320, -70, 90, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("CORNER_STRUT_L1");
        });'''

    new = '''        CreateButton("코너버팀", 320, -70, 90, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("CORNER_STRUT_L1");
        });

        CreateButton("앵커", 420, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("ANCHOR_L1");
        });'''

    if old in text:
        text = text.replace(old, new)
        print("앵커 버튼 추가 완료")
    else:
        print("코너버팀 버튼 기준 문구를 찾지 못했습니다. UI 파일 수동 확인 필요")

path.write_text(text, encoding="utf-8")
print("저장 완료")
