from pathlib import Path

path = Path(r"C:\UnityProjects\SafeAR_Wangsuk_Viewer\Assets\Scripts\UI\WangsukViewerUI.cs")
text = path.read_text(encoding="utf-8")

if 'ToggleGroup("STRUT")' in text:
    print("버팀 버튼 이미 있음")
else:
    old = '''        CreateButton("띠장", 160, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("WALE");
        });'''

    new = '''        CreateButton("띠장", 160, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("WALE");
        });

        CreateButton("버팀", 240, -70, 70, 36, () =>
        {
            if (registry != null) registry.ToggleGroup("STRUT");
        });'''

    if old in text:
        text = text.replace(old, new)
        print("버팀 버튼 추가 완료")
    else:
        print("띠장 버튼 기준 문구를 찾지 못했습니다. UI 수동 확인 필요")

path.write_text(text, encoding="utf-8")
